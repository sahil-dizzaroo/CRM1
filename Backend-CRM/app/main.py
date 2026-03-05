# import os
# import asyncio
# import logging
# from contextlib import asynccontextmanager

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.api import routes, sites, email_webhook
# from app.db import init_db
# from app.db_mongo import get_mongo_client, close_mongo_client

# # -------------------------------------------------
# # Logging
# # -------------------------------------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # -------------------------------------------------
# # Application lifespan (startup / shutdown)
# # -------------------------------------------------
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("Starting FastAPI application...")

#     async def init_services():
#         # ---------- PostgreSQL ----------
#         try:
#             logger.info("Initializing PostgreSQL...")
#             await asyncio.wait_for(init_db(), timeout=10)
#             logger.info("PostgreSQL initialized")
#         except asyncio.TimeoutError:
#             logger.error("PostgreSQL init timed out – continuing startup")
#         except Exception as e:
#             logger.error(f"PostgreSQL init failed: {e}")

#         # ---------- MongoDB ----------
#         try:
#             logger.info("Initializing MongoDB...")
#             await get_mongo_client()
#             logger.info("MongoDB initialized")
#         except Exception as e:
#             logger.error(f"MongoDB init failed: {e}")

#     # Run DB initialization in background (NON-BLOCKING)
#     asyncio.create_task(init_services())

#     # App is now considered STARTED
#     yield

#     # ---------- Shutdown ----------
#     try:
#         await close_mongo_client()
#         logger.info("MongoDB connection closed")
#     except Exception:
#         pass

# # -------------------------------------------------
# # FastAPI app
# # -------------------------------------------------
# app = FastAPI(
#     title="Clinical Trials CRM Communication Engine",
#     lifespan=lifespan
# )

# # -------------------------------------------------
# # CORS
# # -------------------------------------------------
# origins = os.getenv("CORS_ORIGINS", "").split(",")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins if origins != [""] else [],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -------------------------------------------------
# # Routes
# # -------------------------------------------------
# app.include_router(routes.router, prefix="/api", tags=["api"])
# app.include_router(routes.auth_router, prefix="/api", tags=["authentication"])
# app.include_router(sites.router, prefix="/api", tags=["sites"])
# app.include_router(email_webhook.router, prefix="/api", tags=["email-webhook"])

# # -------------------------------------------------
# # Health check
# # -------------------------------------------------
# @app.get("/")
# def health_check():
#     return {"status": "UP"}

import os
import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import sites, email_webhook
from app.api.v1.api import api_router
from app.db import init_db
from app.db_mongo import get_mongo_client, close_mongo_client

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Application lifespan (startup / shutdown)
# -------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FastAPI application...")
    logger.warning(
        "DEPRECATION NOTICE: sites.study_id is deprecated and will be removed. "
        "All Study + Site resolution must use StudySite."
    )

    async def init_services():
        # ---------- PostgreSQL ----------
        try:
            logger.info("Initializing PostgreSQL...")
            await asyncio.wait_for(init_db(), timeout=10)
            logger.info("PostgreSQL initialized")
        except asyncio.TimeoutError:
            logger.error("PostgreSQL init timed out – continuing startup")
        except Exception as e:
            logger.error(f"PostgreSQL init failed: {e}")

        # ---------- MongoDB ----------
        # MongoDB will be initialized lazily when first needed
        # Don't block startup on MongoDB connection
        logger.info("MongoDB will be initialized on first use")

    # Run DB initialization in background (NON-BLOCKING)
    asyncio.create_task(init_services())

    # -------------------------------------------------
    # START CELERY WORKER (SAME CONTAINER)
    # -------------------------------------------------
    if os.getenv("START_CELERY", "false").lower() == "true":
        try:
            logger.info("🚀 Starting Celery worker inside backend container")
            # Let Celery worker logs go to the main process stdout/stderr so we can
            # see SMTP / task errors in App Service logs (especially in production).
            subprocess.Popen(
                [
                    "celery",
                    "-A",
                    "app.workers.celery_app",
                    "worker",
                    "--loglevel=info",
                ]
            )
            logger.info("✅ Celery worker started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start Celery worker: {e}")

    # App is now considered STARTED
    yield

    # -------------------------------------------------
    # Shutdown
    # -------------------------------------------------
    try:
        await close_mongo_client()
        logger.info("MongoDB connection closed")
    except Exception:
        pass

# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI(
    title="Clinical Trials CRM Communication Engine",
    lifespan=lifespan,
)

# -------------------------------------------------
# CORS
# -------------------------------------------------
from app.config import settings

origins = (
    settings.cors_origins.split(",")
    if settings.cors_origins
    else []
)
origins = [o.strip() for o in origins if o and o.strip()]
if not origins:
    # Local-dev fallback to prevent browser CORS blocks when CORS_ORIGINS is unset.
    origins = ["http://localhost:3000", "http://127.0.0.1:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != [""] else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Routes
# -------------------------------------------------
app.include_router(api_router, prefix="/api")
app.include_router(sites.router, prefix="/api", tags=["sites"])
app.include_router(email_webhook.router, prefix="/api", tags=["email-webhook"])
from app.api import feasibility_attachments
app.include_router(feasibility_attachments.router, prefix="/api", tags=["feasibility-attachments"])

# -------------------------------------------------
# Health check
# -------------------------------------------------
@app.get("/")
async def health_check_root():
    """Simple health check at root that doesn't block on database connections."""
    return {"status": "UP", "service": "backend"}


@app.get("/healthcheck")
async def health_check():
    """
    Health check alias for compatibility with curl/http checks.
    Returns the same payload as the root endpoint.
    """
    return {"status": "UP", "service": "backend"}
