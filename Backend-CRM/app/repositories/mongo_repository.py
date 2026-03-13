"""
MongoDB repository base class and implementations for conversation/message data.
This module contains repositories for MongoDB-backed entities.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
import re
from datetime import datetime, timezone
from bson import ObjectId
from pymongo import DESCENDING
from app.db_mongo import get_mongo_db
from app.models import MessageDirection, MessageChannel, MessageStatus
import logging

logger = logging.getLogger(__name__)


def uuid_to_str(uuid_val: UUID) -> str:
    """Convert UUID to string for MongoDB storage."""
    return str(uuid_val) if uuid_val else None


def str_to_uuid(str_val: str) -> Optional[UUID]:
    """Convert string to UUID."""
    try:
        return UUID(str_val) if str_val else None
    except (ValueError, AttributeError):
        return None


class ConversationRepository:
    """Repository for Conversation documents in MongoDB."""
    
    COLLECTION_NAME = "conversations"
    
    @staticmethod
    async def create(conv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new conversation."""
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        
        # Convert UUID to string
        if 'id' in conv_data and isinstance(conv_data['id'], UUID):
            conv_data['id'] = str(conv_data['id'])
        
        # Set timestamps
        now = datetime.now(timezone.utc)
        conv_data['created_at'] = now
        conv_data['updated_at'] = now
        
        # Ensure string fields for boolean-like values
        if 'is_restricted' in conv_data:
            conv_data['is_restricted'] = 'true' if conv_data['is_restricted'] else 'false'
        if 'is_confidential' in conv_data:
            conv_data['is_confidential'] = 'true' if conv_data['is_confidential'] else 'false'
        if 'is_pinned' in conv_data:
            conv_data['is_pinned'] = 'true' if conv_data['is_pinned'] else 'false'
        if 'access_level' not in conv_data:
            conv_data['access_level'] = 'PUBLIC'
        if 'privileged_users' not in conv_data:
            conv_data['privileged_users'] = []
        if 'conversation_type' not in conv_data or not conv_data.get('conversation_type'):
            conv_data['conversation_type'] = 'notice_board'
        if 'is_pinned' not in conv_data:
            conv_data['is_pinned'] = 'false'
        
        result = await collection.insert_one(conv_data)
        logger.info(f"[MONGO] Created conversation: {conv_data.get('id', result.inserted_id)}")
        
        # Return the created document
        created = await collection.find_one({"_id": result.inserted_id})
        return ConversationRepository._normalize_doc(created)
    
    @staticmethod
    async def get_by_id(conv_id: UUID) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"id": str(conv_id)})
        return ConversationRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def get_by_tracker_code(tracker_code: str) -> Optional[Dict[str, Any]]:
        """Get conversation by tracker code."""
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"tracker_code": tracker_code})
        return ConversationRepository._normalize_doc(doc) if doc else None

    @staticmethod
    async def get_pinned_notice_board(site_id: str, study_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get pinned notice board conversation for a site and study (study-specific)."""
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        query = {
            "site_id": site_id,
            "conversation_type": "notice_board",
            "is_pinned": {"$in": ["true", True]},
        }
        if study_id:
            query["study_id"] = study_id
        else:
            # If no study_id, only match conversations with no study_id (site-level only)
            query["$or"] = [{"study_id": None}, {"study_id": {"$exists": False}}]
        doc = await collection.find_one(query)
        return ConversationRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list(
        limit: int = 50,
        offset: int = 0,
        study_id: Optional[str] = None,
        site_id: Optional[str] = None,
        channel: Optional[MessageChannel] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List conversations with filters.

        Conversations are public notice-board items and are not user-filtered.
        """
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        
        query = {}
        if site_id:
            query['site_id'] = site_id
        query['conversation_type'] = 'notice_board'
        if study_id:
            # Conversations are study-specific. Only show notice boards for this study.
            query["study_id"] = study_id
        else:
            # If no study_id filter, only show site-level conversations (no study_id)
            query["$or"] = [{"study_id": None}, {"study_id": {"$exists": False}}]
        
        # Note: Channel filtering requires joining with messages, handled separately
        # Get all matching docs first (don't limit yet - we need to sort properly)
        cursor = collection.find(query)
        all_docs = await cursor.to_list(length=None)  # Get all matching docs
        
        # Normalize all docs
        normalized_docs = [ConversationRepository._normalize_doc(d) for d in all_docs]
        
        # CRITICAL: Sort pinned items FIRST, then by created_at descending
        # This ensures Public Notice Board (pinned) always appears at top
        def sort_key(x):
            is_pinned_val = str(x.get('is_pinned', 'false')).lower().strip()
            is_pinned = (is_pinned_val == 'true' or is_pinned_val == '1' or is_pinned_val == 'yes' or is_pinned_val == 't')
            created_at = x.get('created_at')
            # Convert created_at to timestamp for comparison
            if isinstance(created_at, datetime):
                created_at_ts = created_at.timestamp()
            elif hasattr(created_at, 'timestamp'):
                created_at_ts = created_at.timestamp()
            elif isinstance(created_at, str):
                try:
                    created_at_ts = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
                except:
                    try:
                        from dateutil import parser
                        created_at_ts = parser.parse(created_at).timestamp()
                    except:
                        created_at_ts = 0
            else:
                created_at_ts = 0
            # Return: (0 for pinned, 1 for not pinned), then negative timestamp (newer first)
            return (0 if is_pinned else 1, -created_at_ts)
        
        # Sort: pinned items first, then by date descending
        normalized_docs.sort(key=sort_key)
        
        # Debug: Log first few items to verify sorting
        if normalized_docs:
            print(f"[SORT DEBUG] After Python sort, first {min(3, len(normalized_docs))} conversations:")
            for i, doc in enumerate(normalized_docs[:3]):
                is_pinned_raw = doc.get('is_pinned', 'false')
                is_pinned_val = str(is_pinned_raw).lower().strip()
                is_pinned_bool = (is_pinned_val == 'true' or is_pinned_val == '1' or is_pinned_val == 'yes' or is_pinned_val == 't')
                title = doc.get('title') or doc.get('subject') or 'NO_TITLE'
                created_at = doc.get('created_at')
                print(f"  [{i}] is_pinned_raw={repr(is_pinned_raw)}, is_pinned_val={repr(is_pinned_val)}, is_pinned_bool={is_pinned_bool}, title={title}, created_at={created_at}")
                logger.info(f"[SORT] [{i}] is_pinned={repr(is_pinned_raw)}, title={title}")
        
        # Apply pagination AFTER sorting
        paginated_docs = normalized_docs[offset:offset + limit]
        
        return paginated_docs
    
    @staticmethod
    async def update(conv_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update conversation."""
        db = await get_mongo_db()
        collection = db[ConversationRepository.COLLECTION_NAME]
        
        updates['updated_at'] = datetime.now(timezone.utc)
        
        result = await collection.update_one(
            {"id": str(conv_id)},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(conv_id)})
            return ConversationRepository._normalize_doc(doc) if doc else None
        return None
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document (remove _id, convert id to UUID)."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        if 'id' in normalized and isinstance(normalized['id'], str):
            try:
                normalized['id'] = UUID(normalized['id'])
            except ValueError:
                pass
        # Ensure optional fields required by Pydantic schema are present
        if 'participant_phone' not in normalized:
            normalized['participant_phone'] = None
        if 'participant_email' not in normalized:
            normalized['participant_email'] = None
        # Ensure participant_emails is always an array (default to empty array)
        if 'participant_emails' not in normalized:
            normalized['participant_emails'] = []
        elif normalized.get('participant_emails') is None:
            normalized['participant_emails'] = []
        elif not isinstance(normalized.get('participant_emails'), list):
            # Convert to list if it's not already
            normalized['participant_emails'] = [normalized['participant_emails']] if normalized['participant_emails'] else []
        if 'subject' not in normalized:
            normalized['subject'] = None
        if 'title' not in normalized:
            normalized['title'] = None
        if 'conversation_type' not in normalized:
            normalized['conversation_type'] = 'notice_board'
        # CRITICAL: Normalize is_pinned - handle both string and boolean values from MongoDB
        # ONLY Public Notice Board should be pinned - fix any incorrect data
        if 'is_pinned' not in normalized:
            normalized['is_pinned'] = 'false'
        else:
            # Convert any truthy/falsy value to proper string
            is_pinned_val = normalized.get('is_pinned')
            if isinstance(is_pinned_val, bool):
                normalized['is_pinned'] = 'true' if is_pinned_val else 'false'
            elif isinstance(is_pinned_val, str):
                # Already a string, just ensure it's lowercase
                normalized['is_pinned'] = is_pinned_val.lower().strip()
            else:
                # Handle other types (int, None, etc.)
                normalized['is_pinned'] = 'true' if is_pinned_val else 'false'
        
        # CRITICAL FIX: Only Public Notice Board should be pinned
        # If it's not the notice board, force is_pinned to 'false'
        title = normalized.get('title') or normalized.get('subject') or ''
        is_notice_board = (
            normalized.get('conversation_type') == 'notice_board' and
            (title == 'Public Notice Board' or normalized.get('created_by') == 'system')
        )
        if not is_notice_board:
            normalized['is_pinned'] = 'false'
        if 'tracker_code' not in normalized:
            normalized['tracker_code'] = None
        # AI fields – ensure keys exist so frontend can rely on optional props
        for key in ['ai_category', 'ai_priority', 'ai_sentiment', 'ai_next_best_action']:
            normalized.setdefault(key, None)
        if 'ai_summary' not in normalized:
            normalized['ai_summary'] = None
        if 'ai_summary_updated_at' not in normalized:
            normalized['ai_summary_updated_at'] = None
        return normalized


class MessageRepository:
    """Repository for Message documents in MongoDB."""
    
    COLLECTION_NAME = "messages"
    
    @staticmethod
    async def create(msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message."""
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        
        # Convert UUIDs to strings (always use lowercase for consistency)
        if 'id' in msg_data and isinstance(msg_data['id'], UUID):
            msg_data['id'] = str(msg_data['id']).lower()
        if 'conversation_id' in msg_data and isinstance(msg_data['conversation_id'], UUID):
            msg_data['conversation_id'] = str(msg_data['conversation_id']).lower()
        elif 'conversation_id' in msg_data and isinstance(msg_data['conversation_id'], str):
            msg_data['conversation_id'] = msg_data['conversation_id'].lower()
        
        # Set timestamp
        if 'created_at' not in msg_data:
            msg_data['created_at'] = datetime.now(timezone.utc)
        
        # Convert enums to strings
        if 'direction' in msg_data and hasattr(msg_data['direction'], 'value'):
            msg_data['direction'] = msg_data['direction'].value
        if 'channel' in msg_data and hasattr(msg_data['channel'], 'value'):
            msg_data['channel'] = msg_data['channel'].value
        if 'status' in msg_data and hasattr(msg_data['status'], 'value'):
            msg_data['status'] = msg_data['status'].value
        
        result = await collection.insert_one(msg_data)
        created = await collection.find_one({"_id": result.inserted_id})
        return MessageRepository._normalize_doc(created)
    
    @staticmethod
    async def get_by_id(msg_id: UUID) -> Optional[Dict[str, Any]]:
        """Get message by ID. Uses case-insensitive matching for production compatibility."""
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        
        # Use case-insensitive regex to handle both new (lowercase) and legacy (any case) data
        msg_id_str = str(msg_id)
        escaped_id = re.escape(msg_id_str)
        doc = await collection.find_one({
            "id": {"$regex": f"^{escaped_id}$", "$options": "i"}
        })
        return MessageRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def get_by_provider_message_id(provider_message_id: str) -> Optional[Dict[str, Any]]:
        """Get message by provider_message_id."""
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"provider_message_id": provider_message_id})
        return MessageRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list_by_conversation(
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List messages for a conversation, sorted by created_at descending (latest first).
        
        Uses case-insensitive matching to handle both new (lowercase) and legacy (any case) data.
        """
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        
        # Use case-insensitive regex to match any case variation (production-safe)
        conv_id_str = str(conversation_id)
        escaped_id = re.escape(conv_id_str)
        
        # Query with case-insensitive regex to handle both new (lowercase) and legacy (any case) data
        cursor = collection.find({
            "conversation_id": {"$regex": f"^{escaped_id}$", "$options": "i"}
        })\
            .sort("created_at", DESCENDING)\
            .skip(offset)\
            .limit(limit)
        
        docs = await cursor.to_list(length=limit)
        normalized = [MessageRepository._normalize_doc(d) for d in docs]
        return normalized
    
    @staticmethod
    async def update_status(
        msg_id: UUID,
        status: MessageStatus,
        provider_message_id: Optional[str] = None,
        sent_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Update message status."""
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        
        updates = {
            "status": status.value if hasattr(status, 'value') else str(status),
            "updated_at": datetime.now(timezone.utc)
        }
        if provider_message_id:
            updates["provider_message_id"] = provider_message_id
        if sent_at:
            updates["sent_at"] = sent_at
        if delivered_at:
            updates["delivered_at"] = delivered_at
        
        result = await collection.update_one(
            {"id": str(msg_id)},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(msg_id)})
            return MessageRepository._normalize_doc(doc) if doc else None
        return None
    
    @staticmethod
    async def update_fields(msg_id: UUID, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generic helper to update arbitrary fields on a message document."""
        db = await get_mongo_db()
        collection = db[MessageRepository.COLLECTION_NAME]
        fields = dict(fields or {})
        if not fields:
            return await MessageRepository.get_by_id(msg_id)

        result = await collection.update_one(
            {"id": str(msg_id)},
            {"$set": fields}
        )
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(msg_id)})
            return MessageRepository._normalize_doc(doc) if doc else None
        return None
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        # Convert id and conversation_id to UUID
        for field in ['id', 'conversation_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        # Map metadata field
        if 'message_metadata' in normalized:
            normalized['metadata'] = normalized.pop('message_metadata')
        if 'metadata' not in normalized:
            normalized['metadata'] = {}
        
        # Extract origin, event_type, and is_activity_event from metadata if not present as top-level fields
        metadata = normalized.get('metadata') or {}
        if 'origin' not in normalized and 'origin' in metadata:
            normalized['origin'] = metadata.get('origin')
        if 'event_type' not in normalized and 'event_type' in metadata:
            normalized['event_type'] = metadata.get('event_type')
        if 'is_activity_event' not in normalized and 'is_activity_event' in metadata:
            normalized['is_activity_event'] = metadata.get('is_activity_event')
        
        # Ensure optional fields required by Pydantic schema are present
        if 'provider_message_id' not in normalized:
            normalized['provider_message_id'] = None
        if 'author_id' not in normalized:
            normalized['author_id'] = None
        if 'author_name' not in normalized:
            normalized['author_name'] = None
        if 'sent_at' not in normalized:
            normalized['sent_at'] = None
        if 'delivered_at' not in normalized:
            normalized['delivered_at'] = None
        if 'mentioned_emails' not in normalized:
            normalized['mentioned_emails'] = []
        elif normalized.get('mentioned_emails') is None:
            normalized['mentioned_emails'] = []
        elif not isinstance(normalized.get('mentioned_emails'), list):
            normalized['mentioned_emails'] = []
        
        # Ensure origin, event_type, and is_activity_event are present (defaults for backward compatibility)
        if 'origin' not in normalized:
            normalized['origin'] = 'user'  # Default to "user" for existing messages
        if 'event_type' not in normalized:
            normalized['event_type'] = None
        if 'is_activity_event' not in normalized:
            # Default to False for existing messages (user messages)
            # If origin is "system", infer it might be an activity event, but default to False for safety
            normalized['is_activity_event'] = False
        
        return normalized


class AttachmentRepository:
    """Repository for Attachment documents in MongoDB."""
    
    COLLECTION_NAME = "attachments"
    
    @staticmethod
    async def create(att_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new attachment."""
        db = await get_mongo_db()
        collection = db[AttachmentRepository.COLLECTION_NAME]
        
        # Convert UUIDs to strings
        for field in ['id', 'message_id', 'conversation_id']:
            if field in att_data and isinstance(att_data[field], UUID):
                att_data[field] = str(att_data[field])
        
        if 'uploaded_at' not in att_data:
            att_data['uploaded_at'] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(att_data)
        logger.info(f"[MONGO] Created attachment: {att_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return AttachmentRepository._normalize_doc(created)
    
    @staticmethod
    async def get_by_id(att_id: UUID) -> Optional[Dict[str, Any]]:
        """Get attachment by ID."""
        db = await get_mongo_db()
        collection = db[AttachmentRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"id": str(att_id)})
        return AttachmentRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list_by_conversation(conversation_id: UUID) -> List[Dict[str, Any]]:
        """List attachments for a conversation."""
        db = await get_mongo_db()
        collection = db[AttachmentRepository.COLLECTION_NAME]
        
        cursor = collection.find({"conversation_id": str(conversation_id)})\
            .sort("uploaded_at", DESCENDING)
        
        docs = await cursor.to_list(length=None)
        return [AttachmentRepository._normalize_doc(d) for d in docs]
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        for field in ['id', 'message_id', 'conversation_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        return normalized


class ThreadRepository:
    """Repository for Thread documents in MongoDB."""
    
    COLLECTION_NAME = "threads"
    
    @staticmethod
    async def create(thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new thread."""
        db = await get_mongo_db()
        collection = db[ThreadRepository.COLLECTION_NAME]
        
        # Convert UUIDs to strings (conversation_id can be None)
        if 'id' in thread_data and isinstance(thread_data['id'], UUID):
            thread_data['id'] = str(thread_data['id'])
        if 'conversation_id' in thread_data and thread_data['conversation_id'] is not None and isinstance(thread_data['conversation_id'], UUID):
            thread_data['conversation_id'] = str(thread_data['conversation_id'])
        
        # Set timestamps
        now = datetime.now(timezone.utc)
        thread_data['created_at'] = now
        thread_data['updated_at'] = now
        
        result = await collection.insert_one(thread_data)
        logger.info(f"[MONGO] Created thread: {thread_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return ThreadRepository._normalize_doc(created)
    
    @staticmethod
    async def get_by_id(thread_id: UUID) -> Optional[Dict[str, Any]]:
        """Get thread by ID."""
        db = await get_mongo_db()
        collection = db[ThreadRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"id": str(thread_id)})
        return ThreadRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list(
        limit: int = 50,
        offset: int = 0,
        thread_type: Optional[str] = None,
        status: Optional[str] = None,
        participant_id: Optional[str] = None,
        study_id: Optional[str] = None,
        site_id: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List threads with filters. NEW: Returns threads if visibility_scope='site' OR user_email in participants_emails."""
        db = await get_mongo_db()
        collection = db[ThreadRepository.COLLECTION_NAME]
        
        # Build base query filters
        base_filters = {}
        if thread_type:
            base_filters['thread_type'] = thread_type
        if status:
            base_filters['status'] = status
        # CRITICAL: Both study_id and site_id must match (AND condition)
        if study_id:
            base_filters['related_study_id'] = study_id
        if site_id:
            base_filters['site_id'] = site_id
        
        # NEW VISIBILITY LOGIC: Return thread if visibility_scope='site' OR user_email in participants_emails
        if user_email:
            normalized_email = str(user_email).strip().lower()
            # Build OR condition: site-wide threads OR user is a participant
            visibility_conditions = [
                {'visibility_scope': 'site'},  # Site-wide visible threads
                {'participants_emails': {'$in': [normalized_email]}}  # User is a participant
            ]
            # Combine base filters with visibility conditions
            query = {
                '$and': [
                    base_filters,
                    {'$or': visibility_conditions}
                ]
            } if base_filters else {'$or': visibility_conditions}
        else:
            # If no user_email, only return site-wide threads
            base_filters['visibility_scope'] = 'site'
            query = base_filters
        
        cursor = collection.find(query).sort("updated_at", DESCENDING).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        return [ThreadRepository._normalize_doc(d) for d in docs]
    
    @staticmethod
    async def update(thread_id: UUID, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update thread."""
        db = await get_mongo_db()
        collection = db[ThreadRepository.COLLECTION_NAME]
        
        updates['updated_at'] = datetime.now(timezone.utc)
        
        result = await collection.update_one(
            {"id": str(thread_id)},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(thread_id)})
            return ThreadRepository._normalize_doc(doc) if doc else None
        return None
    
    @staticmethod
    async def delete(thread_id: UUID) -> bool:
        """Delete a thread."""
        db = await get_mongo_db()
        collection = db[ThreadRepository.COLLECTION_NAME]
        
        result = await collection.delete_one({"id": str(thread_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        # Convert id to UUID
        if 'id' in normalized and isinstance(normalized['id'], str):
            try:
                normalized['id'] = UUID(normalized['id'])
            except ValueError:
                pass
        # Convert conversation_id to UUID if present (it's optional)
        if 'conversation_id' in normalized and normalized['conversation_id'] is not None:
            if isinstance(normalized['conversation_id'], str):
                try:
                    normalized['conversation_id'] = UUID(normalized['conversation_id'])
                except ValueError:
                    pass
        # Ensure optional fields required by Pydantic schema are present
        if 'related_patient_id' not in normalized:
            normalized['related_patient_id'] = None
        if 'description' not in normalized:
            normalized['description'] = None
        # AI fields on threads
        if 'ai_summary' not in normalized:
            normalized['ai_summary'] = None
        if 'ai_summary_updated_at' not in normalized:
            normalized['ai_summary_updated_at'] = None
        # TMF filing fields
        if 'tmf_filed' not in normalized:
            normalized['tmf_filed'] = False
        if 'tmf_filed_at' not in normalized:
            normalized['tmf_filed_at'] = None
        if 'conversation_address' not in normalized:
            normalized['conversation_address'] = None
        # Agreement type field
        if 'agreement_type' not in normalized:
            normalized['agreement_type'] = None
        # Participants emails field
        if 'participants_emails' not in normalized:
            normalized['participants_emails'] = []
        elif normalized.get('participants_emails') is None:
            normalized['participants_emails'] = []
        elif not isinstance(normalized.get('participants_emails'), list):
            normalized['participants_emails'] = []
        # Visibility scope field (default to 'private' for backward compatibility)
        if 'visibility_scope' not in normalized:
            normalized['visibility_scope'] = 'private'
        elif normalized.get('visibility_scope') not in ['private', 'site']:
            normalized['visibility_scope'] = 'private'  # Default to private if invalid
        return normalized


class ThreadParticipantRepository:
    """Repository for ThreadParticipant documents in MongoDB."""
    
    COLLECTION_NAME = "thread_participants"
    
    @staticmethod
    async def create(participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new thread participant."""
        db = await get_mongo_db()
        collection = db[ThreadParticipantRepository.COLLECTION_NAME]
        
        if 'id' in participant_data and isinstance(participant_data['id'], UUID):
            participant_data['id'] = str(participant_data['id'])
        if 'thread_id' in participant_data and isinstance(participant_data['thread_id'], UUID):
            participant_data['thread_id'] = str(participant_data['thread_id'])
        
        if 'joined_at' not in participant_data:
            participant_data['joined_at'] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(participant_data)
        logger.info(f"[MONGO] Created thread participant: {participant_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return ThreadParticipantRepository._normalize_doc(created)
    
    @staticmethod
    async def list_by_thread(thread_id: UUID) -> List[Dict[str, Any]]:
        """List participants for a thread."""
        db = await get_mongo_db()
        collection = db[ThreadParticipantRepository.COLLECTION_NAME]
        
        cursor = collection.find({"thread_id": str(thread_id)})
        docs = await cursor.to_list(length=None)
        return [ThreadParticipantRepository._normalize_doc(d) for d in docs]
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        for field in ['id', 'thread_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        return normalized


class ThreadMessageRepository:
    """Repository for ThreadMessage documents in MongoDB."""
    
    COLLECTION_NAME = "thread_messages"
    
    @staticmethod
    async def create(msg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new thread message."""
        db = await get_mongo_db()
        collection = db[ThreadMessageRepository.COLLECTION_NAME]
        
        for field in ['id', 'thread_id', 'message_id']:
            if field in msg_data and isinstance(msg_data[field], UUID):
                msg_data[field] = str(msg_data[field])
        
        if 'created_at' not in msg_data:
            msg_data['created_at'] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(msg_data)
        logger.info(f"[MONGO] Created thread message: {msg_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return ThreadMessageRepository._normalize_doc(created)

    @staticmethod
    async def get_by_id(msg_id: UUID) -> Optional[Dict[str, Any]]:
        """Get thread message by ID."""
        db = await get_mongo_db()
        collection = db[ThreadMessageRepository.COLLECTION_NAME]
        doc = await collection.find_one({"id": str(msg_id)})
        return ThreadMessageRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list_by_thread(
        thread_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List messages for a thread, sorted by created_at descending (latest first)."""
        db = await get_mongo_db()
        collection = db[ThreadMessageRepository.COLLECTION_NAME]
        
        cursor = collection.find({"thread_id": str(thread_id)})\
            .sort("created_at", DESCENDING)\
            .skip(offset)\
            .limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [ThreadMessageRepository._normalize_doc(d) for d in docs]
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        for field in ['id', 'thread_id', 'message_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        # Ensure message_type field is present (defaults to None for regular messages)
        if 'message_type' not in normalized:
            normalized['message_type'] = None
        if 'mentioned_emails' not in normalized:
            normalized['mentioned_emails'] = []
        elif normalized.get('mentioned_emails') is None:
            normalized['mentioned_emails'] = []
        elif not isinstance(normalized.get('mentioned_emails'), list):
            normalized['mentioned_emails'] = []
        return normalized

    @staticmethod
    async def update_fields(msg_id: UUID, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generic helper to update arbitrary fields on a thread message document."""
        db = await get_mongo_db()
        collection = db[ThreadMessageRepository.COLLECTION_NAME]
        fields = dict(fields or {})
        if not fields:
            doc = await collection.find_one({"id": str(msg_id)})
            return ThreadMessageRepository._normalize_doc(doc) if doc else None

        result = await collection.update_one(
            {"id": str(msg_id)},
            {"$set": fields}
        )
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(msg_id)})
            return ThreadMessageRepository._normalize_doc(doc) if doc else None
        return None


class ThreadAttachmentRepository:
    """Repository for ThreadAttachment documents in MongoDB."""
    
    COLLECTION_NAME = "thread_attachments"
    
    @staticmethod
    async def create(att_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new thread attachment link."""
        db = await get_mongo_db()
        collection = db[ThreadAttachmentRepository.COLLECTION_NAME]
        
        for field in ['id', 'thread_id', 'thread_message_id', 'attachment_id']:
            if field in att_data and isinstance(att_data[field], UUID):
                att_data[field] = str(att_data[field])
        
        if 'created_at' not in att_data:
            att_data['created_at'] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(att_data)
        logger.info(f"[MONGO] Created thread attachment: {att_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return ThreadAttachmentRepository._normalize_doc(created)
    
    @staticmethod
    async def list_by_thread(thread_id: UUID) -> List[Dict[str, Any]]:
        """List attachments for a thread."""
        db = await get_mongo_db()
        collection = db[ThreadAttachmentRepository.COLLECTION_NAME]
        
        cursor = collection.find({"thread_id": str(thread_id)})\
            .sort("created_at", DESCENDING)
        
        docs = await cursor.to_list(length=None)
        return [ThreadAttachmentRepository._normalize_doc(d) for d in docs]
    
    @staticmethod
    async def update_fields(att_id: UUID, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fields on a thread attachment document."""
        db = await get_mongo_db()
        collection = db[ThreadAttachmentRepository.COLLECTION_NAME]
        fields = dict(fields or {})
        if not fields:
            doc = await collection.find_one({"id": str(att_id)})
            return ThreadAttachmentRepository._normalize_doc(doc) if doc else None

        result = await collection.update_one(
            {"id": str(att_id)},
            {"$set": fields}
        )
        if result.modified_count > 0:
            doc = await collection.find_one({"id": str(att_id)})
            return ThreadAttachmentRepository._normalize_doc(doc) if doc else None
        return None
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        for field in ['id', 'thread_id', 'thread_message_id', 'attachment_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        return normalized


class ThreadFromConversationRepository:
    """Repository for ThreadFromConversation documents in MongoDB."""
    
    COLLECTION_NAME = "thread_from_conversations"
    
    @staticmethod
    async def create(link_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new thread-from-conversation link."""
        db = await get_mongo_db()
        collection = db[ThreadFromConversationRepository.COLLECTION_NAME]
        
        for field in ['id', 'thread_id', 'conversation_id']:
            if field in link_data and isinstance(link_data[field], UUID):
                link_data[field] = str(link_data[field])
        
        if 'source_message_ids' in link_data:
            link_data['source_message_ids'] = [str(mid) if isinstance(mid, UUID) else mid for mid in link_data['source_message_ids']]
        
        if 'created_at' not in link_data:
            link_data['created_at'] = datetime.now(timezone.utc)
        
        result = await collection.insert_one(link_data)
        logger.info(f"[MONGO] Created thread-from-conversation link: {link_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return ThreadFromConversationRepository._normalize_doc(created)
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        for field in ['id', 'thread_id', 'conversation_id']:
            if field in normalized and isinstance(normalized[field], str):
                try:
                    normalized[field] = UUID(normalized[field])
                except ValueError:
                    pass
        return normalized


class TaskRepository:
    """Repository for Task documents in MongoDB."""
    
    COLLECTION_NAME = "tasks"
    
    @staticmethod
    async def create(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        db = await get_mongo_db()
        collection = db[TaskRepository.COLLECTION_NAME]
        
        # Ensure id is string
        if 'id' in task_data and isinstance(task_data['id'], UUID):
            task_data['id'] = str(task_data['id'])
        elif 'id' not in task_data:
            task_data['id'] = str(uuid.uuid4())
        
        # Set timestamps if not present
        now = datetime.now(timezone.utc)
        if 'createdAt' not in task_data:
            task_data['createdAt'] = now.isoformat()
        if 'updatedAt' not in task_data:
            task_data['updatedAt'] = now.isoformat()
        
        result = await collection.insert_one(task_data)
        logger.info(f"[MONGO] Created task: {task_data.get('id', result.inserted_id)}")
        
        created = await collection.find_one({"_id": result.inserted_id})
        return TaskRepository._normalize_doc(created)
    
    @staticmethod
    async def get_by_id(task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        db = await get_mongo_db()
        collection = db[TaskRepository.COLLECTION_NAME]
        
        doc = await collection.find_one({"id": task_id})
        return TaskRepository._normalize_doc(doc) if doc else None
    
    @staticmethod
    async def list(
        limit: int = 50,
        offset: int = 0,
        **filters
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        db = await get_mongo_db()
        collection = db[TaskRepository.COLLECTION_NAME]
        
        query = {}
        # Handle nested filters (e.g., links.conversationId)
        for key, value in filters.items():
            if value is not None:
                query[key] = value
        
        cursor = collection.find(query).sort("createdAt", DESCENDING).skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [TaskRepository._normalize_doc(doc) for doc in docs]
    
    @staticmethod
    async def update(task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        db = await get_mongo_db()
        collection = db[TaskRepository.COLLECTION_NAME]
        
        # Ensure updatedAt is set
        updates['updatedAt'] = datetime.now(timezone.utc).isoformat()
        
        result = await collection.update_one(
            {"id": task_id},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Task {task_id} not found")
        
        updated = await collection.find_one({"id": task_id})
        return TaskRepository._normalize_doc(updated)
    
    @staticmethod
    async def delete(task_id: str) -> bool:
        """Delete a task."""
        db = await get_mongo_db()
        collection = db[TaskRepository.COLLECTION_NAME]
        
        result = await collection.delete_one({"id": task_id})
        logger.info(f"[MONGO] Deleted task: {task_id} (matched: {result.deleted_count})")
        return result.deleted_count > 0
    
    @staticmethod
    def _normalize_doc(doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize MongoDB document."""
        if not doc:
            return None
        normalized = dict(doc)
        normalized.pop('_id', None)
        return normalized

