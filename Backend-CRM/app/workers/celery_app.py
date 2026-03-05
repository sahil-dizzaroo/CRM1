# from celery import Celery
# from app.config import settings

# celery_app = Celery(
#     "crm_workers",
#     broker=settings.celery_broker_url,
#     backend=settings.celery_result_backend,
# )

# celery_app.conf.update(
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,

#     # ✅ REQUIRED for Azure Redis (TLS)
#     broker_use_ssl={
#         "ssl_cert_reqs": "required"
#     },
#     redis_backend_use_ssl={
#         "ssl_cert_reqs": "required"
#     },
# )

# # Import tasks to register them
# from app.workers import tasks
# from celery import Celery
# from app.config import settings

# # 🔥 IMPORTANT:
# # - Azure Redis is used ONLY as a broker
# # - Result backend is DISABLED (best practice)
# # - Prevents Redis pub/sub auth crashes

# celery_app = Celery(
#     "crm_workers",
#     broker=settings.celery_broker_url,
#     backend=None,  # ✅ DO NOT use Redis result backend on Azure
# )

# celery_app.conf.update(
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,

#     # ✅ REQUIRED for Azure Redis (TLS)
#     broker_use_ssl={
#         "ssl_cert_reqs": "required"
#     },

#     # ❌ DO NOT configure redis_backend_use_ssl
#     # ❌ DO NOT configure result_backend
# )

# # Import tasks so Celery registers them
# from app.workers import tasks
import ssl
from celery import Celery
from app.config import settings

# -------------------------------------------------
# Celery app
# -------------------------------------------------
celery_app = Celery(
    "crm_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# -------------------------------------------------
# Detect if Redis uses SSL (rediss:// = SSL, redis:// = no SSL)
# -------------------------------------------------
broker_uses_ssl = settings.celery_broker_url.startswith("rediss://")
backend_uses_ssl = (
    settings.celery_result_backend and 
    settings.celery_result_backend.startswith("rediss://")
)

# -------------------------------------------------
# Celery configuration
# -------------------------------------------------
celery_config = {
    # ------------------------------
    # Serialization / Time
    # ------------------------------
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,

    # ------------------------------
    # Reliability (IMPORTANT)
    # ------------------------------
    "task_ignore_result": False,
    "task_store_errors_even_if_ignored": True,
    "task_acks_late": True,
    "worker_prefetch_multiplier": 1,

    # ------------------------------
    # Retry defaults
    # ------------------------------
    "task_default_retry_delay": 10,
    "task_max_retries": 3,
    
    # ------------------------------
    # Connection timeouts (prevent hanging)
    # ------------------------------
    "broker_connection_timeout": 5,
    "broker_connection_retry": True,
    "broker_connection_retry_on_startup": True,
    "broker_connection_max_retries": 3,
}

# Only add SSL config if using SSL Redis
if broker_uses_ssl:
    celery_config["broker_use_ssl"] = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }

if backend_uses_ssl:
    celery_config["redis_backend_use_ssl"] = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }

celery_app.conf.update(celery_config)

# -------------------------------------------------
# Debug logs (keep for now)
# -------------------------------------------------
print("🔥 CELERY BROKER =", celery_app.conf.broker_url)
print("🔥 CELERY RESULT BACKEND =", celery_app.conf.result_backend)

# -------------------------------------------------
# Register tasks
# -------------------------------------------------
from app.workers import tasks
