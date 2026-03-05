"""
Agreement Workflow Service

Centralized service for managing agreement status transitions with strict workflow rules.
"""

from typing import Optional, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Agreement, AgreementStatus, AgreementComment, CommentType, UserRole, UserRoleAssignment, AgreementDocument, Site, Study, StudySite
from app.utils.system_notices import create_system_notice_message
import logging

logger = logging.getLogger(__name__)

# Define allowed transitions - no backward transitions, no skipping states
ALLOWED_TRANSITIONS: Dict[AgreementStatus, List[AgreementStatus]] = {
    AgreementStatus.DRAFT: [AgreementStatus.UNDER_REVIEW],
    AgreementStatus.UNDER_REVIEW: [AgreementStatus.UNDER_NEGOTIATION],
    AgreementStatus.UNDER_NEGOTIATION: [AgreementStatus.READY_FOR_SIGNATURE],
    AgreementStatus.READY_FOR_SIGNATURE: [AgreementStatus.SENT_FOR_SIGNATURE],
    AgreementStatus.SENT_FOR_SIGNATURE: [AgreementStatus.EXECUTED],
    AgreementStatus.EXECUTED: [AgreementStatus.CLOSED],
    AgreementStatus.CLOSED: [],  # No transitions allowed from CLOSED
}

def is_transition_allowed(current_status: AgreementStatus, new_status: AgreementStatus) -> bool:
    """
    Check if a status transition is allowed.
    
    Args:
        current_status: Current agreement status
        new_status: Desired new status
        
    Returns:
        True if transition is allowed, False otherwise
    """
    allowed_next_statuses = ALLOWED_TRANSITIONS.get(current_status, [])
    return new_status in allowed_next_statuses


def get_next_allowed_status(current_status: AgreementStatus) -> Optional[AgreementStatus]:
    """
    Get the next allowed status in the workflow.
    
    Args:
        current_status: Current agreement status
        
    Returns:
        Next allowed status, or None if no transitions allowed
    """
    allowed_next = ALLOWED_TRANSITIONS.get(current_status, [])
    return allowed_next[0] if allowed_next else None


def check_can_upload_new_version(
    current_status: AgreementStatus,
    has_signed_version: bool = False
) -> bool:
    """
    Backward-compatibility stub – legacy file-based version uploads are no longer supported.
    Always returns False.
    """
    return False


def filter_versions_by_role(
    versions,
    is_internal: bool = True
) -> list:
    """
    Filter versions based on user role.
    
    Backward-compatibility stub – legacy file-based version filtering removed.
    Always returns an empty list.
    """
    return []


def can_change_status(current_status: AgreementStatus) -> tuple[bool, str]:
    """
    Check if status change is allowed for current status.
    """
    # Status change rules are now governed directly by ALLOWED_TRANSITIONS.
    # This helper remains for backward compatibility and always defers to that logic.
    return True, ""


def check_can_upload_new_version(
    current_status: AgreementStatus,
    has_signed_version: bool = False
) -> bool:
    """
    Backward-compatibility stub – legacy file-based version uploads are no longer supported.
    Always returns False.
    """
    return False


def filter_versions_by_role(
    versions,
    is_internal: bool = True
) -> list:
    """
    Backward-compatibility stub – legacy file-based version filtering removed.
    Always returns an empty list.
    """
    return []


def is_user_internal(user_id: Optional[str], db: AsyncSession) -> bool:
    """
    Determine if a user is internal or external based on their role assignments.
    
    Internal users: Users with roles like CRA, STUDY_MANAGER, MEDICAL_MONITOR
    External users: Users without these roles (e.g., site coordinators, participants)
    
    Args:
        user_id: User ID to check
        db: Database session
        
    Returns:
        True if user is internal, False if external or None
    """
    if not user_id:
        return False  # Anonymous users are treated as external
    
    # For now, default to True (internal) - can be enhanced with actual role checking
    # TODO: Implement actual role checking based on UserRoleAssignment
    return True


def can_create_comment_type(user_id: Optional[str], comment_type: CommentType, db: AsyncSession) -> tuple[bool, str]:
    """
    Check if user can create a comment of the specified type.
    
    Args:
        user_id: User ID
        comment_type: Comment type to create
        db: Database session
        
    Returns:
        Tuple of (is_allowed, error_message)
    """
    # SYSTEM comments cannot be created manually
    if comment_type == CommentType.SYSTEM:
        return False, "SYSTEM comments cannot be created manually. They are generated automatically."
    
    is_internal = is_user_internal(user_id, db)
    
    # INTERNAL users can create INTERNAL and EXTERNAL comments
    if is_internal:
        if comment_type in [CommentType.INTERNAL, CommentType.EXTERNAL]:
            return True, ""
        return False, f"Invalid comment type for internal user: {comment_type.value}"
    
    # EXTERNAL users can only create EXTERNAL comments
    if comment_type == CommentType.EXTERNAL:
        return True, ""
    
    return False, f"EXTERNAL users cannot create {comment_type.value} comments. Only EXTERNAL comments are allowed."


