"""
Sites API endpoints for managing hospital sites and their associated doctors and studies.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.models import User, Study, Site, UserSite, SiteProfile
from app.auth import get_current_user, get_current_user_optional
from app import schemas
from datetime import datetime
import uuid

router = APIRouter()


@router.get("/studies")
async def list_studies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all studies that the current user has access to (via role assignments and site associations)."""
    from app import crud
    
    user_id = current_user.get("user_id")
    
    # Get studies from role assignments (CRA, Study Manager, Medical Monitor)
    studies = await crud.get_user_accessible_studies(db, user_id)
    
    # Also check UserSite associations for backward compatibility
    user_sites_result = await db.execute(
        select(UserSite.site_id).where(UserSite.user_id == user_id)
    )
    user_site_ids = [row[0] for row in user_sites_result.all()]
    
    if user_site_ids:
        # Get all studies for those sites via StudySite mappings
        from app.models import StudySite  # Local import to avoid circulars

        study_site_rows = await db.execute(
            select(StudySite.study_id).where(StudySite.site_id.in_(user_site_ids))
        )
        study_ids_from_sites = [row[0] for row in study_site_rows.all()]

        # Add studies from UserSite associations
        if study_ids_from_sites:
            studies_result = await db.execute(
                select(Study).where(Study.id.in_(study_ids_from_sites))
            )
            studies_from_sites = studies_result.scalars().all()
            
            # Merge with role-based studies (avoid duplicates)
            existing_study_ids = {study.id for study in studies}
            for study in studies_from_sites:
                if study.id not in existing_study_ids:
                    studies.append(study)
    
    return [
        {
            "id": str(study.id),
            "study_id": study.study_id,
            "name": study.name,
            "description": study.description,
            "status": study.status
        }
        for study in studies
    ]


@router.get("/sites")
async def list_sites(
    study_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sites that the current user has access to. Optionally filter by study_id."""
    from app import crud
    from app.models import UserRoleAssignment, UserRole
    from app.repositories.postgres_repository import UserRoleAssignmentRepository
    
    user_id = current_user.get("user_id")
    
    # Get accessible sites from role assignments
    accessible_site_ids = set()
    accessible_study_ids = set()
    assignments = await UserRoleAssignmentRepository.list_by_user(db, user_id)
    
    for assignment in assignments:
        if assignment.site_id:
            accessible_site_ids.add(assignment.site_id)
        if assignment.study_id:
            # If user has study-level access, they can see all sites in that study
            accessible_study_ids.add(assignment.study_id)
    
    # Also get sites from UserSite associations for backward compatibility
    user_sites_result = await db.execute(
        select(UserSite.site_id).where(UserSite.user_id == user_id)
    )
    user_site_ids = [row[0] for row in user_sites_result.all()]
    accessible_site_ids.update(user_site_ids)

    from app.models import StudySite as _StudySite
    from sqlalchemy import select as sa_select

    # Get sites from accessible studies via StudySite mappings
    if accessible_study_ids:
        study_site_rows = await db.execute(
            sa_select(_StudySite.site_id).where(_StudySite.study_id.in_(accessible_study_ids))
        )
        site_ids_from_studies = [row[0] for row in study_site_rows.all()]
        accessible_site_ids.update(site_ids_from_studies)
    
    if not accessible_site_ids:
        return []
    
    # Build query for accessible sites
    # IMPORTANT: If user has site-level access (via role assignment or UserSite),
    # show those sites for ALL studies, not just the study they're technically associated with.
    # Study association is now resolved via StudySite below, so we don't need to eager-load
    # a direct Site.study relationship here.
    query = select(Site).where(Site.id.in_(accessible_site_ids))

    result = await db.execute(query.distinct())
    sites = result.scalars().all()
    
    # Get the selected study if study_id is provided (for response mapping)
    selected_study = None
    if study_id:
        try:
            from uuid import UUID as UUIDType
            study_uuid = UUIDType(study_id)
            study_result = await db.execute(
                select(Study).where(Study.id == study_uuid)
            )
        except (ValueError, TypeError):
            study_result = await db.execute(
                select(Study).where(Study.study_id == study_id)
            )
        selected_study = study_result.scalar_one_or_none()
    
    # Return sites - if study_id is provided, return the selected study's study_id in response
    # This makes site01 appear to be associated with the selected study
    # For legacy callers without study_id, derive the association from StudySite mappings instead of sites.study_id
    site_ids = [site.id for site in sites]
    site_study_map = {}
    if site_ids:
        study_site_result = await db.execute(
            sa_select(_StudySite).where(_StudySite.site_id.in_(site_ids))
        )
        for study_site in study_site_result.scalars().all():
            if study_site.site_id not in site_study_map:
                site_study_map[study_site.site_id] = study_site.study_id

    return [
        {
            "id": str(site.id),
            "site_id": site.site_id,
            # If a study is selected, return that study's study_id so site01 appears associated with it
            # Otherwise return the site's actual study association resolved via StudySite
            "study_id": (
                selected_study.study_id
                if selected_study
                else str(site_study_map.get(site.id)) if site_study_map.get(site.id) else None
            ),
            "name": site.name,
            "code": site.code,
            "location": site.location,
            "principal_investigator": site.principal_investigator,
            "address": site.address,
            "city": site.city,
            "country": site.country,
            "status": site.status
        }
        for site in sites
    ]


@router.get("/sites/{site_id}")
async def get_site(
    site_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get site details with associated doctors and their studies. Returns mock data for now."""
    # TODO: Implement actual Site model and database queries
    # For now, return mock data
    
    # Get some users to show as doctors
    result = await db.execute(select(User).limit(3))
    users = result.scalars().all()
    
    doctors_data = []
    for user in users:
        doctors_data.append({
            "id": str(user.id),
            "user_id": user.user_id,
            "name": user.name or "Unknown Doctor",
            "email": user.email or "no-email@example.com",
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "studies": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Clinical Trial Study A",
                    "description": "Phase 3 study for treatment evaluation",
                    "status": "active"
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Research Study B",
                    "description": "Long-term efficacy study",
                    "status": "active"
                }
            ]
        })
    
    return {
        "id": str(site_id),
        "name": "City General Hospital",
        "address": "123 Medical Center Drive",
        "city": "New York",
        "country": "USA",
        "doctors": doctors_data
    }


