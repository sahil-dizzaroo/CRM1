from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from app.models import (
    Conversation,
    Message,
    AuditLog,
    MessageDirection,
    MessageStatus,
    MessageChannel,
    Thread,
    ThreadParticipant,
    ThreadMessage,
    ThreadAttachment,
    User,
    ConversationAccess,
    ConversationAccessLevel,
    UserRole,
    AccessType,
    Attachment,
    RDStudy,
    IISStudy,
    Event,
    UserProfile,
    ChatMessage,
    ChatDocument,
    Study,
    Site,
    SiteStatus,
    SiteStatusHistory,
    PrimarySiteStatus,
    UserRoleAssignment,
    StudySite,
)
from app.schemas import (
    ConversationCreate, MessageCreate, ThreadCreate, ThreadParticipantCreate, ThreadMessageCreate,
    UserCreate, ConversationAccessCreate,
    RDStudyCreate, IISStudyCreate, EventCreate, UserProfileCreate,
    ChatMessageCreate
)
from app.repositories import (
    ConversationRepository, MessageRepository, AttachmentRepository,
    ThreadRepository, ThreadParticipantRepository, ThreadMessageRepository,
    ThreadAttachmentRepository, ThreadFromConversationRepository,
    ConversationAccessRepository, UserRoleAssignmentRepository, StudyRepository, SiteRepository
)
from datetime import datetime, timezone
import uuid
import shortuuid


async def create_conversation(db: AsyncSession, conv: ConversationCreate) -> Dict[str, Any]:
    """Create a conversation in MongoDB. Returns dict for compatibility."""
    conv_dict = conv.dict()
    print(f"[MONGO] Creating conversation with data: {conv_dict}")  # Debug log
    
    # Handle participant_emails: convert participant_email to array if needed
    if conv_dict.get('participant_emails'):
        # participant_emails provided - use it
        participant_emails = [email.strip() for email in conv_dict['participant_emails'] if email and email.strip()]
        conv_dict['participant_emails'] = participant_emails
        # Set first email as participant_email for backward compatibility
        if participant_emails and not conv_dict.get('participant_email'):
            conv_dict['participant_email'] = participant_emails[0]
    elif conv_dict.get('participant_email'):
        # Only participant_email provided - convert to participant_emails array
        conv_dict['participant_emails'] = [conv_dict['participant_email']]
    else:
        # Neither provided - set empty array
        conv_dict['participant_emails'] = []
    
    # Generate UUID if not provided
    if 'id' not in conv_dict:
        conv_dict['id'] = uuid.uuid4()
    
    # Generate tracker_code if not provided
    if 'tracker_code' not in conv_dict or not conv_dict.get('tracker_code'):
        conv_dict['tracker_code'] = f"DZ-{shortuuid.uuid()[:8].upper()}"
    
    # CRITICAL: Normalize is_pinned - only Public Notice Board should be pinned
    # Default to 'false' unless explicitly set to True (only for system-created notice boards)
    if 'is_pinned' not in conv_dict:
        conv_dict['is_pinned'] = 'false'
    elif conv_dict['is_pinned'] is None:
        conv_dict['is_pinned'] = 'false'
    else:
        # Convert boolean/string to proper string value
        is_pinned_val = conv_dict['is_pinned']
        if isinstance(is_pinned_val, bool):
            conv_dict['is_pinned'] = 'true' if is_pinned_val else 'false'
        elif isinstance(is_pinned_val, str):
            conv_dict['is_pinned'] = 'true' if is_pinned_val.lower().strip() == 'true' else 'false'
        else:
            conv_dict['is_pinned'] = 'false'
    
    # Convert boolean to string for is_restricted and is_confidential
    if 'is_restricted' in conv_dict and conv_dict['is_restricted'] is not None:
        conv_dict['is_restricted'] = 'true' if conv_dict['is_restricted'] else 'false'
    if 'is_confidential' in conv_dict and conv_dict['is_confidential'] is not None:
        conv_dict['is_confidential'] = 'true' if conv_dict['is_confidential'] else 'false'
    # Set default access_level
    if 'access_level' not in conv_dict:
        conv_dict['access_level'] = 'PUBLIC'
    # Explicit type for notice-board behavior
    if 'conversation_type' not in conv_dict or not conv_dict.get('conversation_type'):
        conv_dict['conversation_type'] = 'notice_board'
    
    print(f"[MONGO] Final conversation data before DB insert: {conv_dict}")  # Debug log
    print(f"[MONGO] participant_emails before insert: {conv_dict.get('participant_emails')}")  # Debug log
    db_conv = await ConversationRepository.create(conv_dict)
    print(f"[MONGO] Created conversation with site_id: {db_conv.get('site_id')}, tracker_code: {db_conv.get('tracker_code')}")  # Debug log
    print(f"[MONGO] participant_emails after retrieval: {db_conv.get('participant_emails')}")  # Debug log
    return db_conv


async def get_conversation(db: AsyncSession, conv_id: UUID) -> Optional[Dict[str, Any]]:
    """Get conversation from MongoDB. Returns dict for compatibility."""
    return await ConversationRepository.get_by_id(conv_id)


