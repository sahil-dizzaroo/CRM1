from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header, Query, UploadFile, File, Form, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete, update
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
from datetime import timedelta, datetime, timezone
import asyncio
import os
import hashlib
import shutil
from pathlib import Path
import secrets
from app.db import get_db, init_db
from app import crud, schemas
from app.models import MessageDirection, MessageStatus, MessageChannel, ConversationAccessLevel, ThreadAttachment, Attachment, Conversation, ChatDocument, PrimarySiteStatus, UserRoleAssignment, Site, Study, StudySite, SiteStatus, SiteWorkflowStep, SiteDocument, WorkflowStepName, StepStatus, DocumentCategory, DocumentType, ReviewStatus, ProjectFeasibilityCustomQuestion, FeasibilityRequest, FeasibilityResponse, FeasibilityRequestStatus, FeasibilityAttachment, Agreement, AgreementStatus
from app.websocket_manager import manager
from app.config import settings
from app.auth import create_access_token, get_password_hash, get_current_user, get_current_user_optional, ACCESS_TOKEN_EXPIRE_MINUTES
from app.site_status_service import (
    get_study_status_summary,
    get_country_site_counts,
    get_sites_by_status,
    get_site_status_detail,
)
from app.ai_service import ai_service
import uuid
import logging
# Tasks imported where needed to avoid circular imports


router = APIRouter(tags=["Clinical Workflow"])
logger = logging.getLogger(__name__)

