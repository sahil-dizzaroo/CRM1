"""
Zoho Sign (India) API Service
Handles interactions with Zoho Sign API using OAuth token authentication.
Supports automatic token refresh when access tokens expire.
This implementation uses the documented /requests endpoint with a
multipart form where the JSON payload is passed in a `data` field.
"""
import logging
import json
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime, timedelta

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ZohoSignService:
    """Service for interacting with Zoho Sign API (India region)."""

    def __init__(self):
        self.base_url = settings.zoho_sign_base_url.rstrip("/")
        self.client_id = settings.zoho_sign_client_id
        self.client_secret = settings.zoho_sign_client_secret
        self.refresh_token = settings.zoho_sign_refresh_token
        
        # Access token (can be refreshed)
        self._access_token: Optional[str] = settings.zoho_sign_api_token
        self._token_expires_at: Optional[datetime] = None
        
        # OAuth token endpoint (India region)
        self.token_endpoint = "https://accounts.zoho.in/oauth/v2/token"

        if not self._access_token:
            logger.warning("ZOHO_SIGN_API_TOKEN not configured")
            # Try to get initial token from refresh token if available
            if self.refresh_token and self.client_id and self.client_secret:
                try:
                    self._refresh_access_token()
                except Exception as e:
                    logger.error(f"Failed to get initial access token from refresh token: {e}")

        # Base headers – Content-Type is set per-request
        self._update_headers()

    def _update_headers(self):
        """Update authorization headers with current access token."""
        if not self._access_token:
            raise ValueError("Zoho Sign access token not available")
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self._access_token}",
        }

    def _refresh_access_token(self) -> str:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            The new access token
        """
        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise ValueError(
                "Cannot refresh token: refresh_token, client_id, and client_secret must be configured"
            )

        logger.info("Refreshing Zoho Sign access token...")
        
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": "https://sign.zoho.com",
            "grant_type": "refresh_token",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.token_endpoint, params=params)
                response.raise_for_status()
                token_data = response.json()

                if "access_token" not in token_data:
                    raise ValueError(f"Token refresh response missing access_token: {token_data}")

                self._access_token = token_data["access_token"]
                
                # Zoho tokens typically expire in 1 hour (3600 seconds)
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
                
                self._update_headers()
                
                logger.info(
                    f"Successfully refreshed access token. Expires at: {self._token_expires_at}"
                )
                return self._access_token

        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail = error_body.get("error", error_detail)
                error_description = error_body.get("error_description", "")
                logger.error(f"Token refresh error: {error_detail} - {error_description}")
            except Exception:
                error_detail = e.response.text or error_detail
            
            raise Exception(f"Failed to refresh Zoho Sign access token: {error_detail}")

        except httpx.RequestError as e:
            logger.error(f"Token refresh request error: {str(e)}")
            raise Exception(f"Failed to refresh Zoho Sign access token: {str(e)}")

    def _ensure_valid_token(self):
        """Ensure we have a valid access token, refreshing if necessary."""
        # Check if token is expired or about to expire
        if self._token_expires_at and datetime.now() >= self._token_expires_at:
            logger.info("Access token expired, refreshing...")
            self._refresh_access_token()
        elif not self._access_token and self.refresh_token:
            # No access token but we have refresh token - get initial token
            logger.info("No access token available, fetching from refresh token...")
            self._refresh_access_token()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_on_401: bool = True,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Zoho Sign API.

        For file uploads, Zoho expects a multipart/form-data body with a
        `data` field containing JSON (including the `requests` object).
        
        Automatically refreshes token on 401 Unauthorized errors.
        """
        # Ensure we have a valid token before making the request
        self._ensure_valid_token()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self.headers.copy()

        # Let httpx set multipart boundaries when files are present
        if not files:
            request_headers["Content-Type"] = "application/json"

        try:
            with httpx.Client(timeout=30.0) as client:
                method_upper = method.upper()

                if method_upper == "GET":
                    response = client.get(url, headers=request_headers, params=params)

                elif method_upper == "POST":
                    if files:
                        # Multipart form: Zoho expects JSON under the `data` field
                        form_data = {"data": json.dumps(data or {})}
                        response = client.post(
                            url,
                            headers=request_headers,
                            data=form_data,
                            files=files,
                            params=params,
                        )
                    else:
                        response = client.post(
                            url,
                            headers=request_headers,
                            json=data or {},
                            params=params,
                        )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            # Handle 401 Unauthorized - token may have expired
            if e.response.status_code == 401 and retry_on_401:
                logger.warning("Received 401 Unauthorized, attempting to refresh token...")
                try:
                    self._refresh_access_token()
                    # Retry the request once with the new token
                    return self._make_request(
                        method=method,
                        endpoint=endpoint,
                        data=data,
                        files=files,
                        params=params,
                        retry_on_401=False,  # Don't retry again to avoid infinite loop
                    )
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh token after 401: {refresh_error}")
                    raise Exception(
                        f"Zoho Sign API authentication failed and token refresh failed: {refresh_error}"
                    )

            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                # Log whole body for debugging in case of schema errors like
                # "Extra key found"
                logger.error("Zoho Sign error body: %s", error_body)
                error_detail = error_body.get("message", error_detail)
            except Exception:
                error_detail = e.response.text or error_detail

            logger.error(f"Zoho Sign API error: {error_detail}")
            raise Exception(f"Zoho Sign API error: {error_detail}")

        except httpx.RequestError as e:
            logger.error(f"Zoho Sign request error: {str(e)}")
            raise Exception(f"Zoho Sign request failed: {str(e)}")

    def create_signature_request(
        self,
        request_name: str,
        document_path: Path,
        recipients: List[Dict[str, Any]],
        cc_recipients: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a signature request in Zoho Sign.

        The payload follows the documented `requests` object model:
        - request_name
        - actions: list of recipients with signing order
        """
        if not document_path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")

        # Map our recipients into Zoho Sign "actions"
        actions: List[Dict[str, Any]] = []
        for idx, recipient in enumerate(recipients):
            actions.append(
                {
                    "recipient_name": recipient.get("name") or "",
                    "recipient_email": recipient["email"],
                    "action_type": recipient.get("action", "SIGN"),
                    "signing_order": int(recipient.get("signing_order", idx + 1)),
                }
            )

        requests_payload: Dict[str, Any] = {
            "request_name": request_name,
            "actions": actions,
        }

        # Keep the payload minimal to avoid "Extra key found" schema errors.
        # Zoho's quick-send /requests API is very strict about allowed keys,
        # and CC handling varies by plan / account. To unblock your flow,
        # we intentionally skip sending CC for now.
        # NOTE: webhook_url cannot be sent in the request payload - it must be
        # configured in Zoho Sign account settings instead.
        if message:
            requests_payload["notes"] = message

        payload = {"requests": requests_payload}

        with open(document_path, "rb") as f:
            files = {
                "file": (document_path.name, f, "application/pdf"),
            }

            response = self._make_request(
                method="POST",
                endpoint="/requests",
                data=payload,
                files=files,
            )

        logger.info(
            "Created Zoho Sign request: %s",
            response.get("requests", {}).get("request_id"),
        )
        return response
    
    def get_request_details(self, request_id: str) -> Dict[str, Any]:
        """
        Get details of a signature request.
        
        Args:
            request_id: Zoho Sign request ID
        
        Returns:
            Request details dict
        """
        return self._make_request(
            method="GET",
            endpoint=f"/requests/{request_id}",
        )
    
    def download_signed_document(self, request_id: str, output_path: Path) -> Path:
        """
        Download the signed document from Zoho Sign.
        
        Args:
            request_id: Zoho Sign request ID
            output_path: Path where the signed PDF should be saved
        
        Returns:
            Path to the downloaded file
        """
        # Ensure we have a valid token
        self._ensure_valid_token()
        
        url = f"{self.base_url}/requests/{request_id}/pdf"
        headers = self.headers.copy()
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(url, headers=headers)
                
                # Handle 401 - try refreshing token and retry
                if response.status_code == 401:
                    logger.warning("Received 401 when downloading document, refreshing token...")
                    self._refresh_access_token()
                    headers = self.headers.copy()
                    response = client.get(url, headers=headers)
                
                response.raise_for_status()
                
                # Save PDF to file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded signed document to: {output_path}")
                return output_path
        
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_body = e.response.json()
                error_detail = error_body.get("message", error_detail)
            except:
                error_detail = e.response.text or error_detail
            
            logger.error(f"Failed to download signed document: {error_detail}")
            raise Exception(f"Failed to download signed document: {error_detail}")
        
        except httpx.RequestError as e:
            logger.error(f"Request error downloading document: {str(e)}")
            raise Exception(f"Failed to download signed document: {str(e)}")


# Singleton instance
zoho_sign_service = ZohoSignService()