@router.get("/sites/{site_id}/profile", response_model=schemas.SiteProfileResponse)
async def get_site_profile(
    site_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Get site profile for a site.
    """
    try:
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
        
        # Get profile
        profile_result = await db.execute(
            select(SiteProfile).where(SiteProfile.site_id == site.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Site profile not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting site profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}. Please ensure the site_profiles table exists. Run the migration script: python create_site_profile_table.py"
        )


@router.post("/sites/{site_id}/profile", response_model=schemas.SiteProfileResponse)
async def create_site_profile(
    site_id: str,
    profile_data: schemas.SiteProfileCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Create site profile for a site. If profile already exists, returns existing profile.
    """
    try:
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
        
        # Check if profile already exists
        profile_result = await db.execute(
            select(SiteProfile).where(SiteProfile.site_id == site.id)
        )
        existing_profile = profile_result.scalar_one_or_none()
        
        if existing_profile:
            # Return existing profile
            return existing_profile
        
        # Create new profile
        profile = SiteProfile(
            site_id=site.id,
            **profile_data.model_dump(exclude_unset=True)
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating site profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}. Please ensure the site_profiles table exists. Run the migration script: python create_site_profile_table.py"
        )


@router.put("/sites/{site_id}/profile", response_model=schemas.SiteProfileResponse)
async def update_site_profile(
    site_id: str,
    profile_data: schemas.SiteProfileUpdate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Update site profile for a site. Creates profile if it doesn't exist.
    """
    try:
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
        
        # Get or create profile
        profile_result = await db.execute(
            select(SiteProfile).where(SiteProfile.site_id == site.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            # Create new profile
            profile = SiteProfile(
                site_id=site.id,
                **profile_data.model_dump(exclude_unset=True)
            )
            db.add(profile)
        else:
            # Update existing profile
            update_data = profile_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(profile, key, value)
        
        await db.commit()
        await db.refresh(profile)
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating site profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}. Please ensure the site_profiles table exists. Run the migration script: python create_site_profile_table.py"
        )

