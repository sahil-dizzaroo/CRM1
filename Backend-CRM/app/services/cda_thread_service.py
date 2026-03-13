"""
CDA Thread Integration Service
Handles integration between CDA workflow and Conversation Threads system.
Every CDA lifecycle event is tracked in a dedicated thread.
"""
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.repositories import ThreadRepository, ThreadMessageRepository
from app import crud
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_or_create_agreement_thread(
    db: AsyncSession,
    site_id: str,
    study_id: Optional[str] = None,
    agreement_type: str = "CDA",
    created_by: Optional[str] = None,
    participant_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get or create an agreement thread for a specific site/study combination.
    
    Args:
        db: Database session
        site_id: Site identifier (UUID string or site_id)
        study_id: Optional study identifier
        agreement_type: Type of agreement ('CDA', 'CTA', etc.)
        created_by: User ID who created the thread (if new)
        
    Returns:
        Thread dictionary from MongoDB
    """
    # Find existing thread
    # Convert site_id to string if it's a UUID
    site_id_str = str(site_id) if site_id else None
    study_id_str = str(study_id) if study_id else None
    
    logger.info(f"[CDA_THREAD] Searching for agreement thread - site_id: {site_id_str}, study_id: {study_id_str}, agreement_type: {agreement_type}")
    
    try:
        threads = await ThreadRepository.list(
            limit=100,
            offset=0,
            thread_type="agreement",
            study_id=study_id_str,
            site_id=site_id_str
        )
        logger.info(f"[CDA_THREAD] Found {len(threads)} agreement threads matching site_id and study_id")
    except Exception as e:
        logger.error(f"[CDA_THREAD] Error listing threads: {e}", exc_info=True)
        threads = []
    
    # Filter by agreement_type
    matching_thread = None
    for thread in threads:
        thread_agreement_type = thread.get('agreement_type')
        logger.debug(f"Checking thread {thread.get('id')} - agreement_type: {thread_agreement_type}")
        if thread_agreement_type == agreement_type:
            matching_thread = thread
            logger.info(f"Found matching {agreement_type} thread: {thread.get('id')}")
            break
    
    if matching_thread:
        # Backfill participants_emails for visibility if missing on existing thread.
        normalized_email = (participant_email or "").strip().lower()
        existing_emails = [str(e).strip().lower() for e in (matching_thread.get("participants_emails") or []) if e]
        if normalized_email and normalized_email not in existing_emails:
            existing_emails.append(normalized_email)
            await ThreadRepository.update(matching_thread.get("id"), {"participants_emails": existing_emails})
            matching_thread["participants_emails"] = existing_emails
        logger.info(f"Found existing {agreement_type} thread: {matching_thread.get('id')}")
        return matching_thread
    
    # Create new thread
    logger.info(f"[CDA_THREAD] No existing thread found, creating new {agreement_type} thread...")
    try:
        from app.schemas import ThreadCreate
        thread_data = ThreadCreate(
            title="CDA Discussion",
            description=f"Conversation thread for {agreement_type} workflow",
            thread_type="agreement",
            related_study_id=study_id_str,
            site_id=site_id_str,
            priority="medium",
            created_by=created_by,
            participants_emails=[participant_email.strip().lower()] if participant_email and participant_email.strip() else [],
            agreement_type=agreement_type
        )
        
        logger.info(f"[CDA_THREAD] Calling crud.create_thread with data: {thread_data.dict()}")
        new_thread = await crud.create_thread(db, thread_data)
        if new_thread:
            logger.info(f"[CDA_THREAD] Created new {agreement_type} thread: {new_thread.get('id')}")
        else:
            logger.error(f"[CDA_THREAD] crud.create_thread returned None")
        return new_thread
    except Exception as e:
        logger.error(f"[CDA_THREAD] Error creating thread: {e}", exc_info=True)
        import traceback
        logger.error(f"[CDA_THREAD] Traceback: {traceback.format_exc()}")
        raise


async def append_system_message_to_thread(
    thread_id: UUID,
    message: str,
    created_by: Optional[str] = None
) -> bool:
    """
    Append a system message to a thread.
    
    Args:
        thread_id: UUID of the thread
        message: Message content
        created_by: Optional user ID (defaults to 'system')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import uuid
        from app.schemas import ThreadMessageCreate
        
        message_data = ThreadMessageCreate(
            body=message,
            author_id=created_by or "system",
            author_name="System",
            message_type="system"
        )
        
        # Create message using crud function
        from app.repositories import ThreadRepository
        thread = await ThreadRepository.get_by_id(thread_id)
        if not thread:
            logger.error(f"Thread not found: {thread_id}")
            return False
        
        # We need to use the ThreadMessageRepository directly since crud.create_thread_message
        # requires a db session. Let's create it directly.
        system_message_data = {
            'id': uuid.uuid4(),
            'thread_id': thread_id,
            'body': message,
            'author_id': created_by or 'system',
            'author_name': 'System',
            'message_type': 'system',
            'message_id': None
        }
        
        await ThreadMessageRepository.create(system_message_data)
        
        logger.info(f"Added system message to thread {thread_id}: {message[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error appending system message to thread {thread_id}: {str(e)}")
        return False


async def log_cda_event(
    db: AsyncSession,
    site_id: str,
    study_id: Optional[str],
    event_type: str,
    message: str,
    created_by: Optional[str] = None,
    participant_email: Optional[str] = None,
) -> bool:
    """
    Log a CDA event to the appropriate thread.
    
    Args:
        db: Database session
        site_id: Site identifier
        study_id: Optional study identifier
        event_type: Type of event ('send', 'sync', 'signed', 'complete')
        message: Message to log
        created_by: Optional user ID
        
    Returns:
        bool: True if successful
    """
    try:
        logger.info(f"[CDA_THREAD] Logging CDA event - type: {event_type}, site_id: {site_id}, study_id: {study_id}")
        
        # Get or create CDA thread
        logger.info(f"[CDA_THREAD] Getting or creating agreement thread...")
        thread = await get_or_create_agreement_thread(
            db=db,
            site_id=site_id,
            study_id=study_id,
            agreement_type="CDA",
            created_by=created_by,
            participant_email=participant_email,
        )
        
        if not thread:
            logger.error(f"[CDA_THREAD] Failed to get or create CDA thread for site_id: {site_id}, study_id: {study_id}")
            return False
        
        thread_id = thread.get('id')
        if not thread_id:
            logger.error(f"[CDA_THREAD] Thread created but has no ID: {thread}")
            return False
            
        if isinstance(thread_id, str):
            thread_id = UUID(thread_id)
        
        logger.info(f"[CDA_THREAD] Got/created CDA thread: {thread_id}, appending message...")
        
        # Append system message
        success = await append_system_message_to_thread(
            thread_id=thread_id,
            message=message,
            created_by=created_by
        )
        
        if success:
            logger.info(f"[CDA_THREAD] Successfully logged CDA event to thread {thread_id}")
        else:
            logger.error(f"[CDA_THREAD] Failed to append message to thread {thread_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"[CDA_THREAD] Error logging CDA event: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"[CDA_THREAD] Traceback: {traceback.format_exc()}")
        return False