async def list_conversations(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    study_id: Optional[str] = None,
    site_id: Optional[str] = None,
    channel: Optional[MessageChannel] = None,
    user_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List conversations from MongoDB with optional filters. 
    
    NEW BEHAVIOR: Conversations are PUBLIC - all users with site access can see all conversation messages.
    No filtering by user - conversations act as a public notice board.
    """
    # Get conversations from MongoDB - no user filtering for public notice board
    conversations = await ConversationRepository.list(
        limit=limit,
        offset=offset,
        study_id=study_id,
        site_id=site_id,
        channel=channel,
        user_id=None  # Don't filter by user - conversations are public
    )
    
    return conversations


async def get_conversation_stats(db: AsyncSession, user_id: Optional[str] = None) -> dict:
    """Get conversation statistics filtered by user access. Uses MongoDB aggregation."""
    from app.db_mongo import get_mongo_db
    
    # Get accessible conversations from MongoDB
    conversations = await ConversationRepository.list(limit=1000, offset=0, user_id=user_id)
    
    # Filter by access using Postgres ConversationAccess if user_id provided
    accessible_conversation_ids = []
    for conv in conversations:
        conv_id = conv.get('id')
        if not conv_id:
            continue
        
        # Public conversations - already filtered by repository
        if conv.get('is_confidential') != 'true' and (not conv.get('access_level') or conv.get('access_level') == 'PUBLIC' or conv.get('access_level') == 'public'):
            accessible_conversation_ids.append(conv_id)
        else:
            # Check Postgres for explicit access grants
            if user_id:
                access_type = await check_user_access(db, conv_id, user_id)
                if access_type is not None:
                    accessible_conversation_ids.append(conv_id)
    
    total_conversations = len(accessible_conversation_ids)
    
    # Use MongoDB aggregation to get message statistics
    mongo_db = await get_mongo_db()
    messages_collection = mongo_db[MessageRepository.COLLECTION_NAME]
    
    if accessible_conversation_ids:
        # Convert UUIDs to strings for MongoDB query
        conv_id_strs = [str(cid) for cid in accessible_conversation_ids]
        
        # Total messages
        total_messages = await messages_collection.count_documents({"conversation_id": {"$in": conv_id_strs}})
        
        # Messages by channel (aggregation pipeline)
        channel_pipeline = [
            {"$match": {"conversation_id": {"$in": conv_id_strs}}},
            {"$group": {"_id": "$channel", "count": {"$sum": 1}}}
        ]
        channel_stats = {}
        async for doc in messages_collection.aggregate(channel_pipeline):
            channel_stats[doc["_id"]] = doc["count"]
        
        # Messages by status (aggregation pipeline)
        status_pipeline = [
            {"$match": {"conversation_id": {"$in": conv_id_strs}}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_stats = {}
        async for doc in messages_collection.aggregate(status_pipeline):
            status_stats[doc["_id"]] = doc["count"]
    else:
        total_messages = 0
        channel_stats = {}
        status_stats = {}
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "by_channel": channel_stats,
        "by_status": status_stats
    }


async def get_conversation_with_messages(
    db: AsyncSession, 
    conv_id: UUID, 
    limit: int = 50, 
    offset: int = 0
) -> Optional[Dict[str, Any]]:
    """Get conversation with messages from MongoDB. Returns dict for compatibility."""
    conv = await ConversationRepository.get_by_id(conv_id)
    if conv:
        # Load messages from MongoDB
        messages = await MessageRepository.list_by_conversation(conv_id, limit, offset)
        # Public Notice Board should be chronological (oldest first).
        if conv.get("conversation_type") == "notice_board":
            messages = sorted(
                messages,
                key=lambda m: m.get("created_at") or datetime.min,
                reverse=False,
            )
        conv['messages'] = messages
    return conv


async def create_message(
    db: AsyncSession, 
    conv_id: UUID, 
    msg: MessageCreate, 
    direction: MessageDirection = MessageDirection.OUTBOUND,
    author_id: Optional[str] = None,
    author_name: Optional[str] = None,
    origin: Optional[str] = "user",
    event_type: Optional[str] = None,
    is_activity_event: Optional[bool] = False
) -> Dict[str, Any]:
    """Create a message in MongoDB. Returns dict for compatibility."""
    # Inbound messages should be DELIVERED, outbound should be QUEUED
    initial_status = MessageStatus.DELIVERED if direction == MessageDirection.INBOUND else MessageStatus.QUEUED
    
    # Extract mentioned emails from message body
    from app.utils.email_mentions import extract_mention_emails
    mentioned_emails = extract_mention_emails(msg.body)
    
    # Prepare metadata - include origin, event_type, and is_activity_event in metadata for backward compatibility
    message_metadata = msg.metadata or {}
    if origin:
        message_metadata['origin'] = origin
    if event_type:
        message_metadata['event_type'] = event_type
    if is_activity_event:
        message_metadata['is_activity_event'] = is_activity_event
    
    msg_data = {
        'id': uuid.uuid4(),
        'conversation_id': conv_id,
        'direction': direction,
        'channel': msg.channel,
        'body': msg.body,
        'status': initial_status,
        'message_metadata': message_metadata,
        'author_id': author_id,
        'author_name': author_name,
        'mentioned_emails': mentioned_emails,  # Store extracted email mentions
        'origin': origin or "user",  # Store as top-level field for easy access
        'event_type': event_type,  # Store as top-level field for easy access
        'is_activity_event': is_activity_event if is_activity_event is not None else False  # Store as top-level field
    }
    # Set delivered_at for inbound messages
    if direction == MessageDirection.INBOUND:
        msg_data['delivered_at'] = datetime.now(timezone.utc)
    
    db_msg = await MessageRepository.create(msg_data)
    return db_msg


async def get_message(db: AsyncSession, msg_id: UUID) -> Optional[Dict[str, Any]]:
    """Get message from MongoDB. Returns dict for compatibility."""
    return await MessageRepository.get_by_id(msg_id)


async def update_message_status(
    db: AsyncSession,
    msg_id: UUID,
    status: MessageStatus,
    provider_message_id: Optional[str] = None,
    sent_at: Optional[datetime] = None,
    delivered_at: Optional[datetime] = None
) -> Optional[Dict[str, Any]]:
    """Update message status in MongoDB. Returns dict for compatibility."""
    return await MessageRepository.update_status(
        msg_id, status, provider_message_id, sent_at, delivered_at
    )


async def create_audit_log(
    db: AsyncSession,
    user: Optional[str],
    action: str,
    target_type: str,
    target_id: str,
    details: Optional[dict] = None
):
    log = AuditLog(
        user=user,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {}
    )
    db.add(log)
    await db.commit()


# Thread CRUD operations
async def create_thread(db: AsyncSession, thread: ThreadCreate) -> Dict[str, Any]:
    """Create a thread in MongoDB. Threads can be created independently or linked to a conversation."""
    conv = None
    conv_study_id = None
    conv_site_id = None
    conv_email = None
    
    # Only verify conversation if provided
    if thread.conversation_id:
        conv = await get_conversation(db, thread.conversation_id)
        if not conv:
            raise ValueError(f"Conversation {thread.conversation_id} not found")
        
        # Handle dict from MongoDB
        conv_study_id = conv.get('study_id') if isinstance(conv, dict) else conv.study_id
        conv_site_id = conv.get('site_id') if isinstance(conv, dict) else getattr(conv, 'site_id', None)
        conv_email = conv.get('participant_email') if isinstance(conv, dict) else getattr(conv, 'participant_email', None)
    
    # Extract participants_emails from thread create request
    participants_emails = []
    if hasattr(thread, 'participants_emails') and thread.participants_emails:
        participants_emails = [email.strip().lower() for email in thread.participants_emails if email and email.strip()]
        participants_emails = list(dict.fromkeys(participants_emails))
    # Also extract from participants list if provided
    if thread.participants:
        for participant in thread.participants:
            if participant.participant_email and participant.participant_email.strip():
                normalized_email = participant.participant_email.strip().lower()
                if normalized_email not in participants_emails:
                    participants_emails.append(normalized_email)
    
    # Validate visibility_scope
    visibility_scope = getattr(thread, 'visibility_scope', 'private')
    if visibility_scope not in ['private', 'site']:
        visibility_scope = 'private'  # Default to private if invalid
    
    thread_data = {
        'id': uuid.uuid4(),
        'conversation_id': thread.conversation_id,  # Can be None
        'title': thread.title,
        'description': thread.description,
        'thread_type': thread.thread_type,
        'related_patient_id': thread.related_patient_id,
        'related_study_id': thread.related_study_id or conv_study_id,
        'site_id': thread.site_id or conv_site_id,
        'priority': thread.priority,
        'created_by': thread.created_by,
        'status': 'open',
        'participants_emails': participants_emails,  # Store participant emails for access control
        'visibility_scope': visibility_scope,  # 'private' or 'site'
        'tmf_filed': False,
        'tmf_filed_at': None,
        'conversation_address': None,
        'agreement_type': thread.agreement_type if hasattr(thread, 'agreement_type') else None
    }
    
    db_thread = await ThreadRepository.create(thread_data)
    
    # Create ThreadFromConversation link only if conversation_id is provided
    if thread.conversation_id:
        link_data = {
            'id': uuid.uuid4(),
            'thread_id': db_thread.get('id'),
            'conversation_id': thread.conversation_id,
            'source_message_ids': [],  # Empty for threads created independently
            'created_by': thread.created_by
        }
        await ThreadFromConversationRepository.create(link_data)
    
    # Add participants
    if thread.participants:
        for participant in thread.participants:
            participant_data = {
                'id': uuid.uuid4(),
                'thread_id': db_thread.get('id'),
                'participant_id': participant.participant_id,
                'participant_name': participant.participant_name,
                'participant_email': participant.participant_email,
                'role': participant.role
            }
            await ThreadParticipantRepository.create(participant_data)
    elif conv_email:
        # If no participants specified and thread is linked to conversation, add conversation participant as default
        conv_phone = conv.get('participant_phone') if isinstance(conv, dict) else getattr(conv, 'participant_phone', None)
        if conv_email or conv_phone:
            default_participant_data = {
                'id': uuid.uuid4(),
                'thread_id': db_thread.get('id'),
                'participant_id': conv_email or conv_phone or "unknown",
                'participant_name': None,
                'participant_email': conv_email,
                'role': 'participant'
            }
            await ThreadParticipantRepository.create(default_participant_data)
    
    # Load participants for response
    participants = await ThreadParticipantRepository.list_by_thread(db_thread.get('id'))
    db_thread['participants'] = participants
    
    return db_thread


async def get_thread(db: AsyncSession, thread_id: UUID) -> Optional[Dict[str, Any]]:
    """Get thread from MongoDB. Returns dict for compatibility."""
    thread = await ThreadRepository.get_by_id(thread_id)
    if thread:
        # Load participants
        participants = await ThreadParticipantRepository.list_by_thread(thread_id)
        thread['participants'] = participants
    return thread


async def get_thread_with_messages(
    db: AsyncSession,
    thread_id: UUID,
    limit: int = 50,
    offset: int = 0
) -> Optional[Dict[str, Any]]:
    """Get thread with messages from MongoDB. Returns dict for compatibility."""
    thread = await ThreadRepository.get_by_id(thread_id)
    if thread:
        # Load participants
        participants = await ThreadParticipantRepository.list_by_thread(thread_id)
        thread['participants'] = participants
        
        # Load messages
        messages = await ThreadMessageRepository.list_by_thread(thread_id, limit, offset)
        thread['messages'] = messages
    return thread


async def list_threads(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    thread_type: Optional[str] = None,
    status: Optional[str] = None,
    participant_id: Optional[str] = None,
    study_id: Optional[str] = None,
    site_id: Optional[str] = None,
    user_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List threads from MongoDB with optional filters. 
    
    VISIBILITY RULES (aligned with product requirements):
    - Private threads: only visible if user's email is in participants_emails.
    - Site-visible threads: visible to any authenticated user for the selected study/site.
    """
    normalized_user_email = user_email.lower().strip() if user_email else None
    if not normalized_user_email:
        return []

    # 1) Threads where repository already applies user_email-based filtering
    user_threads = await ThreadRepository.list(
        limit=limit,
        offset=offset,
        thread_type=thread_type,
        status=status,
        participant_id=participant_id,
        study_id=study_id,
        site_id=site_id,
        user_email=normalized_user_email,
    )

    # 2) Additional threads for this study/site (used to pick up site-visible threads)
    all_threads_for_site = await ThreadRepository.list(
        limit=limit * 2,
        offset=0,
        thread_type=thread_type,
        status=status,
        participant_id=participant_id,
        study_id=study_id,
        site_id=site_id,
        user_email=None,
    )

    # Merge, de-duplicate by id
    threads_by_id: Dict[Any, Dict[str, Any]] = {}
    for t in user_threads + all_threads_for_site:
        tid = t.get("id")
        if tid is not None:
            threads_by_id[tid] = t

    visible_threads: List[Dict[str, Any]] = []
    for thread in threads_by_id.values():
        visibility_scope = str(thread.get("visibility_scope", "private") or "").strip().lower()
        participants_emails = [
            str(e).lower().strip() for e in (thread.get("participants_emails") or []) if e
        ]

        if visibility_scope == "site":
            # Site-visible: allow all users for the selected study/site
            visible_threads.append(thread)
            continue

        # Private or unknown scope: only if user is an explicit participant
        if normalized_user_email in participants_emails:
            visible_threads.append(thread)

    # Load participants for each visible thread
    for thread in visible_threads:
        thread_id = thread.get('id')
        if thread_id:
            participants = await ThreadParticipantRepository.list_by_thread(thread_id)
            thread['participants'] = participants

    return visible_threads


async def add_thread_participant(
    db: AsyncSession,
    thread_id: UUID,
    participant: ThreadParticipantCreate
) -> Dict[str, Any]:
    """Add thread participant in MongoDB. Returns dict for compatibility."""
    participant_data = {
        'id': uuid.uuid4(),
        'thread_id': thread_id,
        'participant_id': participant.participant_id,
        'participant_name': participant.participant_name,
        'participant_email': participant.participant_email,
        'role': participant.role
    }
    return await ThreadParticipantRepository.create(participant_data)


async def create_thread_message(
    db: AsyncSession,
    thread_id: UUID,
    message: ThreadMessageCreate
) -> Dict[str, Any]:
    """Create thread message in MongoDB. Returns dict for compatibility."""
    # Extract mentioned emails from message body
    from app.utils.email_mentions import extract_mention_emails
    mentioned_emails = extract_mention_emails(message.body)
    
    message_data = {
        'id': uuid.uuid4(),
        'thread_id': thread_id,
        'message_id': message.message_id,
        'body': message.body,
        'author_id': message.author_id,
        'author_name': message.author_name,
        'mentioned_emails': mentioned_emails,  # Store extracted email mentions
        'message_type': message.message_type if hasattr(message, 'message_type') else None
    }
    db_message = await ThreadMessageRepository.create(message_data)
    
    # Update thread updated_at
    await ThreadRepository.update(thread_id, {'updated_at': datetime.now(timezone.utc)})
    
    return db_message


async def update_thread_status(
    db: AsyncSession,
    thread_id: UUID,
    status: str
) -> Optional[Dict[str, Any]]:
    """Update thread status in MongoDB. Returns dict for compatibility."""
    return await ThreadRepository.update(thread_id, {
        'status': status,
        'updated_at': datetime.now(timezone.utc)
    })


async def add_thread_participant_email(
    db: AsyncSession,
    thread_id: UUID,
    email: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Add an email to thread's participants_emails list. Only thread creator or existing participant can modify."""
    # Get thread
    thread = await ThreadRepository.get_by_id(thread_id)
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")
    
    # Check authorization: only thread creator OR existing participant can modify
    if user_email:
        user_email_lower = user_email.lower().strip()
        created_by = thread.get('created_by', '').lower().strip()
        participants_emails = [str(e).lower().strip() for e in (thread.get('participants_emails') or []) if e]
        
        if user_email_lower != created_by and user_email_lower not in participants_emails:
            raise ValueError("Only thread creator or existing participants can modify participant list")
    
    # Normalize email
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email cannot be empty")
    
    # Get current participants_emails
    participants_emails = thread.get('participants_emails', []) or []
    participants_emails = [str(e).lower().strip() for e in participants_emails if e]
    
    # Add if not already present (prevent duplicates)
    if normalized_email not in participants_emails:
        participants_emails.append(normalized_email)
        
        # Update thread
        updated = await ThreadRepository.update(thread_id, {
            'participants_emails': participants_emails,
            'updated_at': datetime.now(timezone.utc)
        })
        
        return updated or thread
    else:
        # Already exists, return thread as-is
        return thread


async def remove_thread_participant_email(
    db: AsyncSession,
    thread_id: UUID,
    email: str,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """Remove an email from thread's participants_emails list. Only thread creator or existing participant can modify."""
    # Get thread
    thread = await ThreadRepository.get_by_id(thread_id)
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")
    
    # Check authorization: only thread creator OR existing participant can modify
    if user_email:
        user_email_lower = user_email.lower().strip()
        created_by = thread.get('created_by', '').lower().strip()
        participants_emails = [str(e).lower().strip() for e in (thread.get('participants_emails') or []) if e]
        
        if user_email_lower != created_by and user_email_lower not in participants_emails:
            raise ValueError("Only thread creator or existing participants can modify participant list")
    
    # Normalize email
    normalized_email = email.strip().lower()
    
    # Get current participants_emails
    participants_emails = thread.get('participants_emails', []) or []
    participants_emails = [str(e).lower().strip() for e in participants_emails if e]
    
    # Remove if present
    if normalized_email in participants_emails:
        participants_emails.remove(normalized_email)
        
        # Update thread
        updated = await ThreadRepository.update(thread_id, {
            'participants_emails': participants_emails,
            'updated_at': datetime.now(timezone.utc)
        })
        
        return updated or thread
    else:
        # Not found, return thread as-is
        return thread


async def create_thread_from_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    title: str,
    description: Optional[str],
    thread_type: str,
    message_ids: List[UUID],
    created_by: Optional[str] = None,
    creator_email: Optional[str] = None,
    related_study_id: Optional[str] = None,
    visibility_scope: Optional[str] = None,
    participants_emails: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a thread from selected messages in a conversation. Uses MongoDB."""
    # Verify conversation exists
    conv = await get_conversation(db, conversation_id)
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found")
    
    # Get the selected messages from MongoDB
    all_messages = []
    for msg_id in message_ids:
        msg = await MessageRepository.get_by_id(msg_id)
        if msg and msg.get('conversation_id') == conversation_id:
            all_messages.append(msg)
    
    if len(all_messages) != len(message_ids):
        raise ValueError("Some message IDs not found in conversation")
    
    # Handle dict from MongoDB
    conv_study_id = conv.get('study_id') if isinstance(conv, dict) else conv.study_id
    effective_study_id = conv_study_id or related_study_id
    conv_site_id = conv.get('site_id') if isinstance(conv, dict) else getattr(conv, 'site_id', None)
    conv_email = conv.get('participant_email') if isinstance(conv, dict) else getattr(conv, 'participant_email', None)

    # Normalize visibility scope; default to private
    scope = (visibility_scope or "private").strip().lower()
    if scope not in ("private", "site"):
        scope = "private"

    # Build participants_emails list for private threads only.
    # - Start from any explicit participants_emails passed in the request
    # - Optionally include conversation participant email (if any)
    # - Always include creator email (if any)
    merged_emails: List[str] = []
    if scope == "private":
        for e in (participants_emails or []):
            if e and str(e).strip():
                merged_emails.append(str(e).strip().lower())
        if conv_email and str(conv_email).strip():
            merged_emails.append(str(conv_email).strip().lower())
        if creator_email and str(creator_email).strip():
            merged_emails.append(str(creator_email).strip().lower())
    # Keep order while de-duplicating
    participants_emails_final = list(dict.fromkeys(merged_emails)) if scope == "private" else []
    
    # Create the thread in MongoDB
    thread_data = {
        'id': uuid.uuid4(),
        'conversation_id': conversation_id,
        'title': title,
        'description': description,
        'thread_type': thread_type,
        'related_patient_id': None,  # Explicitly set to None
        'related_study_id': effective_study_id,
        'site_id': conv_site_id,
        'participants_emails': participants_emails_final,
        'visibility_scope': scope,
        'created_by': created_by,
        'status': 'open',
        'priority': 'medium',
        'tmf_filed': False,
        'tmf_filed_at': None,
        'conversation_address': None,
        'agreement_type': None
    }
    thread = await ThreadRepository.create(thread_data)
    thread_id = thread.get('id')
    
    # Create ThreadFromConversation link (required for all threads)
    link_data = {
        'id': uuid.uuid4(),
        'thread_id': thread_id,
        'conversation_id': conversation_id,
        'source_message_ids': [str(msg_id) for msg_id in message_ids],
        'created_by': created_by
    }
    await ThreadFromConversationRepository.create(link_data)
    
    # Add conversation participant as thread participant
    conv_phone = conv.get('participant_phone') if isinstance(conv, dict) else getattr(conv, 'participant_phone', None)
    if conv_email or conv_phone:
        participant_data = {
            'id': uuid.uuid4(),
            'thread_id': thread_id,
            'participant_id': conv_email or conv_phone or "unknown",
            'participant_name': None,
            'participant_email': conv_email,
            'role': 'participant'
        }
        await ThreadParticipantRepository.create(participant_data)
    
    # Create thread messages from conversation messages (preserve links)
    # Sort by created_at (oldest first for thread)
    sorted_messages = sorted(all_messages, key=lambda m: m.get('created_at', datetime.min), reverse=False)
    for msg in sorted_messages:
        thread_msg_data = {
            'id': uuid.uuid4(),
            'thread_id': thread_id,
            'message_id': msg.get('id'),  # Link to original message
            'body': msg.get('body'),
            'author_id': msg.get('author_id') or msg.get('direction', 'unknown'),
            'author_name': msg.get('author_name')
        }
        await ThreadMessageRepository.create(thread_msg_data)
    
    # Link conversation attachments to the thread
    await link_conversation_attachments_to_thread(db, thread_id, conversation_id, message_ids)
    
    # Load participants for response
    participants = await ThreadParticipantRepository.list_by_thread(thread_id)
    thread['participants'] = participants
    
    return thread


# Access Control CRUD Functions
async def create_user(db: AsyncSession, user: UserCreate, password_hash: Optional[str] = None) -> User:
    """Create a new user."""
    user_dict = user.dict(exclude={'password'})  # Exclude password from dict
    user_dict['is_privileged'] = 'true' if user_dict.get('is_privileged', False) else 'false'
    if 'role' in user_dict:
        try:
            user_dict['role'] = UserRole(user_dict['role'])
        except ValueError:
            user_dict['role'] = UserRole.PARTICIPANT
    
    if password_hash:
        user_dict['password_hash'] = password_hash
    
    db_user = User(**user_dict)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    from app.auth import verify_password
    
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by user_id."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, limit: int = 100, offset: int = 0) -> List[User]:
    """List all users."""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def is_user_privileged(db: AsyncSession, user_id: str) -> bool:
    """Check if a user has privileged access."""
    user = await get_user(db, user_id)
    if not user:
        return False
    return user.is_privileged == 'true'


async def update_conversation_access(
    db: AsyncSession,
    conversation_id: UUID,
    is_restricted: Optional[bool] = None,
    is_confidential: Optional[bool] = None,
    privileged_users: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Update conversation access settings in MongoDB. Returns dict for compatibility."""
    conv = await get_conversation(db, conversation_id)
    if not conv:
        return None
    
    updates = {}
    if is_restricted is not None:
        updates['is_restricted'] = 'true' if is_restricted else 'false'
        if is_restricted:
            updates['access_level'] = 'RESTRICTED'
    
    if is_confidential is not None:
        updates['is_confidential'] = 'true' if is_confidential else 'false'
        if is_confidential:
            updates['access_level'] = 'CONFIDENTIAL'
    
    if privileged_users is not None:
        updates['privileged_users'] = privileged_users
    
    if updates:
        return await ConversationRepository.update(conversation_id, updates)
    return conv


async def grant_conversation_access(
    db: AsyncSession,
    conversation_id: UUID,
    access: ConversationAccessCreate
) -> ConversationAccess:
    """Grant access to a conversation for a user."""
    # Check if access already exists
    result = await db.execute(
        select(ConversationAccess)
        .where(ConversationAccess.conversation_id == conversation_id)
        .where(ConversationAccess.user_id == access.user_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Update existing access
        existing.access_type = AccessType(access.access_type)
        existing.granted_by = access.granted_by
        await db.commit()
        await db.refresh(existing)
        return existing
    
    # Create new access
    access_dict = access.dict()
    access_dict['conversation_id'] = conversation_id
    access_dict['access_type'] = AccessType(access_dict['access_type'])
    
    db_access = ConversationAccess(**access_dict)
    db.add(db_access)
    await db.commit()
    await db.refresh(db_access)
    return db_access


async def revoke_conversation_access(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: str
) -> bool:
    """Revoke access to a conversation for a user."""
    result = await db.execute(
        select(ConversationAccess)
        .where(ConversationAccess.conversation_id == conversation_id)
        .where(ConversationAccess.user_id == user_id)
    )
    access = result.scalar_one_or_none()
    
    if access:
        await db.delete(access)
        await db.flush()
        await db.commit()
        return True
    return False


async def get_conversation_access_list(
    db: AsyncSession,
    conversation_id: UUID
) -> List[ConversationAccess]:
    """Get list of all users with access to a conversation."""
    result = await db.execute(
        select(ConversationAccess)
        .where(ConversationAccess.conversation_id == conversation_id)
    )
    return list(result.scalars().all())


async def check_user_access(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: str
) -> Optional[str]:
    """Check if user has access to conversation. Returns access_type or None."""
    conv = await get_conversation(db, conversation_id)
    if not conv:
        return None
    
    # Handle dict from MongoDB
    is_confidential = conv.get('is_confidential') if isinstance(conv, dict) else conv.is_confidential
    is_restricted = conv.get('is_restricted') if isinstance(conv, dict) else conv.is_restricted
    access_level = conv.get('access_level') if isinstance(conv, dict) else conv.access_level
    privileged_users = conv.get('privileged_users') if isinstance(conv, dict) else conv.privileged_users
    created_by = conv.get('created_by') if isinstance(conv, dict) else conv.created_by
    
    # Public conversations (not confidential, not restricted) - everyone has access
    if is_confidential != 'true' and is_restricted != 'true':
        if not access_level or access_level == 'PUBLIC' or access_level == 'public':
            return 'read'
    
    # For confidential or restricted conversations, check explicit access
    # Check explicit access grants first (from Postgres)
    result = await db.execute(
        select(ConversationAccess)
        .where(ConversationAccess.conversation_id == conversation_id)
        .where(ConversationAccess.user_id == user_id)
    )
    access = result.scalar_one_or_none()
    if access:
        return access.access_type.value
    
    # Check if user is in privileged_users list
    if privileged_users and user_id in privileged_users:
        return 'read'
    
    # Check if user created the conversation (creator always has access)
    if created_by and created_by == user_id:
        return 'admin'
    
    # No access for confidential/restricted conversations without explicit grant
    return None


# Role-Based Access Control Functions
async def check_user_has_site_access(
    db: AsyncSession,
    user_id: str,
    site_id: UUID
) -> bool:
    """
    Check if user has access to a site based on their role assignments.
    
    Rules:
    - CRA: Has access if assigned to this specific site
    - Study Manager: Has access if assigned to this site (site-level access)
    - Medical Monitor: Has access if assigned to this specific site
    """
    assignments = await UserRoleAssignmentRepository.list_by_user(db, user_id)
    
    for assignment in assignments:
        if assignment.role in [UserRole.CRA, UserRole.STUDY_MANAGER, UserRole.MEDICAL_MONITOR]:
            # If assigned to this specific site
            if assignment.site_id == site_id:
                return True
    
    return False


async def check_user_has_study_access(
    db: AsyncSession,
    user_id: str,
    study_id: UUID
) -> bool:
    """
    Check if user has access to a study based on their role assignments.
    
    Rules:
    - CRA: Has access if assigned to this specific study
    - Study Manager: Has access if assigned to any site that belongs to this study
    - Medical Monitor: Has access if assigned to this specific study
    """
    assignments = await UserRoleAssignmentRepository.list_by_user(db, user_id)
    
    for assignment in assignments:
        if assignment.role == UserRole.CRA or assignment.role == UserRole.MEDICAL_MONITOR:
            # CRA and Medical Monitor: direct study assignment
            if assignment.study_id == study_id:
                return True
        
        elif assignment.role == UserRole.STUDY_MANAGER:
            # Study Manager: site-level access - check if site belongs to study via StudySite mapping
            if assignment.site_id:
                study_site_result = await db.execute(
                    select(StudySite).where(
                        StudySite.site_id == assignment.site_id,
                        StudySite.study_id == study_id,
                    )
                )
                study_site = study_site_result.scalar_one_or_none()
                if study_site:
                    return True
    
    return False


async def get_user_accessible_sites(
    db: AsyncSession,
    user_id: str
) -> List[Site]:
    """
    Get all sites that a user has access to based on their role assignments.
    
    Returns list of Site objects the user can access.
    """
    assignments = await UserRoleAssignmentRepository.list_by_user(db, user_id)
    accessible_site_ids = set()
    
    for assignment in assignments:
        if assignment.role in [UserRole.CRA, UserRole.STUDY_MANAGER, UserRole.MEDICAL_MONITOR]:
            if assignment.site_id:
                accessible_site_ids.add(assignment.site_id)
    
    if not accessible_site_ids:
        return []
    
    # Fetch all accessible sites
    sites = []
    for site_id in accessible_site_ids:
        result = await db.execute(select(Site).where(Site.id == site_id))
        site = result.scalar_one_or_none()
        if site:
            sites.append(site)
    
    return sites


async def get_user_accessible_studies(
    db: AsyncSession,
    user_id: str
) -> List[Study]:
    """
    Get all studies that a user has access to based on their role assignments.
    
    Rules:
    - CRA/Medical Monitor: Studies directly assigned
    - Study Manager: All studies in sites they have access to
    """
    assignments = await UserRoleAssignmentRepository.list_by_user(db, user_id)
    accessible_study_ids = set()
    accessible_site_ids = set()
    
    for assignment in assignments:
        if assignment.role == UserRole.CRA or assignment.role == UserRole.MEDICAL_MONITOR:
            # Direct study assignment
            if assignment.study_id:
                accessible_study_ids.add(assignment.study_id)
            # Direct site assignment (for site-level access)
            if assignment.site_id:
                accessible_site_ids.add(assignment.site_id)
        
        elif assignment.role == UserRole.STUDY_MANAGER:
            # Site-level access - get all studies in these sites
            if assignment.site_id:
                accessible_site_ids.add(assignment.site_id)
    
    # For sites, get their associated studies
    if accessible_site_ids:
        # Resolve studies via StudySite mappings instead of deprecated sites.study_id
        result = await db.execute(
            select(StudySite.study_id).where(StudySite.site_id.in_(accessible_site_ids))
        )
        for row in result.all():
            study_id = row[0]
            if study_id:
                accessible_study_ids.add(study_id)
    
    if not accessible_study_ids:
        return []
    
    # Fetch all accessible studies
    studies = []
    for study_id in accessible_study_ids:
        result = await db.execute(select(Study).where(Study.id == study_id))
        study = result.scalar_one_or_none()
        if study:
            studies.append(study)
    
    return studies


async def check_user_can_access_conversation_by_role(
    db: AsyncSession,
    user_id: str,
    conversation: Dict[str, Any]
) -> bool:
    """
    Check if user can access a conversation based on role-based site/study access.
    
    This checks if the conversation's site_id or study_id matches the user's role assignments.
    """
    conv_site_id = conversation.get('site_id')
    conv_study_id = conversation.get('study_id')
    
    if not conv_site_id and not conv_study_id:
        # Conversation not associated with site/study - use default access rules
        return False
    
    # Check site access
    if conv_site_id:
        # Try to get site by site_id (external identifier)
        site = await SiteRepository.get_by_site_id(db, conv_site_id)
        if site:
            if await check_user_has_site_access(db, user_id, site.id):
                return True
    
    # Check study access
    if conv_study_id:
        # Try to get study by study_id (external identifier)
        study = await StudyRepository.get_by_study_id(db, conv_study_id)
        if study:
            if await check_user_has_study_access(db, user_id, study.id):
                return True
    
    return False


# Attachment CRUD Functions
async def create_attachment(
    db: AsyncSession,
    conversation_id: UUID,
    file_path: str,
    content_type: str,
    size: int,
    message_id: Optional[UUID] = None,
    checksum: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new attachment record in MongoDB. Returns dict for compatibility."""
    att_data = {
        'id': uuid.uuid4(),
        'conversation_id': conversation_id,
        'message_id': message_id,
        'file_path': file_path,
        'content_type': content_type,
        'size': size,
        'checksum': checksum
    }
    return await AttachmentRepository.create(att_data)


async def get_attachment(db: AsyncSession, attachment_id: UUID) -> Optional[Dict[str, Any]]:
    """Get an attachment by ID from MongoDB. Returns dict for compatibility."""
    return await AttachmentRepository.get_by_id(attachment_id)


async def list_conversation_attachments(
    db: AsyncSession,
    conversation_id: UUID
) -> List[Dict[str, Any]]:
    """List all attachments for a conversation from MongoDB. Returns list of dicts for compatibility."""
    return await AttachmentRepository.list_by_conversation(conversation_id)


async def list_thread_attachments(
    db: AsyncSession,
    thread_id: UUID
) -> List[Dict[str, Any]]:
    """List all attachments for a thread from MongoDB. Returns list of dicts for compatibility."""
    return await ThreadAttachmentRepository.list_by_thread(thread_id)


async def create_thread_attachment(
    db: AsyncSession,
    thread_id: UUID,
    attachment_id: UUID,
    thread_message_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Link an attachment to a thread in MongoDB. Returns dict for compatibility."""
    att_data = {
        'id': uuid.uuid4(),
        'thread_id': thread_id,
        'attachment_id': attachment_id,
        'thread_message_id': thread_message_id
    }
    return await ThreadAttachmentRepository.create(att_data)


async def link_conversation_attachments_to_thread(
    db: AsyncSession,
    thread_id: UUID,
    conversation_id: UUID,
    message_ids: List[UUID]
) -> List[Dict[str, Any]]:
    """Link conversation attachments to a thread when creating thread from conversation. Uses MongoDB."""
    # Get attachments from MongoDB
    all_attachments = await AttachmentRepository.list_by_conversation(conversation_id)
    
    # Filter attachments that belong to the selected messages or are conversation-level
    filtered_attachments = []
    message_id_strs = {str(mid) for mid in message_ids}
    for att in all_attachments:
        att_msg_id = att.get('message_id')
        if att_msg_id and str(att_msg_id) in message_id_strs:
            filtered_attachments.append(att)
        elif not att_msg_id:  # Conversation-level attachment
            filtered_attachments.append(att)
    
    # Create thread attachment links in MongoDB
    thread_attachments = []
    seen_attachment_ids = set()
    for attachment in filtered_attachments:
        att_id = attachment.get('id')
        if att_id and att_id not in seen_attachment_ids:
            att_data = {
                'id': uuid.uuid4(),
                'thread_id': thread_id,
                'attachment_id': att_id,
                'thread_message_id': None  # Can be linked later if needed
            }
            thread_att = await ThreadAttachmentRepository.create(att_data)
            thread_attachments.append(thread_att)
            seen_attachment_ids.add(att_id)
    
    return thread_attachments


# User Profile CRUD Functions
async def create_rd_study(db: AsyncSession, user_id: str, study: RDStudyCreate) -> RDStudy:
    """Create a new R&D study for a user."""
    study_dict = study.dict()
    study_dict['user_id'] = user_id
    db_study = RDStudy(**study_dict)
    db.add(db_study)
    await db.commit()
    await db.refresh(db_study)
    return db_study


async def get_rd_studies(db: AsyncSession, user_id: str) -> List[RDStudy]:
    """Get all R&D studies for a user."""
    result = await db.execute(
        select(RDStudy)
        .where(RDStudy.user_id == user_id)
        .order_by(RDStudy.created_at.desc())
    )
    return list(result.scalars().all())


async def update_rd_study(db: AsyncSession, study_id: UUID, user_id: str, study: RDStudyCreate) -> Optional[RDStudy]:
    """Update an R&D study."""
    result = await db.execute(
        select(RDStudy)
        .where(RDStudy.id == study_id)
        .where(RDStudy.user_id == user_id)
    )
    db_study = result.scalar_one_or_none()
    if not db_study:
        return None
    
    study_dict = study.dict(exclude_unset=True)
    for key, value in study_dict.items():
        setattr(db_study, key, value)
    
    await db.commit()
    await db.refresh(db_study)
    return db_study


async def delete_rd_study(db: AsyncSession, study_id: UUID, user_id: str) -> bool:
    """Delete an R&D study."""
    result = await db.execute(
        select(RDStudy)
        .where(RDStudy.id == study_id)
        .where(RDStudy.user_id == user_id)
    )
    db_study = result.scalar_one_or_none()
    if not db_study:
        return False
    
    await db.delete(db_study)
    await db.commit()
    return True


async def create_iis_study(db: AsyncSession, user_id: str, study: IISStudyCreate) -> IISStudy:
    """Create a new IIS study for a user."""
    study_dict = study.dict()
    study_dict['user_id'] = user_id
    db_study = IISStudy(**study_dict)
    db.add(db_study)
    await db.commit()
    await db.refresh(db_study)
    return db_study


async def get_iis_studies(db: AsyncSession, user_id: str) -> List[IISStudy]:
    """Get all IIS studies for a user."""
    result = await db.execute(
        select(IISStudy)
        .where(IISStudy.user_id == user_id)
        .order_by(IISStudy.created_at.desc())
    )
    return list(result.scalars().all())


async def update_iis_study(db: AsyncSession, study_id: UUID, user_id: str, study: IISStudyCreate) -> Optional[IISStudy]:
    """Update an IIS study."""
    result = await db.execute(
        select(IISStudy)
        .where(IISStudy.id == study_id)
        .where(IISStudy.user_id == user_id)
    )
    db_study = result.scalar_one_or_none()
    if not db_study:
        return None
    
    study_dict = study.dict(exclude_unset=True)
    for key, value in study_dict.items():
        setattr(db_study, key, value)
    
    await db.commit()
    await db.refresh(db_study)
    return db_study


async def delete_iis_study(db: AsyncSession, study_id: UUID, user_id: str) -> bool:
    """Delete an IIS study."""
    result = await db.execute(
        select(IISStudy)
        .where(IISStudy.id == study_id)
        .where(IISStudy.user_id == user_id)
    )
    db_study = result.scalar_one_or_none()
    if not db_study:
        return False
    
    await db.delete(db_study)
    await db.commit()
    return True


async def create_event(db: AsyncSession, user_id: str, event: EventCreate) -> Event:
    """Create a new event for a user."""
    event_dict = event.dict()
    event_dict['user_id'] = user_id
    db_event = Event(**event_dict)
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


async def get_events(db: AsyncSession, user_id: str) -> List[Event]:
    """Get all events for a user."""
    result = await db.execute(
        select(Event)
        .where(Event.user_id == user_id)
        .order_by(Event.date_of_event.desc().nullslast(), Event.created_at.desc())
    )
    return list(result.scalars().all())


async def update_event(db: AsyncSession, event_id: UUID, user_id: str, event: EventCreate) -> Optional[Event]:
    """Update an event."""
    result = await db.execute(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.user_id == user_id)
    )
    db_event = result.scalar_one_or_none()
    if not db_event:
        return None
    
    event_dict = event.dict(exclude_unset=True)
    for key, value in event_dict.items():
        setattr(db_event, key, value)
    
    await db.commit()
    await db.refresh(db_event)
    return db_event


async def delete_event(db: AsyncSession, event_id: UUID, user_id: str) -> bool:
    """Delete an event."""
    result = await db.execute(
        select(Event)
        .where(Event.id == event_id)
        .where(Event.user_id == user_id)
    )
    db_event = result.scalar_one_or_none()
    if not db_event:
        return False
    
    await db.delete(db_event)
    await db.commit()
    return True


async def get_user_profile(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
    """Get user profile."""
    result = await db.execute(
        select(UserProfile)
        .where(UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_user_profile(db: AsyncSession, user_id: str, profile: UserProfileCreate) -> UserProfile:
    """Create or update user profile."""
    existing = await get_user_profile(db, user_id)
    
    if existing:
        profile_dict = profile.dict(exclude_unset=True)
        for key, value in profile_dict.items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        profile_dict = profile.dict()
        profile_dict['user_id'] = user_id
        db_profile = UserProfile(**profile_dict)
        db.add(db_profile)
        await db.commit()
        await db.refresh(db_profile)
        return db_profile


# Chat CRUD Functions
async def create_chat_message(db: AsyncSession, user_id: str, message: ChatMessageCreate) -> ChatMessage:
    """Create a new chat message for a user."""
    message_dict = message.dict()
    message_dict['user_id'] = user_id
    db_message = ChatMessage(**message_dict)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_chat_messages(db: AsyncSession, user_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
    """Get chat messages for a user."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def create_chat_document(db: AsyncSession, user_id: str, file_path: str, filename: str, content_type: str, size: int) -> ChatDocument:
    """Create a new chat document for a user."""
    db_document = ChatDocument(
        user_id=user_id,
        file_path=file_path,
        filename=filename,
        content_type=content_type,
        size=size
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    return db_document


async def get_chat_document(db: AsyncSession, document_id: UUID, user_id: str) -> Optional[ChatDocument]:
    """Get a chat document by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(ChatDocument)
        .where(ChatDocument.id == document_id)
        .where(ChatDocument.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_chat_documents(db: AsyncSession, user_id: str) -> List[ChatDocument]:
    """Get all chat documents for a user."""
    result = await db.execute(
        select(ChatDocument)
        .where(ChatDocument.user_id == user_id)
        .order_by(ChatDocument.uploaded_at.desc())
    )
    return list(result.scalars().all())


async def delete_chat_document(db: AsyncSession, document_id: UUID, user_id: str) -> bool:
    """Delete a chat document, ensuring it belongs to the user."""
    result = await db.execute(
        select(ChatDocument)
        .where(ChatDocument.id == document_id)
        .where(ChatDocument.user_id == user_id)
    )
    db_document = result.scalar_one_or_none()
    if not db_document:
        return False
    
    # Delete the file from disk
    try:
        import os
        if os.path.exists(db_document.file_path):
            os.remove(db_document.file_path)
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    await db.delete(db_document)
    await db.commit()
    return True


async def combine_threads(
    db: AsyncSession,
    thread1_id: UUID,
    thread2_id: UUID,
    target_thread_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Combine two threads into one. Merges participants, messages, and attachments.
    The target_thread_id is the thread that will be kept (the other will be deleted).
    Returns the combined thread.
    """
    # Verify both threads exist
    thread1 = await ThreadRepository.get_by_id(thread1_id)
    thread2 = await ThreadRepository.get_by_id(thread2_id)
    
    if not thread1 or not thread2:
        raise ValueError("One or both threads not found")
    
    # Ensure target_thread_id is one of the two threads
    if target_thread_id not in [thread1_id, thread2_id]:
        raise ValueError("target_thread_id must be either thread1_id or thread2_id")
    
    source_thread_id = thread2_id if target_thread_id == thread1_id else thread1_id
    target_thread = thread1 if target_thread_id == thread1_id else thread2
    source_thread = thread2 if target_thread_id == thread1_id else thread1
    
    # Get all participants from both threads
    target_participants = await ThreadParticipantRepository.list_by_thread(target_thread_id)
    source_participants = await ThreadParticipantRepository.list_by_thread(source_thread_id)
    
    # Merge participants (avoid duplicates)
    existing_participant_ids = {p.get('participant_id') for p in target_participants}
    for participant in source_participants:
        participant_id = participant.get('participant_id')
        if participant_id and participant_id not in existing_participant_ids:
            # Add participant to target thread
            participant_data = {
                'id': uuid.uuid4(),
                'thread_id': target_thread_id,
                'participant_id': participant.get('participant_id'),
                'participant_name': participant.get('participant_name'),
                'participant_email': participant.get('participant_email'),
                'role': participant.get('role', 'participant')
            }
            await ThreadParticipantRepository.create(participant_data)
            existing_participant_ids.add(participant_id)
    
    # Get all messages from source thread
    source_messages = await ThreadMessageRepository.list_by_thread(source_thread_id, limit=1000, offset=0)
    
    # Move messages to target thread and track original thread
    for msg in source_messages:
        # Update message to point to target thread and preserve original thread info
        await ThreadMessageRepository.update_fields(
            msg.get('id'),
            {
                'thread_id': str(target_thread_id),
                'original_thread_id': str(source_thread_id),  # Track which thread this message came from
                'merged_at': datetime.now(timezone.utc).isoformat()  # Track when it was merged
            }
        )
    
    # Get all attachments from source thread
    source_attachments = await ThreadAttachmentRepository.list_by_thread(source_thread_id)
    
    # Move attachments to target thread
    for att in source_attachments:
        # Update attachment to point to target thread
        await ThreadAttachmentRepository.update_fields(
            att.get('id'),
            {'thread_id': str(target_thread_id)}
        )
    
    # Update target thread metadata (merge titles, descriptions, etc.)
    updates = {
        'updated_at': datetime.now(timezone.utc)
    }
    
    # Merge titles if different
    if target_thread.get('title') != source_thread.get('title'):
        updates['title'] = f"{target_thread.get('title')} / {source_thread.get('title')}"
    
    # Merge descriptions if both exist
    target_desc = target_thread.get('description')
    source_desc = source_thread.get('description')
    if target_desc and source_desc and target_desc != source_desc:
        updates['description'] = f"{target_desc}\n\n--- Merged from: {source_thread.get('title')} ---\n{source_desc}"
    elif source_desc and not target_desc:
        updates['description'] = source_desc
    
    # Use the most urgent priority
    priorities = ['urgent', 'high', 'medium', 'low']
    target_priority = target_thread.get('priority', 'medium')
    source_priority = source_thread.get('priority', 'medium')
    if priorities.index(source_priority) < priorities.index(target_priority):
        updates['priority'] = source_priority
    
    # Update target thread
    await ThreadRepository.update(target_thread_id, updates)
    
    # Delete source thread (this will cascade delete ThreadFromConversation links)
    # Note: We keep the messages and attachments, just move them
    await ThreadRepository.delete(source_thread_id)
    
    # Return updated target thread
    return await ThreadRepository.get_by_id(target_thread_id)

