"""
System notice message helper.
Creates public notice board messages in Conversations for system events.
"""
from typing import Optional, Dict, Any
from app import crud
from app.schemas import MessageCreate
from app.models import MessageDirection, MessageChannel
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.conversation_service import ensure_public_notice_board


async def create_system_notice_message(
    db: AsyncSession,
    site_id: str,
    message: str,
    created_by: Optional[str] = None,
    study_id: Optional[str] = None,
    attachment_url: Optional[str] = None,
    attachment_name: Optional[str] = None,
    attachment_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    event_type: Optional[str] = None,
) -> dict:
    """
    Create a system notice message in the public Conversations feed.
    
    This creates a Conversation entry (public notice board) for system events like:
    - CDA sent
    - CDA signed
    - Status updated
    - Document filed
    
    Args:
        db: Database session
        site_id: Site ID for the notice
        message: The notice message text
        created_by: User who triggered the notice (optional)
        study_id: Study ID (optional)
        
    Returns:
        Public notice board conversation dict
    """
    # Ensure one pinned Public Notice Board exists for this study+site, then append the system message there.
    conversation = await ensure_public_notice_board(db, site_id, study_id)
    conv_id = conversation.get("id") if isinstance(conversation, dict) else conversation.id
    notice_metadata: Dict[str, Any] = {"origin": "system"}
    if study_id:
        notice_metadata["study_id"] = study_id
    if attachment_url:
        notice_metadata["attachment_url"] = attachment_url
    if attachment_name:
        notice_metadata["attachment_name"] = attachment_name
    if attachment_type:
        notice_metadata["attachment_type"] = attachment_type
    if event_type:
        notice_metadata["event_type"] = event_type
    if metadata:
        notice_metadata.update(metadata)
    
    # Create the notice message (no email sending - just a notice)
    msg_create = MessageCreate(
        channel=MessageChannel.EMAIL,  # Use EMAIL channel but won't send
        body=message,
        metadata=notice_metadata,
    )
    
    # Create message with no email mentions (so no email is sent)
    # Pass origin, event_type, and is_activity_event as separate parameters for MongoDB storage
    await crud.create_message(
        db=db,
        conv_id=conv_id,
        msg=msg_create,
        direction=MessageDirection.OUTBOUND,
        author_id=created_by or "system",
        author_name="System",
        origin="system",
        event_type=event_type,
        is_activity_event=True  # System notices are activity events
    )
    
    return conversation


async def createSystemNoticeMessage(
    db: AsyncSession,
    site_id: str,
    message: str,
    created_by: Optional[str] = None,
    study_id: Optional[str] = None,
    attachment_url: Optional[str] = None,
    attachment_name: Optional[str] = None,
    attachment_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    event_type: Optional[str] = None,
) -> dict:
    """CamelCase alias required by product spec."""
    return await create_system_notice_message(
        db=db,
        site_id=site_id,
        message=message,
        created_by=created_by,
        study_id=study_id,
        attachment_url=attachment_url,
        attachment_name=attachment_name,
        attachment_type=attachment_type,
        metadata=metadata,
        event_type=event_type,
    )
