from fastapi import APIRouter

from .endpoints import (
    auth_profiles,
    communications,
    ai_services,
    clinical_workflow,
    legal_docs,
    operations,
)

api_router = APIRouter()

api_router.include_router(auth_profiles.router, prefix="", tags=["Profiles"])
api_router.include_router(communications.router, prefix="", tags=["Communications"])
api_router.include_router(ai_services.router, prefix="", tags=["AI"])
api_router.include_router(clinical_workflow.router, prefix="", tags=["Clinical Workflow"])
api_router.include_router(legal_docs.router, prefix="", tags=["Legal"])
api_router.include_router(operations.router, prefix="", tags=["Operations"])

