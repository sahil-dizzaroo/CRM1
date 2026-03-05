# from pydantic_settings import BaseSettings
# from typing import Optional


# class Settings(BaseSettings):
#     # ---- REQUIRED (NO BAD DEFAULTS) ----
#     database_url: str
#     redis_url: str
#     celery_broker_url: str
#     celery_result_backend: str
#     mongodb_uri: str

#     # ---- Optional ----
#     mongodb_database: str = "crm_db"
#     mock_provider_token: Optional[str] = None
#     gemini_api_key: Optional[str] = None

#     upload_dir: str = "uploads"

#     google_search_api_key: Optional[str] = None
#     google_search_engine_id: Optional[str] = None

#     smtp_host: str = "smtp.gmail.com"
#     smtp_port: int = 587
#     smtp_user: Optional[str] = None
#     smtp_password: Optional[str] = None

#     mailgun_signing_key: Optional[str] = None

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"
#         case_sensitive = False


# settings = Settings()

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",  # Ignore extra environment variables
        case_sensitive=False,  # IMPORTANT for Azure env vars
        env_file=".env",
        env_file_encoding="utf-8",
    )
    # -------------------------------------------------
    # REQUIRED DATABASES
    # -------------------------------------------------
    database_url: str
    mongodb_uri: str
    
    # External MongoDB for feasibility questionnaires (read-only)
    feasibility_mongo_uri: Optional[str] = None

    # -------------------------------------------------
    # CELERY / REDIS (PRODUCTION)
    # -------------------------------------------------
    # Celery MUST have a broker in production
    celery_broker_url: str

    # Result backend is REQUIRED for reliability
    celery_result_backend: Optional[str] = None

    # App-level Redis (WebSockets / pub-sub / cache)
    redis_url: Optional[str] = None

    # -------------------------------------------------
    # OPTIONAL / DEFAULTS
    # -------------------------------------------------
    mongodb_database: str = "crm_db"

    mock_provider_token: Optional[str] = None

    # AI
    gemini_api_key: Optional[str] = None

    upload_dir: str = "uploads"

    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None

    # SMTP (optional, not Mailgun inbound)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Feasibility form default recipient email
    feasibility_default_email: Optional[str] = None

    # -------------------------------------------------
    # MAILGUN (INBOUND SECURITY)
    # -------------------------------------------------
    mailgun_signing_key: Optional[str] = None

    # -------------------------------------------------
    # ZOHO SIGN (INDIA)
    # -------------------------------------------------
    zoho_sign_api_token: Optional[str] = None  # Access token (can be refreshed)
    zoho_sign_base_url: str = "https://sign.zoho.in/api/v1"
    zoho_sign_webhook_url: Optional[str] = None  # Will be set dynamically based on deployment
    # OAuth credentials for token refresh
    zoho_sign_client_id: Optional[str] = None
    zoho_sign_client_secret: Optional[str] = None
    zoho_sign_refresh_token: Optional[str] = None
    
    # Sponsor signatory configuration for agreements
    sponsor_signatory_name: Optional[str] = None
    sponsor_signatory_email: Optional[str] = None
    
    # -------------------------------------------------
    # ONLYOFFICE Document Server
    # -------------------------------------------------
    onlyoffice_url: str = "http://onlyoffice:80"  # Internal Docker network URL
    onlyoffice_public_url: Optional[str] = None  # Public URL for frontend (defaults to onlyoffice_url if not set)
    onlyoffice_jwt_secret: Optional[str] = None  # JWT secret for secure communication
    onlyoffice_jwt_enabled: bool = True  # Enable JWT for security

    # -------------------------------------------------
    # Backend base URL for callbacks (e.g. ONLYOFFICE)
    # -------------------------------------------------
    # Used when external services (OnlyOffice) need to call back into the backend.
    # Default works for local docker-compose (service name "backend").
    # In production (e.g. Azure App Service), set BACKEND_INTERNAL_URL to the public HTTPS URL.
    backend_internal_url: str = "http://backend:8000"

    # -------------------------------------------------
    # Pydantic config
    # -------------------------------------------------
    cors_origins: Optional[str] = None


settings = Settings()