def filter_comments_by_role(
    comments: List[AgreementComment],
    is_internal: bool = True
) -> List[AgreementComment]:
    """
    Filter comments based on user role.
    
    Args:
        comments: List of agreement comments
        is_internal: True if user is internal, False if external
        
    Returns:
        Filtered list of comments sorted by created_at ASC
    """
    if is_internal:
        # Internal users can see all comments
        filtered = comments
    else:
        # External users can only see EXTERNAL and SYSTEM comments
        filtered = [c for c in comments if c.comment_type in [CommentType.EXTERNAL, CommentType.SYSTEM]]
    
    # Sort by created_at ASC (chronological timeline)
    return sorted(filtered, key=lambda c: c.created_at)


def get_editor_permissions(
    agreement: Agreement,
    is_internal: bool = True
) -> tuple[bool, bool]:
    """
    Determine editor permissions based on agreement status and user role.
    
    Args:
        agreement: Agreement object
        is_internal: Whether user is internal
        
    Returns:
        Tuple of (can_edit, can_comment)
    """
    status = agreement.status
    
    # Check if any document is signed
    has_signed_document = False
    if hasattr(agreement, 'documents') and agreement.documents:
        has_signed_document = any(d.is_signed_version == 'true' for d in agreement.documents)
    
    if has_signed_document:
        return False, False  # Signed documents cannot be edited or commented
    
    # Status-based rules
    if status == AgreementStatus.DRAFT:
        # DRAFT: editable for internal only
        return is_internal, is_internal
    
    elif status == AgreementStatus.UNDER_REVIEW:
        # UNDER_REVIEW: editable for internal only
        return is_internal, is_internal
    
    elif status == AgreementStatus.UNDER_NEGOTIATION:
        # UNDER_NEGOTIATION: editable for internal, comment-only for external
        if is_internal:
            return True, True
        else:
            return False, True  # External can comment but not edit
    
    elif status in [AgreementStatus.READY_FOR_SIGNATURE, AgreementStatus.SENT_FOR_SIGNATURE, AgreementStatus.EXECUTED, AgreementStatus.CLOSED]:
        # All locked statuses: read-only
        return False, False
    
    # Default: no permissions
    return False, False


def get_agreement_permissions(
    agreement: Agreement,
    is_internal: bool = True
) -> dict:
    """
    Get comprehensive permission flags for an agreement based on status and user role.
    
    Args:
        agreement: Agreement object
        is_internal: Whether user is internal
        
    Returns:
        Dictionary with permission flags:
        - can_edit: Can edit document content
        - can_save: Can save document (create new version)
        - can_move_status: Can transition to next status
        - is_locked: Agreement is fully locked (no changes allowed)
    """
    status = agreement.status
    
    # Check if any document is signed
    has_signed_document = False
    if hasattr(agreement, 'documents') and agreement.documents:
        has_signed_document = any(d.is_signed_version == 'true' for d in agreement.documents)
    
    # Locked statuses (no changes allowed)
    locked_statuses = {
        AgreementStatus.READY_FOR_SIGNATURE,
        AgreementStatus.SENT_FOR_SIGNATURE,
        AgreementStatus.EXECUTED,
        AgreementStatus.CLOSED,
    }
    
    is_locked = status in locked_statuses or has_signed_document
    
    # Initialize permissions
    can_edit = False
    can_save = False
    can_move_status = False
    
    if is_locked:
        # Fully locked: no permissions
        return {
            "can_edit": False,
            "can_save": False,
            "can_move_status": False,
            "is_locked": True,
        }
    
    # Status-based rules
    if status == AgreementStatus.DRAFT:
        # DRAFT: editable for internal only
        can_edit = is_internal
        can_save = is_internal
        can_move_status = True  # Can move to UNDER_REVIEW
    
    elif status == AgreementStatus.UNDER_REVIEW:
        # UNDER_REVIEW: editable for internal only
        can_edit = is_internal
        can_save = is_internal
        can_move_status = True  # Can move to UNDER_NEGOTIATION
    
    elif status == AgreementStatus.UNDER_NEGOTIATION:
        # UNDER_NEGOTIATION: editable for internal only (external read-only for now)
        can_edit = is_internal
        can_save = is_internal
        can_move_status = True  # Can move to READY_FOR_SIGNATURE
    
    elif status == AgreementStatus.READY_FOR_SIGNATURE:
        # READY_FOR_SIGNATURE: locked
        can_edit = False
        can_save = False
        can_move_status = True  # Can move to SENT_FOR_SIGNATURE
    
    elif status == AgreementStatus.SENT_FOR_SIGNATURE:
        # SENT_FOR_SIGNATURE: locked
        can_edit = False
        can_save = False
        can_move_status = True  # Can move to EXECUTED
    
    elif status == AgreementStatus.EXECUTED:
        # EXECUTED: permanently locked, no further changes or status transitions allowed
        can_edit = False
        can_save = False
        can_move_status = False  # Permanent lock - no status transitions allowed
    
    elif status == AgreementStatus.CLOSED:
        # CLOSED: fully locked, no transitions
        can_edit = False
        can_save = False
        can_move_status = False
    
    return {
        "can_edit": can_edit,
        "can_save": can_save,
        "can_move_status": can_move_status,
        "is_locked": is_locked,
    }


