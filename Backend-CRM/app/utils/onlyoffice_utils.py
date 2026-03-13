"""
ONLYOFFICE Document Server Utilities

Handles JWT token generation, document URL creation, and callback processing.
"""

import logging
import jwt
import hashlib
import io
from docx import Document
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger(__name__)


        

def generate_jwt_token(payload: Dict[str, Any]) -> str:
    """
    Generate JWT token for ONLYOFFICE communication.
    
    Args:
        payload: Dictionary to encode in JWT
        
    Returns:
        JWT token string
    """
    if not settings.onlyoffice_jwt_secret:
        logger.warning("ONLYOFFICE JWT secret not configured. JWT disabled.")
        return ""
    
    try:
        # PyJWT 2.x returns a string, but ensure it's a string
        token = jwt.encode(
            payload,
            settings.onlyoffice_jwt_secret,
            algorithm="HS256"
        )
        # Ensure we return a string (PyJWT 2.x should already return str)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        logger.debug(f"Generated JWT token (length: {len(token)})")
        return str(token)
    except Exception as e:
        logger.error(f"Failed to generate JWT token: {str(e)}")
        raise


def create_document_config(
    document_url: str,
    callback_url: str,
    document_key: str,
    document_title: str,
    user_id: str,
    user_name: str,
    mode: str = "edit",
) -> Dict[str, Any]:
    """
    Create ONLYOFFICE document configuration with internal networking fixes.
    """
    # --- STEP 1: DOCKER NETWORKING FIX ---
    # OnlyOffice is in a separate container. It cannot reach 'localhost:8000'.
    # We must replace localhost with the service name 'backend' defined in your docker-compose.
    internal_callback = callback_url.replace("localhost:8000", "backend:8000")
    internal_document = document_url.replace("localhost:8000", "backend:8000")

    config = {
        "document": {
            "fileType": "docx",
            "key": document_key,
            "title": document_title,
            "url": internal_document, # Backend URL reachable by OnlyOffice
            "permissions": {
                "edit": mode == "edit",
                "fillForms": True,
                "comment": True,
                # Permission needed for template-based structural changes
                "modifyContentControl": True, 
                "review": True
            }
        },
        "documentType": "word",
        "editorConfig": {
            "mode": mode,
            "callbackUrl": internal_callback, # The critical internal path
            "user": {
                "id": user_id,
                "name": user_name,
            },
            "customization": {
                "autosave": True,
                "forcesave": True,
                "chat": True,
                "help": False,
                "compactHeader": True,
            },
        },
    }

    # --- STEP 2: JWT STRUCTURE FIX ---
    # According to ONLYOFFICE security rules, when JWT is enabled, 
    # the token MUST contain the full config object, and the 
    # "token" field must be at the root of the config.
    if settings.onlyoffice_jwt_enabled and settings.onlyoffice_jwt_secret:
        # Generate token using the config as the payload
        token = generate_jwt_token(config)
        config["token"] = token
        
        # Some OnlyOffice versions also require the token inside editorConfig
        config["editorConfig"]["token"] = token
        
        logger.debug(f"JWT token applied to config for document: {document_key}")
    else:
        logger.warning("JWT is disabled; OnlyOffice may refuse to save if JWT_ENABLED=true in docker-compose")

    logger.info(f"ONLYOFFICE Config: Callback set to {internal_callback}")
    return config

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token from ONLYOFFICE callback.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    if not settings.onlyoffice_jwt_secret:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.onlyoffice_jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except Exception as e:
        logger.error(f"Failed to verify JWT token: {str(e)}")
        return None


def get_onlyoffice_editor_url() -> str:
    """
    Get ONLYOFFICE editor URL for iframe embedding.
    
    Returns:
        URL to ONLYOFFICE editor
    """
    # Use public URL for frontend access, fallback to localhost:8080 if not set
    if settings.onlyoffice_public_url:
        public_url = settings.onlyoffice_public_url
    else:
        # Default to localhost:8080 for local development
        public_url = "http://localhost:8080"
    return f"{public_url}/web-apps/apps/api/documents/api.js"



def extract_content_controls(docx_bytes: bytes) -> dict:
    """
    Extracts all Content Controls (w:sdt) and their text values from a DOCX file.
    Returns a dictionary mapping the field name (alias/tag) to its text value.
    """
    try:
        doc = Document(io.BytesIO(docx_bytes))
        controls = {}
        
        # Search for all Structured Document Tags using XPath
        for sdt in doc.element.xpath('//w:sdt'):
            # Get the tag name we set earlier (e.g., "SITE_NAME")
            tags = sdt.xpath('.//w:tag/@w:val')
            if not tags:
                continue
            tag_name = tags[0]

            # Extract all text nodes within the content control
            sdt_content = sdt.xpath('.//w:sdtContent//w:t/text()')
            text_value = "".join(sdt_content).strip()
            
            controls[tag_name] = text_value

        return controls
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to extract DOCX content controls: {e}")

    return {}
