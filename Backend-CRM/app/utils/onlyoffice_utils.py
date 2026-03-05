"""
ONLYOFFICE Document Server Utilities

Handles JWT token generation, document URL creation, and callback processing.
"""

import logging
import jwt
import hashlib
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
    mode: str = "edit",  # "edit" or "view"
) -> Dict[str, Any]:
    """
    Create ONLYOFFICE document configuration.
    
    Args:
        document_url: URL to fetch the document
        callback_url: URL for ONLYOFFICE to call when saving
        document_key: Unique key for the document
        document_title: Title of the document
        user_id: User ID for editor
        user_name: User name for editor
        mode: "edit" or "view"
        
    Returns:
        Document configuration dictionary
    """
    config = {
        "document": {
            "fileType": "docx",
            "key": document_key,
            "title": document_title,
            "url": document_url,
        },
        "documentType": "word",  # Must be "word" for DOCX files (not "text")
        "editorConfig": {
            "mode": mode,
            "callbackUrl": callback_url,
            "user": {
                "id": user_id,
                "name": user_name,
            },
            "customization": {
                "autosave": True,
                "forcesave": True,
            },
        },
    }

    # Note: documentServerUrl is not required and should not be added to editorConfig
    
    # Add JWT if enabled
    if settings.onlyoffice_jwt_enabled and settings.onlyoffice_jwt_secret:
        token = generate_jwt_token(config)
        config["token"] = token
        logger.debug(f"JWT token generated and added to config (token length: {len(token)})")
    else:
        logger.warning("JWT is not enabled or secret is missing - config will not be signed")
    
    logger.info(f"ONLYOFFICE document config created - document.url: {config.get('document', {}).get('url')}, callbackUrl: {config.get('editorConfig', {}).get('callbackUrl')}, has_token: {'token' in config}")
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