async def change_agreement_status(
    db: AsyncSession,
    agreement_id: str,
    new_status: AgreementStatus,
    user_id: Optional[str] = None
) -> Agreement:
    """
    Centralized function to change agreement status with strict workflow validation.
    
    This function:
    1. Validates current status
    2. Checks if transition is allowed
    3. Enforces locking rules
    4. Updates status
    5. Creates SYSTEM comment
    
    Args:
        db: Database session
        agreement_id: Agreement UUID
        new_status: Desired new status
        user_id: User ID making the change (optional)
        
    Returns:
        Updated Agreement object
        
    Raises:
        ValueError: If transition is invalid or locked
    """
    # Get agreement with current status
    agreement_result = await db.execute(
        select(Agreement).where(Agreement.id == agreement_id)
    )
    agreement = agreement_result.scalar_one_or_none()
    
    if not agreement:
        raise ValueError(f"Agreement {agreement_id} not found")
    
    logger.info(
        "Agreement %s loaded via study_site_id=%s (study=%s, site=%s)",
        agreement_id,
        getattr(agreement, "study_site_id", None),
        getattr(agreement, "study_id", None),
        getattr(agreement, "site_id", None),
    )
    
    current_status = agreement.status
    
    # Check if status change is allowed at all
    can_change, error_msg = can_change_status(current_status)
    if not can_change:
        raise ValueError(error_msg)
    
    # Validate transition
    if not is_transition_allowed(current_status, new_status):
        allowed_next = ALLOWED_TRANSITIONS.get(current_status, [])
        allowed_str = ", ".join([s.value for s in allowed_next]) if allowed_next else "none"
        raise ValueError(
            f"Invalid status transition: Cannot change from {current_status.value} to {new_status.value}. "
            f"Allowed transitions from {current_status.value}: {allowed_str}"
        )
    
    # Special locking rules for SENT_FOR_SIGNATURE
    if current_status == AgreementStatus.SENT_FOR_SIGNATURE:
        if new_status != AgreementStatus.EXECUTED:
            raise ValueError(
                f"Cannot change status from {current_status.value} to {new_status.value}. "
                f"Only transition to EXECUTED is allowed."
            )
    
    # Store old status for comment
    old_status = current_status.value
    
    # Update status
    agreement.status = new_status
    await db.flush()
    
    # Create system comment for status change
    user_info = f" by {user_id}" if user_id else ""
    comment_content = f"Status changed from {old_status} to {new_status.value}{user_info}"
    
    comment = AgreementComment(
        agreement_id=agreement.id,
        version_id=None,  # version_id is None for status changes
        comment_type=CommentType.SYSTEM,
        content=comment_content,
        created_by=None  # System comments have no creator
    )
    db.add(comment)
    await db.flush()
    
    await db.commit()
    await db.refresh(agreement)
    
    logger.info(
        f"Agreement {agreement_id} status changed from {old_status} to {new_status.value} "
        f"(user: {user_id or 'system'})"
    )
    
    return agreement


async def create_agreement_notice(
    db: AsyncSession,
    agreement: Agreement,
    event_type: str,
    message: str,
    metadata: Optional[Dict] = None,
) -> None:
    """
    Central helper to create Public Notice Board entries for agreement events.

    Resolves Study + Site context and calls create_system_notice_message.
    """
    # Resolve site
    site_result = await db.execute(select(Site).where(Site.id == agreement.site_id))
    site = site_result.scalar_one_or_none()
    if not site:
        logger.warning("create_agreement_notice: site not found for agreement %s", agreement.id)
        return

    site_id_str = site.site_id if hasattr(site, "site_id") else str(site.id)

    # Resolve study via Agreement or StudySite
    study_id_str: Optional[str] = None
    if getattr(agreement, "study_id", None):
        study_result = await db.execute(select(Study).where(Study.id == agreement.study_id))
        study = study_result.scalar_one_or_none()
        if study:
            study_id_str = str(study.id)
    elif getattr(agreement, "study_site_id", None):
        study_site_result = await db.execute(
            select(StudySite).where(StudySite.id == agreement.study_site_id)
        )
        study_site = study_site_result.scalar_one_or_none()
        if study_site:
            study_result = await db.execute(select(Study).where(Study.id == study_site.study_id))
            study = study_result.scalar_one_or_none()
            if study:
                study_id_str = str(study.id)

    try:
        await create_system_notice_message(
            db=db,
            site_id=site_id_str,
            study_id=study_id_str,
            message=message,
            created_by=None,
            metadata=metadata or {},
            event_type=event_type,
        )
        logger.info(
            "Created agreement notice: agreement_id=%s, site_id=%s, study_id=%s, event_type=%s",
            str(agreement.id),
            site_id_str,
            study_id_str,
            event_type,
        )
    except Exception as e:
        logger.error(
            "Failed to create agreement notice for agreement_id=%s: %s",
            str(agreement.id),
            e,
            exc_info=True,
        )