@router.get("/site-status/summary", response_model=schemas.StudyStatusSummary)
async def get_site_status_summary(
    study_id: str = Query(..., description="Study UUID or external study_id string"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Study‑level Site Status dashboard summary.

    - Site status is the source of truth
    - Country and Study statuses are derived automatically
    - READ‑ONLY – no status changes are exposed here
    """

    result = await get_study_status_summary(db, study_id)
    if not result:
        raise HTTPException(status_code=404, detail="Study not found or no sites")

    _study, summary = result
    return summary


@router.get("/site-status/countries", response_model=List[schemas.CountryStatusSummary])
async def get_site_status_countries(
    study_id: str = Query(..., description="Study UUID or external study_id string"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Country‑wise site counts and derived status for a given study.
    """

    return await get_country_site_counts(db, study_id)


@router.get("/site-status/sites")
async def get_site_status_sites(
    study_id: str = Query(..., description="Study UUID or external study_id string"),
    status: Optional[PrimarySiteStatus] = Query(
        None,
        description="Filter by primary site status (optional)",
    ),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    List sites for a given study, optionally filtered by primary status.
    """

    return await get_sites_by_status(db, study_id, status=status)


@router.get("/site-status/sites/{site_id}", response_model=schemas.SiteStatusDetail)
async def get_site_status_site_detail(
    site_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Detailed site status view with full audit trail.

    - Current primary status (highlighted in UI)
    - Chronological status history
    - Secondary status details (CDA, SFQ, SQV, EC, SIV etc.) via metadata
    """

    detail = await get_site_status_detail(db, site_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Site not found")
    return detail


# ---------------------------------------------------------------------------
# Site Workflow Endpoints (Under Consideration)
# ---------------------------------------------------------------------------

# Study-specific workflow steps that require study_site_id
STUDY_SPECIFIC_STEPS = {
    WorkflowStepName.SITE_IDENTIFICATION,
    WorkflowStepName.CDA_EXECUTION,
    WorkflowStepName.FEASIBILITY,
    WorkflowStepName.SITE_SELECTION_OUTCOME,
}


async def get_or_create_study_site(
    db: AsyncSession,
    study_id: UUID,
    site_id: UUID
) -> StudySite:
    """
    Get or create a study_site mapping.
    Returns the StudySite record for the given study_id and site_id.
    Handles race conditions where multiple requests try to create the same mapping.
    """
    try:
        # Try to find existing mapping first
        result = await db.execute(
            select(StudySite).where(
                StudySite.study_id == study_id,
                StudySite.site_id == site_id
            )
        )
        study_site = result.scalar_one_or_none()
        
        if study_site:
            return study_site
        
        # Try to create new mapping
        # Handle race condition: if another request created it between select and insert,
        # we'll catch the IntegrityError and retry the select
        try:
            study_site = StudySite(
                study_id=study_id,
                site_id=site_id
            )
            db.add(study_site)
            await db.flush()
            await db.refresh(study_site)
            return study_site
        except Exception as insert_error:
            # Check if it's a unique constraint violation (race condition)
            error_msg = str(insert_error)
            if "unique constraint" in error_msg.lower() or "duplicate key" in error_msg.lower() or "uq_study_site" in error_msg:
                # Another request created it, so fetch it now
                await db.rollback()
                result = await db.execute(
                    select(StudySite).where(
                        StudySite.study_id == study_id,
                        StudySite.site_id == site_id
                    )
                )
                study_site = result.scalar_one_or_none()
                if study_site:
                    return study_site
                # If still not found, re-raise the original error
                raise insert_error
            # For other errors, re-raise
            raise insert_error
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # If table doesn't exist, raise a helpful error
        error_msg = str(e)
        if "does not exist" in error_msg or "relation" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail=f"study_sites table does not exist. Please run the migration script: python create_study_site_mapping.py"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get or create study_site mapping: {error_msg}"
        )


@router.get("/sites/{site_id}/study-id")
async def get_site_study_id(
    site_id: str,
    study_id: Optional[str] = Query(
        None,
        description=(
            "Selected study identifier (UUID or external study_id string). "
            "If provided, this will be used instead of the site's stored study_id. "
            "This allows a single site (e.g. site01) to be used for multiple studies."
        ),
    ),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get study ID (UUID) for a site.

    NOTE:
    - Originally this always returned the study attached to the Site row.
    - For your setup, a single site (site01) is used for many studies.
    - The frontend sends the selected study when fetching feasibility questions.
    - So if a study_id is provided, we resolve and return THAT study's UUID,
      ignoring the site's stored study_id.
    """
    # If the caller provides an explicit study_id (selected in UI), prefer that.
    if study_id:
        # Resolve study by UUID or external study_id string
        try:
            study_uuid = UUID(str(study_id))
            study_result = await db.execute(select(Study).where(Study.id == study_uuid))
            study = study_result.scalar_one_or_none()
        except (ValueError, TypeError):
            study_result = await db.execute(select(Study).where(Study.study_id == study_id))
            study = study_result.scalar_one_or_none()

        if study:
            # Return the canonical UUID that the feasibility endpoint expects
            return {"study_id": str(study.id)}

    # Fallback: behave like before, but resolve study via StudySite mapping instead of sites.study_id
    try:
        site_uuid = UUID(str(site_id))
        site_result = await db.execute(select(Site).where(Site.id == site_uuid))
        site = site_result.scalar_one_or_none()
    except (ValueError, TypeError):
        site_result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = site_result.scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Capture the DB UUID for this site once so we don't trigger any lazy loads later.
    # Accessing ORM attributes like site.id after the object is expired can cause
    # async IO in unexpected places (MissingGreenlet). Using this local value avoids that.
    site_db_id = site.id

    study_site_result = await db.execute(
        select(StudySite)
        .where(StudySite.site_id == site.id)
        .order_by(StudySite.created_at)
    )
    study_site = study_site_result.scalars().first()

    if not study_site:
        raise HTTPException(status_code=404, detail="Study mapping not found for site")

    # Return the canonical UUID that downstream endpoints expect
    return {"study_id": str(study_site.study_id)}


@router.get("/sites/{site_id}/workflow/steps", response_model=schemas.WorkflowStepsResponse)
async def get_site_workflow_steps(
    site_id: str,
    study_id: Optional[str] = Query(
        None,
        description=(
            "Study identifier (UUID or external study_id string). "
            "Required for study-specific workflow steps (Site Identification, CDA, Feasibility, Site Selection Outcome). "
            "If not provided, uses the site's default study_id."
        ),
    ),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all workflow steps for a site.
    For study-specific steps (Site Identification, CDA, Feasibility, Site Selection Outcome),
    requires study_id to scope steps to a (study + site) combination.
    Returns step states including locked/unlocked status based on dependencies.
    """
    # Resolve site
    try:
        site_uuid = UUID(str(site_id))
        site_result = await db.execute(select(Site).where(Site.id == site_uuid))
        site = site_result.scalar_one_or_none()
    except (ValueError, TypeError):
        site_result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Capture the DB UUID for this site once so we don't trigger any lazy loads later.
    # Using a local primitive avoids async IO from ORM attribute access in unexpected places.
    site_db_id = site.id
    
    # Resolve study_id and StudySite mapping
    resolved_study_id = None
    study_site = None
    if study_id:
        try:
            resolved_study_id = UUID(str(study_id))
            study_result = await db.execute(select(Study).where(Study.id == resolved_study_id))
            study = study_result.scalar_one_or_none()
            if not study:
                raise HTTPException(status_code=404, detail="Study not found")
        except (ValueError, TypeError):
            study_result = await db.execute(select(Study).where(Study.study_id == study_id))
            study = study_result.scalar_one_or_none()
            if not study:
                raise HTTPException(status_code=404, detail="Study not found")
            resolved_study_id = study.id

        # Get or create study_site mapping for the explicit study_id
        try:
            study_site = await get_or_create_study_site(db, resolved_study_id, site_db_id)
        except HTTPException:
            # Re-raise HTTP exceptions (they have helpful messages)
            raise
        except Exception as e:
            # If study_sites table doesn't exist, provide helpful error
            error_msg = str(e)
            if "does not exist" in error_msg or "relation" in error_msg.lower():
                raise HTTPException(
                    status_code=500,
                    detail="study_sites table does not exist. Please run the migration script: python create_study_site_mapping.py"
                )
            raise
    else:
        # No explicit study_id – resolve via existing StudySite mapping for this site
        study_site_result = await db.execute(
            select(StudySite)
            .where(StudySite.site_id == site_db_id)
            .order_by(StudySite.created_at)
        )
        study_site = study_site_result.scalars().first()
        if not study_site:
            raise HTTPException(status_code=404, detail="Study site mapping not found for site")
        resolved_study_id = study_site.study_id
    
    # Get all steps for this site/study combination
    # For study-specific steps, use study_site_id; for others, use site_id
    # Build query for study-specific steps
    study_specific_steps_query = select(SiteWorkflowStep).where(
        SiteWorkflowStep.study_site_id == study_site.id
    )
    # Filter by step names - need to check each enum value
    study_specific_conditions = [
        SiteWorkflowStep.step_name == step_enum
        for step_enum in STUDY_SPECIFIC_STEPS
    ]
    if study_specific_conditions:
        study_specific_steps_query = study_specific_steps_query.where(
            or_(*study_specific_conditions)
        )
    
    # Build query for non-study-specific steps (if any exist in the future)
    # For now, all 4 steps are study-specific, so this query may return empty
    other_steps_query = select(SiteWorkflowStep).where(
        SiteWorkflowStep.site_id == site_db_id,
        SiteWorkflowStep.study_site_id.is_(None)  # Only non-study-specific steps
    )
    
    # Execute both queries and combine results
    try:
        study_specific_result = await db.execute(study_specific_steps_query)
        other_result = await db.execute(other_steps_query)
        all_steps = list(study_specific_result.scalars().all()) + list(other_result.scalars().all())
    except Exception as e:
        error_msg = str(e)
        # Check if it's a table/column doesn't exist error
        if "does not exist" in error_msg or "relation" in error_msg.lower() or "column" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail=f"Database schema error. Please run the migration script: python create_study_site_mapping.py. Error: {error_msg}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch workflow steps: {error_msg}"
        )
    # Index by both enum instance and string value for flexible lookup
    existing_steps = {}
    for step in all_steps:
        # step.step_name is an enum instance when retrieved from DB
        step_name_enum = step.step_name
        step_name_value = step_name_enum.value if hasattr(step_name_enum, 'value') else str(step_name_enum)
        existing_steps[step_name_enum] = step
        existing_steps[step_name_value] = step
    
    # Ensure all steps exist (create if not)
    step_order = [
        WorkflowStepName.SITE_IDENTIFICATION,
        WorkflowStepName.CDA_EXECUTION,
        WorkflowStepName.FEASIBILITY,
        WorkflowStepName.SITE_SELECTION_OUTCOME,
    ]
    
    steps_list = []
    for step_name_enum in step_order:
        step_name_value = step_name_enum.value
        step = existing_steps.get(step_name_value)
        
        if not step:
            # Create new step with default state
            # Use study_site_id for study-specific steps, site_id for others
            if step_name_enum in STUDY_SPECIFIC_STEPS:
                step = SiteWorkflowStep(
                    study_site_id=study_site.id,
                    step_name=step_name_enum,
                    status=StepStatus.NOT_STARTED,
                    step_data={}
                )
            else:
                step = SiteWorkflowStep(
                    site_id=site.id,
                    step_name=step_name_enum,
                    status=StepStatus.NOT_STARTED,
                    step_data={}
                )
            db.add(step)
            await db.flush()

        # --- CDA reconciliation (legacy external signing before JSONB tracking fix) ---
        # If the CDA HTML file and/or SiteDocument exists but step_data wasn't persisted (JSONB tracking),
        # automatically reconcile the CDA step back to SIGNED so CRM can enable "Complete Step".
        if step_name_enum == WorkflowStepName.CDA_EXECUTION:
            try:
                from sqlalchemy.orm.attributes import flag_modified

                sd = step.step_data or {}
                cda_required_val = sd.get("cda_required")
                cda_required_truthy = str(cda_required_val).lower() in ("true", "1", "yes")
                cda_status_lower = str(sd.get("cda_status") or "").lower()
                cda_doc_path = sd.get("cda_document_path")

                # Only reconcile when CDA is required, we have a document path, and we're not already signed
                if cda_required_truthy and cda_doc_path and cda_status_lower != "signed":
                    # Look for a signed CDA SiteDocument that matches the snapshot file
                    signed_doc_result = await db.execute(
                        select(SiteDocument)
                        .where(
                            SiteDocument.site_id == site.id,
                            SiteDocument.category == DocumentCategory.SIGNED_CDA,
                            SiteDocument.file_path == str(cda_doc_path),
                        )
                        .order_by(SiteDocument.uploaded_at.desc())
                        .limit(1)
                    )
                    signed_doc = signed_doc_result.scalar_one_or_none()

                    if signed_doc:
                        # Derive the document URL from the snapshot filename (stem)
                        try:
                            snapshot_stem = Path(str(cda_doc_path)).stem
                        except Exception:
                            snapshot_stem = None

                        if snapshot_stem:
                            sd.update(
                                {
                                    "cda_status": "SIGNED",
                                    "final_document_url": f"/api/cda/document/{snapshot_stem}",
                                    "cda_document_url": f"/api/cda/document/{snapshot_stem}",
                                    "signed_cda_document_id": str(signed_doc.id),
                                    # Best-effort: treat uploaded_at as the time the site signed
                                    "site_signed_at": sd.get("site_signed_at")
                                    or (signed_doc.uploaded_at.isoformat() if signed_doc.uploaded_at else None),
                                    # Token should no longer be usable once we consider it signed
                                    "cda_sign_token": None,
                                    "cda_sign_token_expires_at": None,
                                }
                            )
                            step.step_data = sd.copy()
                            step.updated_at = datetime.now(timezone.utc)
                            flag_modified(step, "step_data")
                            logger.info(
                                f"Reconciled CDA step to SIGNED from SiteDocument: step_id={step.id}, signed_doc_id={signed_doc.id}"
                            )
            except Exception as e:
                logger.warning(f"CDA reconciliation skipped due to error: {e}")
        
        # Determine if step should be locked based on previous step completion or workflow lock
        is_locked = False
        
        # Check if workflow is locked (Do Not Proceed was selected in Site Identification)
        # For study-specific steps, look up by study_site_id context
        site_ident_step = existing_steps.get(WorkflowStepName.SITE_IDENTIFICATION) or existing_steps.get(WorkflowStepName.SITE_IDENTIFICATION.value)
        workflow_locked = False
        if site_ident_step:
            # Check if decision was "Do Not Proceed"
            decision = site_ident_step.step_data.get('decision') if site_ident_step.step_data else None
            workflow_locked = (decision == 'do_not_proceed') or (site_ident_step.step_data.get('workflow_locked') is True)
        
        if step_name_enum == WorkflowStepName.SITE_IDENTIFICATION:
            # First step is never locked
            is_locked = False
        elif workflow_locked:
            # If workflow is locked (Do Not Proceed), all subsequent steps are locked
            is_locked = True
        elif step_name_enum == WorkflowStepName.CDA_EXECUTION:
            # Locked if site identification not completed OR if decision was "Do Not Proceed"
            if not site_ident_step or site_ident_step.status != StepStatus.COMPLETED:
                is_locked = True
        elif step_name_enum == WorkflowStepName.FEASIBILITY:
            # Locked if CDA not completed
            cda_step = existing_steps.get(WorkflowStepName.CDA_EXECUTION) or existing_steps.get(WorkflowStepName.CDA_EXECUTION.value)
            if not cda_step or cda_step.status != StepStatus.COMPLETED:
                is_locked = True
        elif step_name_enum == WorkflowStepName.SITE_SELECTION_OUTCOME:
            # Locked if feasibility not completed
            feasibility_step = existing_steps.get(WorkflowStepName.FEASIBILITY) or existing_steps.get(WorkflowStepName.FEASIBILITY.value)
            if not feasibility_step or feasibility_step.status != StepStatus.COMPLETED:
                is_locked = True
        
        # Update step status based on lock state
        if is_locked:
            # If step should be locked and it's not started, set to LOCKED
            if step.status == StepStatus.NOT_STARTED:
                step.status = StepStatus.LOCKED
        else:
            # If step should NOT be locked but status is LOCKED, change to NOT_STARTED
            if step.status == StepStatus.LOCKED:
                step.status = StepStatus.NOT_STARTED
        
        steps_list.append({
            "step_name": step.step_name.value if hasattr(step.step_name, 'value') else str(step.step_name),
            "status": step.status.value if hasattr(step.status, 'value') else str(step.status),
            "step_data": step.step_data or {},
            "completed_at": step.completed_at.isoformat() if step.completed_at else None,
            "completed_by": step.completed_by,
            "created_at": step.created_at,
            "updated_at": step.updated_at,
        })
    
    await db.commit()
    
    return {
        "site_id": str(site.id),
        "steps": steps_list
    }


@router.post("/sites/{site_id}/workflow/steps/{step_name}")
async def update_workflow_step(
    site_id: str,
    step_name: str,
    update_data: schemas.WorkflowStepUpdate,
    study_id: Optional[str] = Query(
        None,
        description=(
            "Study identifier (UUID or external study_id string). "
            "Required for study-specific workflow steps (Site Identification, CDA, Feasibility, Site Selection Outcome). "
            "If not provided, uses the site's default study_id."
        ),
    ),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a workflow step state.
    For study-specific steps, requires study_id to scope steps to a (study + site) combination.
    Enforces sequential dependencies - cannot complete a step if previous step is not completed.
    """
    # Resolve site
    try:
        site_uuid = UUID(str(site_id))
        site_result = await db.execute(select(Site).where(Site.id == site_uuid))
        site = site_result.scalar_one_or_none()
    except (ValueError, TypeError):
        site_result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Validate step name
    try:
        step_enum = WorkflowStepName(step_name)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid step name: {step_name}")
    
    # Resolve study_id for study-specific steps
    resolved_study_id = None
    study_site = None
    if step_enum in STUDY_SPECIFIC_STEPS:
        if study_id:
            try:
                resolved_study_id = UUID(str(study_id))
                study_result = await db.execute(select(Study).where(Study.id == resolved_study_id))
                study = study_result.scalar_one_or_none()
                if not study:
                    raise HTTPException(status_code=404, detail="Study not found")
            except (ValueError, TypeError):
                study_result = await db.execute(select(Study).where(Study.study_id == study_id))
                study = study_result.scalar_one_or_none()
                if not study:
                    raise HTTPException(status_code=404, detail="Study not found")
                resolved_study_id = study.id

            # Get or create study_site mapping for the explicit study_id
            study_site = await get_or_create_study_site(db, resolved_study_id, site.id)
        else:
            # No explicit study_id – resolve via existing StudySite mapping for this site
            study_site_result = await db.execute(
                select(StudySite)
                .where(StudySite.site_id == site.id)
                .order_by(StudySite.created_at)
            )
            study_site = study_site_result.scalars().first()
            if not study_site:
                raise HTTPException(status_code=404, detail="Study site mapping not found for site")
            resolved_study_id = study_site.study_id
    
    # Get or create step
    if step_enum in STUDY_SPECIFIC_STEPS:
        step_result = await db.execute(
            select(SiteWorkflowStep).where(
                SiteWorkflowStep.study_site_id == study_site.id,
                SiteWorkflowStep.step_name == step_enum
            )
        )
    else:
        step_result = await db.execute(
            select(SiteWorkflowStep).where(
                SiteWorkflowStep.site_id == site.id,
                SiteWorkflowStep.step_name == step_enum
            )
        )
    step = step_result.scalar_one_or_none()
    
    if not step:
        if step_enum in STUDY_SPECIFIC_STEPS:
            step = SiteWorkflowStep(
                study_site_id=study_site.id,
                step_name=step_enum,
                status=StepStatus.NOT_STARTED,
                step_data={}
            )
        else:
            step = SiteWorkflowStep(
                site_id=site.id,
                step_name=step_enum,
                status=StepStatus.NOT_STARTED,
                step_data={}
            )
        db.add(step)
    
    # PART 3: Prevent Manual Override for CDA Execution
    # If CDA Execution step and CDA is required, check if CDA Agreement exists
    is_cda_step = step_enum == WorkflowStepName.CDA_EXECUTION
    if is_cda_step and update_data.status == StepStatus.COMPLETED.value:
        # Check if CDA is required (check step_data)
        cda_required_value = step.step_data.get('cda_required') if step.step_data else None
        cda_required = False
        cda_not_applicable = False
        
        if cda_required_value is True or str(cda_required_value).lower() in ['true', 'yes', '1']:
            cda_required = True
        elif cda_required_value == 'not_applicable' or str(cda_required_value).lower() == 'not_applicable':
            cda_not_applicable = True
        
        # If CDA is required (Yes), check if Agreement is executed
        if cda_required:
            # Check if CDA Agreement exists and is executed
            from app.models import Agreement, AgreementDocument, StudyTemplate, TemplateType
            from sqlalchemy.orm import selectinload
            
            # Get study_id for querying agreements
            study_id_for_query = None
            if study_site and study_site.study_id:
                study_id_for_query = study_site.study_id
            
            # Find CDA agreements for this Study + Site pair
            # Prefer StudySite-based scoping when available, with legacy fallback.
            cda_agreements_query = None

            if study_id_for_query:
                # Try to resolve StudySite first
                study_site_result = await db.execute(
                    select(StudySite)
                    .where(StudySite.site_id == site.id)
                    .where(StudySite.study_id == study_id_for_query)
                )
                study_site = study_site_result.scalar_one_or_none()
            else:
                study_site = None

            if not (study_site and study_site.id):
                logger.info(
                    "CDA milestone check: no StudySite mapping for study=%s, site=%s; treating as no CDA agreement",
                    str(study_id_for_query),
                    str(site.id),
                )
                cda_agreements = []
            else:
                logger.info(
                    "CDA milestone check via study_site_id=%s (study=%s, site=%s)",
                    str(study_site.id),
                    str(study_id_for_query),
                    str(site.id),
                )
                cda_agreements_query = select(Agreement).where(
                    Agreement.study_site_id == study_site.id
                )

                cda_agreements_result = await db.execute(
                    cda_agreements_query.options(selectinload(Agreement.documents))
                )
                cda_agreements = cda_agreements_result.scalars().all()
            
            # Filter for CDA type agreements
            cda_agreement_executed = False
            for agreement in cda_agreements:
                if agreement.documents and len(agreement.documents) > 0:
                    first_doc = agreement.documents[0]
                    if first_doc.created_from_template_id:
                        template_result = await db.execute(
                            select(StudyTemplate).where(StudyTemplate.id == first_doc.created_from_template_id)
                        )
                        template = template_result.scalar_one_or_none()
                        if template and template.template_type == TemplateType.CDA:
                            # This is a CDA agreement
                            if agreement.status == AgreementStatus.EXECUTED:
                                cda_agreement_executed = True
                                break
            
            if not cda_agreement_executed:
                # CDA Agreement doesn't exist or is not executed
                raise HTTPException(
                    status_code=400,
                    detail="CDA must be executed via Agreement module. Please create and execute a CDA Agreement first."
                )
            # If CDA Agreement is executed, mark in step_data to skip old validation
            # merged_step_data will be created later from step.step_data, so setting it here is sufficient
            if step.step_data is None:
                step.step_data = {}
            step.step_data['completed_via_agreement'] = True
            # If CDA Agreement is executed, allow completion
        # If CDA is Not Applicable or No, allow manual completion (no Agreement check needed)
        # Comment requirement for "No" is handled by frontend validation
    
    # Check dependencies and completion requirements before allowing completion
    if update_data.status == StepStatus.COMPLETED.value:
        step_order = [
            WorkflowStepName.SITE_IDENTIFICATION,
            WorkflowStepName.CDA_EXECUTION,
            WorkflowStepName.FEASIBILITY,
            WorkflowStepName.SITE_SELECTION_OUTCOME,
        ]
        current_index = step_order.index(step_enum)
        
        # Check previous step completion and workflow lock status
        if current_index > 0:
            prev_step_name = step_order[current_index - 1]
            # For study-specific steps, use study_site_id; otherwise use site_id
            if prev_step_name in STUDY_SPECIFIC_STEPS and step_enum in STUDY_SPECIFIC_STEPS:
                prev_result = await db.execute(
                    select(SiteWorkflowStep).where(
                        SiteWorkflowStep.study_site_id == study_site.id,
                        SiteWorkflowStep.step_name == prev_step_name
                    )
                )
            else:
                prev_result = await db.execute(
                    select(SiteWorkflowStep).where(
                        SiteWorkflowStep.site_id == site.id,
                        SiteWorkflowStep.step_name == prev_step_name
                    )
                )
            prev_step = prev_result.scalar_one_or_none()
            
            if not prev_step or prev_step.status != StepStatus.COMPLETED:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot complete {step_name}: previous step {prev_step_name.value} is not completed"
                )
            
            # Check if previous step locked the workflow (e.g., "do_not_proceed", "not_required", etc.)
            prev_step_data = prev_step.step_data or {}
            if prev_step_data.get('workflow_locked') is True:
                # Determine lock reason based on which step locked it
                if prev_step_name == WorkflowStepName.SITE_IDENTIFICATION:
                    reason = 'Site Identification decision was "Do Not Proceed"'
                elif prev_step_name == WorkflowStepName.CDA_EXECUTION:
                    cda_required = prev_step_data.get('cda_required')
                    if cda_required is False:
                        reason = 'CDA Execution was marked as "Not Required"'
                    elif cda_required == 'not_applicable':
                        reason = 'CDA Execution was marked as "Not Applicable"'
                    else:
                        reason = f'{prev_step_name.value} locked the workflow'
                else:
                    reason = f'{prev_step_name.value} locked the workflow'
                
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot complete {step_name}: {reason} - workflow is locked"
                )
        
        # Step-specific completion validation
        merged_step_data = {**(step.step_data or {}), **(update_data.step_data or {})}
        
        if step_enum == WorkflowStepName.SITE_IDENTIFICATION:
            # Site Identification now only requires a decision to complete.
            # Uploading a Site Visibility Report is optional and handled via Site Documents.
            if not merged_step_data.get('decision'):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete Site Identification: Decision is required"
                )
            # If "Do Not Proceed", lock all subsequent steps
            if merged_step_data.get('decision') == 'do_not_proceed':
                merged_step_data['workflow_locked'] = True
        
        elif step_enum == WorkflowStepName.CDA_EXECUTION:
            # Must have cda_required decision
            if merged_step_data.get('cda_required') is None:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete CDA Execution: Please indicate if CDA is required"
                )
            # If CDA is required, check if it was completed via Agreement module
            # The validation above (lines 614-670) already checks if CDA Agreement is executed
            # If we reach here with CDA required, it means either:
            # 1. CDA Agreement is executed (validation passed above), OR
            # 2. This is a legacy flow with signed_cda_document_id
            if merged_step_data.get('cda_required') is True:
                # Check if completed via Agreement module (new flow)
                completed_via_agreement = merged_step_data.get('completed_via_agreement') or step.step_data.get('completed_via_agreement')
                
                if not completed_via_agreement:
                    # Legacy flow - check for signed_cda_document_id
                    cda_status_value = str(merged_step_data.get('cda_status') or '').upper()
                    # Accept both legacy internal flow ('SIGNED') and Zoho flow ('CDA_COMPLETED', 'COMPLETED')
                    if cda_status_value not in ('SIGNED', 'CDA_COMPLETED', 'COMPLETED'):
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "Cannot complete CDA Execution: Signed/Completed CDA must be present when "
                                "CDA is required (expected status SIGNED or CDA_COMPLETED)"
                            ),
                        )
                    if not merged_step_data.get('signed_cda_document_id'):
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                "Cannot complete CDA Execution: Signed CDA document must be stored "
                                "in Site Documents (missing signed_cda_document_id). "
                                "For new CDA workflow, please use the Agreement module."
                            ),
                        )
                # If completed_via_agreement is True, skip signed_cda_document_id check
                # The Agreement module validation already passed above
            # If CDA is NOT required or NOT applicable, require a comment and lock all subsequent steps
            if merged_step_data.get('cda_required') is False or merged_step_data.get('cda_required') == 'not_applicable':
                cda_comment = merged_step_data.get('cda_comment', '').strip()
                if not cda_comment:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Cannot complete CDA Execution: A comment explaining why CDA is not required "
                            "or not applicable is mandatory"
                        ),
                    )
                merged_step_data['workflow_locked'] = True
        
        elif step_enum == WorkflowStepName.FEASIBILITY:
            # Normalize possible frontend camelCase payload keys to snake_case.
            # This keeps backward compatibility across UI versions.
            if merged_step_data.get('response_received') is None and 'responseReceived' in merged_step_data:
                merged_step_data['response_received'] = merged_step_data.get('responseReceived')
            if merged_step_data.get('response_received_at') is None and 'responseReceivedAt' in merged_step_data:
                merged_step_data['response_received_at'] = merged_step_data.get('responseReceivedAt')
            if merged_step_data.get('additional_feasibility') is None and 'additionalFeasibility' in merged_step_data:
                merged_step_data['additional_feasibility'] = merged_step_data.get('additionalFeasibility')
            if merged_step_data.get('onsite_visit_required') is None and 'onsiteVisitRequired' in merged_step_data:
                merged_step_data['onsite_visit_required'] = merged_step_data.get('onsiteVisitRequired')
            if merged_step_data.get('onsite_report_uploaded') is None and 'onsiteReportUploaded' in merged_step_data:
                merged_step_data['onsite_report_uploaded'] = merged_step_data.get('onsiteReportUploaded')

            # Check CDA dependency if required
            # CDA is study-specific, so use study_site_id
            if step_enum in STUDY_SPECIFIC_STEPS and study_site:
                cda_result = await db.execute(
                    select(SiteWorkflowStep).where(
                        SiteWorkflowStep.study_site_id == study_site.id,
                        SiteWorkflowStep.step_name == WorkflowStepName.CDA_EXECUTION
                    )
                )
            else:
                cda_result = await db.execute(
                    select(SiteWorkflowStep).where(
                        SiteWorkflowStep.site_id == site.id,
                        SiteWorkflowStep.step_name == WorkflowStepName.CDA_EXECUTION
                    )
                )
            cda_step = cda_result.scalar_one_or_none()
            if cda_step:
                cda_required_value = cda_step.step_data.get('cda_required')
                cda_required_truthy = (
                    cda_required_value is True
                    or str(cda_required_value).lower() in ("true", "1", "yes")
                )
                cda_status_value = str(cda_step.step_data.get('cda_status') or '').upper()
                # Accept both legacy and Zoho-based completed statuses.
                if cda_required_truthy and cda_status_value not in ('SIGNED', 'CDA_COMPLETED', 'COMPLETED'):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Cannot complete Feasibility: CDA is required and not yet signed/completed "
                            "(expected SIGNED or CDA_COMPLETED)"
                        ),
                    )
            # Must have questionnaire response - check step_data or verify responses exist
            response_received = merged_step_data.get('response_received')
            if not response_received:
                # Auto-check if feasibility responses exist for this study_site
                if study_site:
                    from app.models import FeasibilityRequest, FeasibilityResponse
                    response_check = await db.execute(
                        select(FeasibilityResponse)
                        .join(FeasibilityRequest, FeasibilityResponse.request_id == FeasibilityRequest.id)
                        .where(FeasibilityRequest.study_site_id == study_site.id)
                        .where(FeasibilityRequest.status == FeasibilityRequestStatus.COMPLETED.value)
                        .limit(1)
                    )
                    has_responses = response_check.scalar_one_or_none() is not None
                    if has_responses:
                        # Auto-set response_received if responses exist
                        merged_step_data['response_received'] = True
                        if not merged_step_data.get('response_received_at'):
                            merged_step_data['response_received_at'] = datetime.now(timezone.utc).isoformat()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Cannot complete Feasibility: Questionnaire response must be received"
                        )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot complete Feasibility: Questionnaire response must be received"
                    )
            # Must have all toggles resolved
            if merged_step_data.get('additional_feasibility') is None:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete Feasibility: Additional feasibility requirement must be specified"
                )
            if merged_step_data.get('onsite_visit_required') is None:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete Feasibility: On-site visit requirement must be specified"
                )
            # If onsite visit required, report must be uploaded
            if merged_step_data.get('onsite_visit_required') is True:
                if not merged_step_data.get('onsite_report_uploaded'):
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot complete Feasibility: On-site visit report must be uploaded when required"
                    )
        
        elif step_enum == WorkflowStepName.SITE_SELECTION_OUTCOME:
            # Must have final decision
            if not merged_step_data.get('decision'):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot complete Site Selection Outcome: Final decision is required"
                )
    
    # Track if status was updated to COMPLETED
    status_updated_to_completed = False
    validated_status = None
    
    # Update step
    if update_data.status:
        # Validate that status is a valid StepStatus value, then store as enum
        try:
            validated_status = StepStatus(update_data.status)
            step.status = validated_status  # SQLEnum will convert enum to value for DB
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data.status}")
        
        # Check if status is completed
        if validated_status == StepStatus.COMPLETED:
            status_updated_to_completed = True
            step.completed_at = datetime.now(timezone.utc)
            if current_user:
                step.completed_by = current_user.get("user_id") or current_user.get("email", "unknown")
        # Note: When changing from COMPLETED to IN_PROGRESS (reopening), we preserve completed_at/completed_by
        # for audit history. The status change itself is allowed - no validation needed for reopening.
        
        # TODO: Consider invalidating dependent steps when reopening earlier steps if business logic requires it.
        # For example, if Site Identification decision changes from "proceed" to "do_not_proceed", 
        # subsequent steps should be invalidated. However, this should only happen if the change
        # truly invalidates later steps - not for simple data updates.
    
    if update_data.step_data is not None:
        if step.step_data is None:
            step.step_data = {}
        # Merge the update data with existing step_data
        step.step_data = {**(step.step_data or {}), **update_data.step_data}
        step.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(step)
    
    # Append to Public Notice Board if CDA step was completed
    # Check both if status was just updated to COMPLETED or if step is already COMPLETED
    was_completed = status_updated_to_completed or step.status == StepStatus.COMPLETED
    
    # Check step name - handle both enum and string comparison
    step_name_value = step.step_name.value if hasattr(step.step_name, 'value') else str(step.step_name)
    is_cda_step = (
        step.step_name == WorkflowStepName.CDA_EXECUTION or 
        step_name_value == 'cda_execution' or
        step_name_value == WorkflowStepName.CDA_EXECUTION.value
    )
    
    if is_cda_step and was_completed:
        logger.info(f"CDA step completed detected - step_name: {step_name_value}, status: {step.status}, was_completed: {was_completed}")
        try:
            from app.utils.system_notices import create_system_notice_message
            # Get site and study objects to use their string IDs (site_id, study_id) instead of UUIDs
            site_obj = None
            study_obj = None
            
            if step.site_id:
                site_result = await db.execute(select(Site).where(Site.id == step.site_id))
                site_obj = site_result.scalar_one_or_none()
            
            if step.study_site_id:
                study_site_result = await db.execute(
                    select(StudySite).where(StudySite.id == step.study_site_id)
                )
                study_site = study_site_result.scalar_one_or_none()
                if study_site and study_site.study_id:
                    study_result = await db.execute(select(Study).where(Study.id == study_site.study_id))
                    study_obj = study_result.scalar_one_or_none()
            
            # Use string IDs (site_id, study_id) for matching with frontend queries
            site_id_str = site_obj.site_id if site_obj and hasattr(site_obj, 'site_id') else (str(step.site_id) if step.site_id else None)
            study_id_str = study_obj.study_id if study_obj and hasattr(study_obj, 'study_id') else None
            
            if site_id_str:
                logger.info(f"Appending CDA complete notice - site_id: {site_id_str}, study_id: {study_id_str}")
                await create_system_notice_message(
                    db=db,
                    site_id=site_id_str,
                    study_id=study_id_str,
                    message="CDA step marked as completed.",
                    created_by=current_user.get("user_id") if current_user else None,
                    event_type="status_update",
                )
            else:
                logger.warning(f"Cannot append CDA complete notice: site_id is None")
        except Exception as e:
            logger.error(f"Failed to append CDA complete notice: {e}", exc_info=True)
    
    return {
        "step_name": step.step_name.value if hasattr(step.step_name, 'value') else str(step.step_name),
        "status": step.status.value if hasattr(step.status, 'value') else str(step.status),
        "step_data": step.step_data or {},
        "completed_at": step.completed_at.isoformat() if step.completed_at else None,
        "completed_by": step.completed_by,
        "updated_at": step.updated_at,
    }


# ---------------------------------------------------------------------------
# Workflow Reset Endpoint (for testing)
# ---------------------------------------------------------------------------

@router.delete("/sites/{site_id}/workflow/steps")
async def reset_workflow_steps(
    site_id: str,
    study_id: Optional[str] = Query(
        None,
        description=(
            "Study identifier (UUID or external study_id string). "
            "If provided, only resets study-specific workflow steps for this study+site combination. "
            "If not provided, resets all workflow steps for the site."
        ),
    ),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset workflow steps for a site (for testing purposes).
    If study_id is provided, only resets study-specific steps for that study+site combination.
    Otherwise, resets all workflow steps for the site.
    """
    # Resolve site
    try:
        site_uuid = UUID(str(site_id))
        site_result = await db.execute(select(Site).where(Site.id == site_uuid))
        site = site_result.scalar_one_or_none()
    except (ValueError, TypeError):
        site_result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Delete workflow steps
    from sqlalchemy import delete
    if study_id:
        # Resolve study_id
        try:
            resolved_study_id = UUID(str(study_id))
            study_result = await db.execute(select(Study).where(Study.id == resolved_study_id))
            study = study_result.scalar_one_or_none()
            if not study:
                raise HTTPException(status_code=404, detail="Study not found")
        except (ValueError, TypeError):
            study_result = await db.execute(select(Study).where(Study.study_id == study_id))
            study = study_result.scalar_one_or_none()
            if not study:
                raise HTTPException(status_code=404, detail="Study not found")
            resolved_study_id = study.id
        
        # Get study_site mapping
        study_site = await get_or_create_study_site(db, resolved_study_id, site.id)
        
        # Delete only study-specific steps for this study+site
        # Build conditions for each study-specific step
        step_conditions = [
            SiteWorkflowStep.step_name == step_enum
            for step_enum in STUDY_SPECIFIC_STEPS
        ]
        await db.execute(
            delete(SiteWorkflowStep).where(
                SiteWorkflowStep.study_site_id == study_site.id,
                or_(*step_conditions)
            )
        )
        message = f"Study-specific workflow steps reset for study {study.study_id} and site {site.site_id or site.id}"
    else:
        # Delete all workflow steps for this site
        await db.execute(delete(SiteWorkflowStep).where(SiteWorkflowStep.site_id == site.id))
        message = f"Workflow steps reset for site {site.site_id or site.id}"
    
    await db.commit()
    
    return {"message": message, "site_id": str(site.id)}


# ---------------------------------------------------------------------------
# Site Documents Endpoints
# ---------------------------------------------------------------------------

@router.get("/feasibility-questionnaire/{project_id}", response_model=schemas.FeasibilityQuestionnaireResponse)
async def get_feasibility_questionnaire(
    project_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get feasibility questionnaire for a project/study.
    Merges external MongoDB questions with CRM custom questions.
    
    - project_id: Can be Study.id (UUID) or Study.study_id (string)
    - Returns merged list of questions from both sources
    - If external MongoDB is unavailable or no questions found, returns empty list (no error)
    """
    from app.services.feasibility_service import get_feasibility_questions_for_questionnaire

    study, all_questions = await get_feasibility_questions_for_questionnaire(db, project_id)

    return schemas.FeasibilityQuestionnaireResponse(
        project_id=str(study.id),
        questions=all_questions,
    )


@router.get("/feasibility-questionnaire/debug/test-connection")
async def debug_test_feasibility_connection(
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Debug endpoint to test MongoDB connection and see what's actually in the database.
    This helps diagnose why questions aren't being fetched.
    """
    from app.db_feasibility_mongo import get_feasibility_mongo_db

    result = {
        "connection_status": "unknown",
        "database_name": None,
        "collections": [],
        "feasibilityquestionnaires_count": 0,
        "sample_documents": [],
        "test_queries": {},
    }

    try:
        feasibility_db = await get_feasibility_mongo_db()
        if feasibility_db is None:
            result["connection_status"] = "failed - no database connection"
            return result

        result["connection_status"] = "connected"
        result["database_name"] = feasibility_db.name

        # List collections
        collections = await feasibility_db.list_collection_names()
        result["collections"] = collections

        # Check feasibilityquestionnaires collection
        collection = feasibility_db["feasibilityquestionnaires"]
        doc_count = await collection.count_documents({})
        result["feasibilityquestionnaires_count"] = doc_count

        # Get sample documents
        sample_docs = await collection.find({}).limit(5).to_list(length=5)
        for sample in sample_docs:
            project_val = sample.get("project")
            questions_count = len(sample.get("questionnaire", []))
            result["sample_documents"].append(
                {
                    "_id": str(sample.get("_id")),
                    "project": str(project_val) if project_val else None,
                    "project_type": type(project_val).__name__ if project_val else None,
                    "questions_count": questions_count,
                    "keys": list(sample.keys()),
                }
            )

        # Get ALL documents and their project ObjectIds
        all_docs = await collection.find({}).to_list(length=100)
        result["all_project_objectids"] = []
        for doc in all_docs:
            proj = doc.get("project")
            if proj:
                result["all_project_objectids"].append(
                    {
                        "objectid": str(proj),
                        "questions_count": len(doc.get("questionnaire", [])),
                    }
                )

    except Exception as e:
        result["connection_status"] = f"error: {str(e)}"
        import traceback
        result["traceback"] = traceback.format_exc()

    return result


@router.post("/feasibility-questionnaire/custom-questions", response_model=schemas.CustomQuestionResponse)
async def create_custom_question(
    question_data: schemas.CustomQuestionCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom feasibility question in CRM DB."""
    # Resolve study_id - can be UUID string or study_id/name string
    study = None
    try:
        # Try as UUID first
        from uuid import UUID as UUIDType
        try:
            study_uuid = UUIDType(str(question_data.study_id))
            study_result = await db.execute(select(Study).where(Study.id == study_uuid))
            study = study_result.scalar_one_or_none()
        except (ValueError, TypeError):
            # Not a UUID, try as study_id or name
            study_result = await db.execute(
                select(Study).where(
                    (Study.study_id == str(question_data.study_id)) |
                    (Study.name == str(question_data.study_id))
                )
            )
            study = study_result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error resolving study: {e}")
    
    if not study:
        raise HTTPException(status_code=404, detail=f"Study not found: {question_data.study_id}")
    
    custom_question = ProjectFeasibilityCustomQuestion(
        study_id=study.id,  # Use resolved study UUID
        workflow_step="feasibility",
        question_text=question_data.question_text,
        section=question_data.section,
        expected_response_type=question_data.expected_response_type or "text",
        display_order=question_data.display_order or 0,
        created_by=current_user.get("user_id") if current_user else None
    )
    
    db.add(custom_question)
    await db.commit()
    await db.refresh(custom_question)
    
    return custom_question


@router.get("/feasibility-questionnaire/custom-questions/{study_id}", response_model=List[schemas.CustomQuestionResponse])
async def list_custom_questions(
    study_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """List all custom questions for a study."""
    # Resolve study
    try:
        study_uuid = UUID(str(study_id))
        study_result = await db.execute(select(Study).where(Study.id == study_uuid))
        study = study_result.scalar_one_or_none()
    except (ValueError, TypeError):
        study_result = await db.execute(select(Study).where(Study.study_id == study_id))
        study = study_result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    result = await db.execute(
        select(ProjectFeasibilityCustomQuestion)
        .where(ProjectFeasibilityCustomQuestion.study_id == study.id)
        .where(ProjectFeasibilityCustomQuestion.workflow_step == "feasibility")
        .order_by(ProjectFeasibilityCustomQuestion.display_order, ProjectFeasibilityCustomQuestion.created_at)
    )
    
    return result.scalars().all()


@router.put("/feasibility-questionnaire/custom-questions/{question_id}", response_model=schemas.CustomQuestionResponse)
async def update_custom_question(
    question_id: UUID,
    question_data: schemas.CustomQuestionUpdate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom feasibility question."""
    result = await db.execute(
        select(ProjectFeasibilityCustomQuestion).where(ProjectFeasibilityCustomQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Custom question not found")
    
    if question_data.question_text is not None:
        question.question_text = question_data.question_text
    if question_data.section is not None:
        question.section = question_data.section
    if question_data.expected_response_type is not None:
        question.expected_response_type = question_data.expected_response_type
    if question_data.display_order is not None:
        question.display_order = question_data.display_order
    
    await db.commit()
    await db.refresh(question)
    
    return question


@router.delete("/feasibility-questionnaire/custom-questions/{question_id}")
async def delete_custom_question(
    question_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom feasibility question."""
    result = await db.execute(
        select(ProjectFeasibilityCustomQuestion).where(ProjectFeasibilityCustomQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    
    if not question:
        raise HTTPException(status_code=404, detail="Custom question not found")
    
    await db.delete(question)
    await db.commit()
    
    return {"message": "Custom question deleted successfully"}


# ---------------------------------------------------------------------------
# Feasibility Request Endpoints
# ---------------------------------------------------------------------------

@router.post("/feasibility-requests", response_model=schemas.FeasibilityRequestResponse)
async def create_feasibility_request(
    request_data: schemas.FeasibilityRequestCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a feasibility request and send email with form link.
    Generates a secure token and persists the request before sending email.
    
    If email is not provided in request_data, uses FEASIBILITY_DEFAULT_EMAIL from environment.
    """
    # Use default email from environment if not provided
    recipient_email = request_data.email
    if not recipient_email or not recipient_email.strip():
        recipient_email = settings.feasibility_default_email or "labeshg@dizzaroo.com"
    import secrets
    from datetime import datetime, timedelta, timezone
    from app.services.smtp_service import smtp_service
    from app.config import settings
    
    # Verify study_site exists
    study_site_result = await db.execute(
        select(StudySite).where(StudySite.id == request_data.study_site_id)
    )
    study_site = study_site_result.scalar_one_or_none()
    
    if not study_site:
        raise HTTPException(status_code=404, detail="Study site not found")
    
    # Check if there's already a completed request for this study_site
    existing_result = await db.execute(
        select(FeasibilityRequest)
        .where(FeasibilityRequest.study_site_id == request_data.study_site_id)
        .where(FeasibilityRequest.status == FeasibilityRequestStatus.COMPLETED.value)
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A feasibility request has already been completed for this study site"
        )
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = None
    if request_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request_data.expires_in_days)
    
    # Create feasibility request
    feasibility_request = FeasibilityRequest(
        study_site_id=request_data.study_site_id,
        email=recipient_email.strip(),
        token=token,
        status=FeasibilityRequestStatus.SENT.value,
        expires_at=expires_at
    )
    
    db.add(feasibility_request)
    await db.flush()
    await db.refresh(feasibility_request)
    
    # Get study and site info for email
    study_result = await db.execute(select(Study).where(Study.id == study_site.study_id))
    study = study_result.scalar_one_or_none()
    
    site_result = await db.execute(select(Site).where(Site.id == study_site.site_id))
    site = site_result.scalar_one_or_none()
    
    study_name = study.name if study else "Unknown Study"
    site_name = site.name if site else "Unknown Site"
    
    # Build form URL
    # Extract first origin from CORS_ORIGINS if it's a comma-separated list
    frontend_url = 'http://localhost:5173'  # Default for local development
    if settings.cors_origins:
        origins = [origin.strip() for origin in settings.cors_origins.split(',')]
        frontend_url = origins[0] if origins else frontend_url
    
    form_url = f"{frontend_url}/feasibility/form?token={token}"
    
    # Check if Protocol Synopsis attachment exists
    attachment_result = await db.execute(
        select(FeasibilityAttachment).where(FeasibilityAttachment.study_site_id == request_data.study_site_id)
    )
    attachment = attachment_result.scalar_one_or_none()
    
    # Prepare email content
    email_subject = f"Feasibility Form Request - {study_name}"
    protocol_synopsis_note = ""
    if attachment:
        protocol_synopsis_note = "\n\nA Protocol Synopsis document is attached to this email and is also available for download within the feasibility form."
    
    email_body = f"""
Dear Site Contact,

You have been requested to complete a feasibility form for the following study:

Study: {study_name}
Site: {site_name}

Please click the link below to access the feasibility form:

{form_url}

This link will expire on {expires_at.strftime('%Y-%m-%d') if expires_at else 'never'}.{protocol_synopsis_note}

If you have any questions, please contact the study team.

Best regards,
CRM System
"""
    
    # Prepare attachments list
    email_attachments = []
    if attachment:
        file_path = Path(attachment.file_path)
        if file_path.exists():
            email_attachments.append(str(file_path))
    
    # Send email
    from_email = settings.smtp_user or "noreply@crm.com"
    email_result = smtp_service.send_email(
        to=recipient_email.strip(),
        subject=email_subject,
        body=email_body,
        from_email=from_email,
        html=False,
        attachments=email_attachments if email_attachments else None
    )
    
    if not email_result.get('success'):
        # Rollback the request if email fails
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {email_result.get('error', 'Unknown error')}"
        )
    
    await db.commit()
    
    return feasibility_request


@router.get("/feasibility/form", response_model=schemas.FeasibilityFormResponse)
async def get_feasibility_form(
    token: str = Query(..., description="Secure token for accessing the form"),
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint to load feasibility form questions using token.
    No authentication required.
    """
    from datetime import datetime, timezone
    
    # Find request by token
    request_result = await db.execute(
        select(FeasibilityRequest).where(FeasibilityRequest.token == token)
    )
    request = request_result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Check if already completed
    if request.status == FeasibilityRequestStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="This feasibility form has already been submitted")
    
    # Check expiration
    if request.expires_at and request.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This form link has expired")
    
    # Get study_site info
    study_site_result = await db.execute(
        select(StudySite).where(StudySite.id == request.study_site_id)
    )
    study_site = study_site_result.scalar_one_or_none()
    
    if not study_site:
        raise HTTPException(status_code=404, detail="Study site not found")
    
    # Get study and site names
    study_result = await db.execute(select(Study).where(Study.id == study_site.study_id))
    study = study_result.scalar_one_or_none()
    
    site_result = await db.execute(select(Site).where(Site.id == study_site.site_id))
    site = site_result.scalar_one_or_none()
    
    study_name = study.name if study else "Unknown Study"
    site_name = site.name if site else "Unknown Site"
    
    # Get feasibility questions for the study
    # Use the same logic as get_feasibility_questionnaire to fetch questions
    all_questions: List[schemas.FeasibilityQuestion] = []
    doc = None  # Initialize doc variable early

    # 1. Fetch external questions from MongoDB (read-only)
    from app.services.feasibility_service import get_feasibility_questions_for_form

    study, external_questions = await get_feasibility_questions_for_form(db, str(study.id))

    if not study:
        raise HTTPException(status_code=404, detail="Study/Project not found")

    all_questions.extend(external_questions)
    
    # 2. Fetch custom questions from CRM DB
    custom_questions_result = await db.execute(
        select(ProjectFeasibilityCustomQuestion)
        .where(ProjectFeasibilityCustomQuestion.study_id == study.id)
        .where(ProjectFeasibilityCustomQuestion.workflow_step == "feasibility")
        .order_by(ProjectFeasibilityCustomQuestion.display_order, ProjectFeasibilityCustomQuestion.created_at)
    )
    custom_questions = custom_questions_result.scalars().all()
    
    for cq in custom_questions:
        all_questions.append(schemas.FeasibilityQuestion(
            text=cq.question_text,
            section=cq.section,
            type=cq.expected_response_type or "text",
            source="custom",
            criterion_reference=None,
            display_order=cq.display_order,
            id=cq.id
        ))
    
    # Sort by display_order
    all_questions.sort(key=lambda q: (q.display_order or 0, 0 if q.source == "external" else 1))
    
    # Convert to form questions
    form_questions = [
        schemas.FeasibilityFormQuestion(
            text=q.text,
            section=q.section,
            type=q.type,
            id=q.id,
            display_order=q.display_order
        )
        for q in all_questions
    ]
    
    # Check if Protocol Synopsis attachment exists
    attachment_result = await db.execute(
        select(FeasibilityAttachment).where(FeasibilityAttachment.study_site_id == request.study_site_id)
    )
    attachment = attachment_result.scalar_one_or_none()
    
    protocol_synopsis = None
    if attachment:
        protocol_synopsis = schemas.FeasibilityAttachmentResponse(
            id=attachment.id,
            study_site_id=attachment.study_site_id,
            file_name=attachment.file_name,
            file_path=attachment.file_path,
            content_type=attachment.content_type,
            size=attachment.size,
            uploaded_by=attachment.uploaded_by,
            uploaded_at=attachment.uploaded_at
        )
    
    return schemas.FeasibilityFormResponse(
        request_id=request.id,
        study_name=study_name,
        site_name=site_name,
        questions=form_questions,
        protocol_synopsis=protocol_synopsis
    )


@router.post("/feasibility/submit")
async def submit_feasibility_form(
    submit_data: schemas.FeasibilityFormSubmit,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feasibility form responses.
    Validates token, stores answers, and marks request as completed.
    """
    from datetime import datetime, timezone
    from app.api.v1.endpoints.clinical_workflow import get_or_create_study_site
    
    # Find request by token
    request_result = await db.execute(
        select(FeasibilityRequest).where(FeasibilityRequest.token == submit_data.token)
    )
    request = request_result.scalar_one_or_none()
    
    if not request:
        raise HTTPException(status_code=404, detail="Invalid or expired token")
    
    # Check if already completed
    if request.status == FeasibilityRequestStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="This feasibility form has already been submitted")
    
    # Check expiration
    if request.expires_at and request.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This form link has expired")
    
    # Validate that we have answers
    if not submit_data.answers:
        raise HTTPException(status_code=400, detail="No answers provided")
    
    # Store responses
    responses = []
    for answer_data in submit_data.answers:
        response = FeasibilityResponse(
            request_id=request.id,
            question_text=answer_data.question_text,
            question_id=answer_data.question_id,
            answer=answer_data.answer,
            section=answer_data.section
        )
        db.add(response)
        responses.append(response)
    
    # Mark request as completed
    request.status = FeasibilityRequestStatus.COMPLETED.value
    request.updated_at = datetime.now(timezone.utc)
    
    await db.flush()
    
    # Update feasibility workflow step status
    try:
        study_site_result = await db.execute(
            select(StudySite).where(StudySite.id == request.study_site_id)
        )
        study_site = study_site_result.scalar_one_or_none()
        
        if study_site:
            # Find or create feasibility workflow step
            workflow_step_result = await db.execute(
                select(SiteWorkflowStep)
                .where(SiteWorkflowStep.study_site_id == study_site.id)
                .where(SiteWorkflowStep.step_name == WorkflowStepName.FEASIBILITY)
            )
            workflow_step = workflow_step_result.scalar_one_or_none()
            
            if workflow_step:
                # Update step data to mark response as received
                step_data = workflow_step.step_data or {}
                step_data["response_received"] = True
                step_data["response_received_at"] = datetime.now(timezone.utc).isoformat()
                workflow_step.step_data = step_data
                workflow_step.updated_at = datetime.now(timezone.utc)
    except Exception as e:
        logger.warning(f"Failed to update workflow step: {e}")
        # Don't fail the submission if workflow update fails
    
    await db.commit()
    
    return {
        "message": "Feasibility form submitted successfully",
        "request_id": str(request.id),
        "responses_count": len(responses)
    }


@router.get("/study-sites/lookup")
async def get_study_site_id(
    site_id: str = Query(..., description="Site ID (UUID or external site_id string)"),
    study_id: str = Query(..., description="Study ID (UUID or external study_id string)"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get or create study_site_id for a given site_id and study_id combination.
    Returns the study_site_id UUID.
    """
    # Resolve site
    try:
        site_uuid = UUID(str(site_id))
        site_result = await db.execute(select(Site).where(Site.id == site_uuid))
        site = site_result.scalar_one_or_none()
    except (ValueError, TypeError):
        site_result = await db.execute(select(Site).where(Site.site_id == site_id))
        site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Resolve study
    try:
        study_uuid = UUID(str(study_id))
        study_result = await db.execute(select(Study).where(Study.id == study_uuid))
        study = study_result.scalar_one_or_none()
    except (ValueError, TypeError):
        study_result = await db.execute(select(Study).where(Study.study_id == study_id))
        study = study_result.scalar_one_or_none()
    
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    
    # Get or create study_site
    study_site = await get_or_create_study_site(db, study.id, site.id)
    
    return {"study_site_id": str(study_site.id)}


@router.get("/feasibility-responses/{study_site_id}", response_model=List[schemas.FeasibilityResponsesDisplay])
async def get_feasibility_responses(
    study_site_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all feasibility responses for a study_site.
    Used to display responses in the CRM app.
    """
    # Get all requests for this study_site
    requests_result = await db.execute(
        select(FeasibilityRequest)
        .where(FeasibilityRequest.study_site_id == study_site_id)
        .order_by(FeasibilityRequest.created_at.desc())
    )
    requests = requests_result.scalars().all()
    
    result = []
    for req in requests:
        # Get responses for this request
        responses_result = await db.execute(
            select(FeasibilityResponse)
            .where(FeasibilityResponse.request_id == req.id)
            .order_by(FeasibilityResponse.created_at)
        )
        responses = responses_result.scalars().all()
        
        # Only include requests that have responses (completed requests)
        if not responses or len(responses) == 0:
            continue
        
        # Find completed_at from the first response (they're all created at the same time)
        completed_at = responses[0].created_at if responses else None
        
        result.append(schemas.FeasibilityResponsesDisplay(
            study_site_id=req.study_site_id,
            request_id=req.id,
            email=req.email,
            status=req.status,
            created_at=req.created_at,
            updated_at=req.updated_at,
            completed_at=completed_at,
            responses=[
                schemas.FeasibilityResponseDisplay(
                    id=resp.id,
                    question_text=resp.question_text,
                    answer=resp.answer,
                    section=resp.section,
                    created_at=resp.created_at
                )
                for resp in responses
            ]
        ))
    
    return result


@router.post("/feasibility/reset-all")
async def reset_all_feasibility_requests(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset all feasibility requests and responses for testing purposes.
    This will delete all feasibility requests, responses, and reset workflow steps.
    """
    try:
        # Delete all feasibility responses first (due to foreign key constraint)
        await db.execute(
            delete(FeasibilityResponse)
        )
        
        # Delete all feasibility requests
        await db.execute(
            delete(FeasibilityRequest)
        )
        
        # Reset feasibility workflow steps for all study sites
        await db.execute(
            update(SiteWorkflowStep)
            .where(SiteWorkflowStep.step_name == WorkflowStepName.FEASIBILITY.value)
            .values(
                status=StepStatus.NOT_STARTED.value,
                step_data={},
                completed_at=None,
                completed_by=None
            )
        )
        
        await db.commit()
        
        return {
            "message": "All feasibility requests and responses have been reset successfully",
            "reset_items": {
                "feasibility_requests": "deleted",
                "feasibility_responses": "deleted",
                "workflow_steps": "reset to NOT_STARTED"
            }
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resetting feasibility data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset feasibility data: {str(e)}")


# ---------------------------------------------------------------------------
# CDA Signing Endpoints (Extending Existing CDA Functionality)
# ---------------------------------------------------------------------------

def generate_cda_document_html(
    study_name: str,
    site_name: str,
    cda_template: str,
    step_data: dict,
    site_signer_name: Optional[str] = None,
    site_signer_title: Optional[str] = None,
    site_signed_at: Optional[str] = None,
) -> str:
    """
    Generate CDA document HTML at any stage (draft, internally signed, fully signed).
    Uses the actual CDA template and injects signatures into placeholder lines.
    """
    from datetime import datetime
    
    internal_signer_name = step_data.get('internal_signer_name', '')
    internal_signer_title = step_data.get('internal_signer_title', '')
    internal_signed_at = step_data.get('internal_signed_at', '')
    cda_status = step_data.get('cda_status', 'draft')
    
    # Format dates for display
    def format_date(date_str):
        if not date_str:
            return ''
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%B %d, %Y')
        except:
            return date_str
    
    # Format signature line - show value if signed, otherwise show empty line
    def format_signature_line(value):
        if value:
            return f'<div class="signature-line"><strong>{value}</strong></div>'
        else:
            return '<div class="signature-line"></div>'
    
    # Get current date for the document
    current_date = datetime.now().strftime('%B %d, %Y')
    
    # Format internal signature date
    internal_date = format_date(internal_signed_at) if internal_signed_at else ''
    
    # Format external signature date
    external_date = format_date(site_signed_at) if site_signed_at else ''
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Confidential Disclosure Agreement (CDA) - {study_name} - {site_name}</title>

  <style>
    body {{
      font-family: "Aptos", "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: #000;
      margin: 40px;
    }}

    h1, h2 {{
      font-family: "Aptos Display", "Segoe UI", sans-serif;
      font-weight: normal;
      color: #0f4761;
      page-break-after: avoid;
      page-break-inside: avoid;
    }}

    h1 {{
      font-size: 20pt;
      margin: 18pt 0 6pt;
    }}

    h2 {{
      font-size: 16pt;
      margin: 16pt 0 6pt;
    }}

    p {{
      margin: 8pt 0;
    }}

    hr {{
      border: none;
      border-top: 2px solid #ddd;
      margin: 14pt 0;
    }}

    ul {{
      margin-left: 28pt;
    }}

    ul li {{
      margin: 4pt 0;
    }}

    /* Alphabetical lists: a), b), c) */
    .alpha-list {{
      list-style: none;
      counter-reset: alpha;
      padding-left: 0;
      margin-left: 28pt;
    }}

    .alpha-list > li {{
      counter-increment: alpha;
      position: relative;
      padding-left: 22pt;
      margin: 6pt 0;
    }}

    .alpha-list > li::before {{
      content: counter(alpha, lower-latin) ")";
      position: absolute;
      left: 0;
    }}

    .logo {{
      margin-bottom: 14pt;
    }}

    .signature-block {{
      margin-top: 18pt;
    }}

    .signature-line {{
      margin: 6pt 0;
      border-bottom: 1px solid #000;
      min-height: 20px;
      padding-bottom: 2px;
    }}

    .signature-filled {{
      margin: 6pt 0;
      border-bottom: 1px solid #000;
      min-height: 20px;
      padding-bottom: 2px;
    }}

    .footer {{
      margin-top: 30pt;
      font-size: 11px;
      color: #555;
    }}
  </style>
</head>

<body>

  <!-- LOGO -->
  <div class="logo">
    <img src="data:image/png;base64,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"
         alt="Dizzaroo Logo">
  </div>

  <h1>Confidential Disclosure Agreement (CDA)</h1>
  <p><strong>(Mutual – Plain-English Version)</strong></p>

  <p><strong>Study:</strong> {study_name}</p>
  <p>This Agreement is between:</p>

  <p>
    <strong>Dizzaroo Private Limited</strong><br>
    SR NO 3112, Speciality Business Center, B-211, Baner Gaon,<br>
    Pune, Maharashtra, India, 411045 ("Dizzaroo")
  </p>

  <p><strong>and</strong></p>

  <p>
    <strong>{site_name}</strong><br>
    ("Site")
  </p>

  <p>Dizzaroo and the Site are together called "the parties".</p>

  <p><strong>Date:</strong> {current_date}</p>
  <hr>

  <h2>1. Purpose</h2>
  <p>
    The parties want to share confidential information with each other to explore and evaluate
    a potential working relationship, collaboration, project, service arrangement, or any
    related business discussion (the <strong>"Purpose"</strong>).
  </p>
  <hr>

  <h2>2. Confidential Information</h2>
  <p>
    "Confidential Information" means any non-public information one party ("Disclosing Party")
    shares with the other ("Receiving Party"), in any form, including:
  </p>
  <ul>
    <li>technical information, software, models, algorithms, research, designs;</li>
    <li>business plans, strategies, forecasts, pricing, and financials;</li>
    <li>customer, partner, or supplier information;</li>
    <li>presentations, documents, reports, data, analyses, or summaries;</li>
    <li>any notes or copies based on the above.</li>
  </ul>
  <hr>

  <h2>3. What is not Confidential Information</h2>
  <p>Information is not considered Confidential Information if the Receiving Party can show that:</p>
  <ol class="alpha-list">
    <li>it was already public when received;</li>
    <li>it became public later without breaking this Agreement;</li>
    <li>it was already in the Receiving Party's possession legally;</li>
    <li>it was received from someone authorised to share it; or</li>
    <li>it was developed independently.</li>
  </ol>
  <hr>

  <h2>4. Obligations of the Receiving Party</h2>
  <ol class="alpha-list">
    <li>use Confidential Information only for the Purpose;</li>
    <li>
      not share it except with people who need to know and are bound to confidentiality;
    </li>
    <li>
      protect the information with reasonable care;
    </li>
    <li>
      immediately notify of unauthorised use or disclosure.
    </li>
  </ol>
  <hr>

  <h2>5. Disclosures required by law</h2>
  <ol class="alpha-list">
    <li>notify the Disclosing Party as soon as legally allowed; and</li>
    <li>share only the minimum information required.</li>
  </ol>
  <hr>

  <h2>6. Ownership</h2>
  <p>
    Confidential Information remains the property of the Disclosing Party. Nothing grants
    ownership or licence rights beyond the Purpose.
  </p>
  <hr>

  <h2>7. Term and confidentiality duration</h2>
  <p>This Agreement begins on the Date above.</p>
  <p>
    Confidentiality obligations continue for <strong>five (5) years</strong> after last disclosure.
  </p>
  <hr>

  <h2>8. Return or destruction of information</h2>
  <ol class="alpha-list">
    <li>return or destroy Confidential Information; and</li>
    <li>confirm in writing that this has been done.</li>
  </ol>
  <p>Except where retention is legally required.</p>
  <hr>

  <h2>9. Breach and remedies</h2>
  <p>
    Unauthorised disclosure may cause serious harm. Remedies include injunctions and damages.
  </p>
  <hr>

  <h2>10. Governing law and jurisdiction</h2>
  <p>This Agreement is governed by the laws of <strong>India</strong>.</p>
  <p>Courts of <strong>Pune, Maharashtra</strong> have jurisdiction.</p>
  <hr>

  <h2>11. General</h2>
  <ol class="alpha-list">
    <li>This Agreement is the complete agreement.</li>
    <li>Changes must be in writing and signed.</li>
    <li>Invalid provisions do not affect the rest.</li>
  </ol>
  <hr>

  <h2>Signatures</h2>

  <div class="signature-block">
    <p><strong>For Dizzaroo Private Limited</strong></p>
    <div class="signature-line">Name: {internal_signer_name if internal_signer_name else ''}</div>
    <div class="signature-line">Title: {internal_signer_title if internal_signer_title else ''}</div>
    <div class="signature-line">Signature: {'✓ Electronically Signed' if internal_signer_name else ''}</div>
    <div class="signature-line">Date: {internal_date if internal_date else ''}</div>
  </div>

  <div class="signature-block">
    <p><strong>For {site_name}</strong></p>
    <div class="signature-line">Name: {site_signer_name if site_signer_name else ''}</div>
    <div class="signature-line">Title: {site_signer_title if site_signer_title else ''}</div>
    <div class="signature-line">Signature: {'✓ Electronically Signed' if site_signer_name else ''}</div>
    <div class="signature-line">Date: {external_date if external_date else ''}</div>
  </div>

  <div class="footer">
    Speciality Business Center, B-211, Baner – Balewadi Rd, Pune – 411045<br>
    www.dizzaroo.com
  </div>

</body>
</html>"""
    
    return html_content


def get_cda_document_path(study_site_id: Optional[UUID], site_id: UUID, study_name: str, site_name: str):
    """
    Get the file path for a CDA document. Returns the same path for a given study-site combination.
    This ensures we update the same document file rather than creating new ones.
    """
    upload_dir = Path(settings.upload_dir)
    if not upload_dir.is_absolute():
        import pathlib
        app_dir = pathlib.Path(__file__).parent.parent
        upload_dir = app_dir / upload_dir
    
    cda_dir = upload_dir / "cda_snapshots"
    cda_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a deterministic filename based on study-site combination
    if study_site_id:
        file_id = str(study_site_id)
    else:
        # For site-level CDA, use site_id
        file_id = str(site_id)
    
    # Sanitize names for filename
    safe_study = "".join(c for c in study_name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    safe_site = "".join(c for c in site_name if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
    
    html_file_path = cda_dir / f"{file_id}_{safe_study}_{safe_site}.html"
    file_id_for_url = html_file_path.stem  # Use filename without extension for URL
    
    return html_file_path, file_id_for_url


