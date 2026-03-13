from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header, Query, UploadFile, File, Form, Request, Body
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
from app.models import MessageDirection, MessageStatus, MessageChannel, ConversationAccessLevel, ThreadAttachment, Attachment, Conversation, ChatDocument, PrimarySiteStatus, UserRoleAssignment, Site, Study, StudySite, SiteStatus, SiteWorkflowStep, SiteDocument, WorkflowStepName, StepStatus, DocumentCategory, DocumentType, ReviewStatus, ProjectFeasibilityCustomQuestion, FeasibilityRequest, FeasibilityResponse, FeasibilityRequestStatus, FeasibilityAttachment
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
from app.services.conversation_service import ensure_public_notice_board
import uuid
import logging
# Tasks imported where needed to avoid circular imports


router = APIRouter(tags=["Communications"])
logger = logging.getLogger(__name__)

@router.post("/conversations", response_model=schemas.ConversationResponse)
async def create_conversation(
    conv: schemas.ConversationCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # CRITICAL: Enforce study_id + site_id requirement for data isolation
    if not conv.study_id:
        raise HTTPException(status_code=400, detail="study_id is required for conversation creation")
    if not conv.site_id:
        raise HTTPException(status_code=400, detail="site_id is required for conversation creation")
    
    # Set created_by if user is authenticated
    if current_user:
        conv_dict = conv.dict()
        conv_dict['created_by'] = current_user.get("user_id")
        conv = schemas.ConversationCreate(**conv_dict)
    db_conv = await crud.create_conversation(db, conv)
    return db_conv


@router.get("/conversations", response_model=List[schemas.ConversationResponse])
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    study_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    channel: Optional[MessageChannel] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List conversations that are public within sites the user can access."""
    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access conversations")

    if site_id:
        await ensure_public_notice_board(db, site_id, study_id)

    conversations = await crud.list_conversations(db, limit=limit * 10, offset=offset, study_id=study_id, site_id=site_id, channel=channel, user_id=None)
    visible = []
    for conv in conversations:
        if await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
            visible.append(conv)
    
    # CRITICAL: Re-sort to ensure pinned items are at the top
    # Sort by is_pinned first (pinned="true" comes first), then by created_at descending
    def endpoint_sort_key(x):
        is_pinned_val = str(x.get('is_pinned', 'false')).lower().strip()
        is_pinned = (is_pinned_val == 'true' or is_pinned_val == '1' or is_pinned_val == 'yes' or is_pinned_val == 't')
        created_at = x.get('created_at')
        # Convert created_at to timestamp
        if isinstance(created_at, datetime):
            created_at_ts = created_at.timestamp()
        elif hasattr(created_at, 'timestamp'):
            created_at_ts = created_at.timestamp()
        elif isinstance(created_at, str):
            try:
                created_at_ts = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
            except:
                created_at_ts = 0
        else:
            created_at_ts = 0
        return (0 if is_pinned else 1, -created_at_ts)
    
    visible.sort(key=endpoint_sort_key)
    
    return visible[:limit]


@router.get("/conversations/stats")
async def get_stats(
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation and message statistics filtered by user access."""
    user_id = current_user.get("user_id") if current_user else None
    stats = await crud.get_conversation_stats(db, user_id=user_id)
    return stats


@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    limit: int = Query(200, ge=1, le=500),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0)
):
    """Get conversation with messages (public within accessible site)."""
    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access conversations")

    conv = await crud.get_conversation_with_messages(db, conversation_id, limit, offset)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
        raise HTTPException(status_code=403, detail="You don't have access to this conversation")
    
    # Handle dict from MongoDB - ensure messages have metadata field and proper format
    if isinstance(conv, dict):
        messages = conv.get('messages', [])
        
        # Normalize all messages
        normalized_messages = []
        for msg in messages:
            # Convert UUIDs to strings for JSON serialization
            normalized_msg = dict(msg)
            if 'id' in normalized_msg:
                normalized_msg['id'] = str(normalized_msg['id']) if isinstance(normalized_msg['id'], UUID) else normalized_msg['id']
            if 'conversation_id' in normalized_msg:
                normalized_msg['conversation_id'] = str(normalized_msg['conversation_id']) if isinstance(normalized_msg['conversation_id'], UUID) else normalized_msg['conversation_id']
            # Map metadata field
            if 'message_metadata' in normalized_msg and 'metadata' not in normalized_msg:
                normalized_msg['metadata'] = normalized_msg.pop('message_metadata')
            # Ensure status and direction are strings (handle both enum and string cases)
            if 'status' in normalized_msg:
                if hasattr(normalized_msg['status'], 'value'):
                    normalized_msg['status'] = normalized_msg['status'].value
                elif not isinstance(normalized_msg['status'], str):
                    normalized_msg['status'] = str(normalized_msg['status'])
            if 'direction' in normalized_msg:
                if hasattr(normalized_msg['direction'], 'value'):
                    normalized_msg['direction'] = normalized_msg['direction'].value
                elif not isinstance(normalized_msg['direction'], str):
                    normalized_msg['direction'] = str(normalized_msg['direction'])
                normalized_msg['direction'] = normalized_msg['direction'].lower()
            if 'channel' in normalized_msg:
                if hasattr(normalized_msg['channel'], 'value'):
                    normalized_msg['channel'] = normalized_msg['channel'].value
                elif not isinstance(normalized_msg['channel'], str):
                    normalized_msg['channel'] = str(normalized_msg['channel'])
                normalized_msg['channel'] = normalized_msg['channel'].lower()
            normalized_messages.append(normalized_msg)
        
        conv['messages'] = normalized_messages
    else:
        # Legacy SQLAlchemy model handling
        for msg in conv.messages:
            if hasattr(msg, 'message_metadata'):
                msg.metadata = msg.message_metadata
    return conv


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated summary of a conversation (public within accessible site)."""
    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access conversations")
    
    # Get conversation with messages
    conv = await crud.get_conversation_with_messages(db, conversation_id, limit=200, offset=0)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
        raise HTTPException(status_code=403, detail="You don't have access to this conversation")
    
    # Check if AI service is available
    if not ai_service.is_available():
        api_key_status = "configured" if settings.gemini_api_key else "not configured"
        raise HTTPException(
            status_code=503, 
            detail=f"AI service is not available. GEMINI_API_KEY is {api_key_status}. Please check your .env file."
        )
    
    # Generate summary
    try:
        # Handle dict from MongoDB
        messages = conv.get('messages', []) if isinstance(conv, dict) else conv.messages
        if not messages:
            return {"summary": "No messages in this conversation.", "conversation_id": str(conversation_id)}
        
        summary = await ai_service.summarize_conversation(conv, messages)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="Failed to generate summary. Check backend logs for details.")
        
        return {"summary": summary, "conversation_id": str(conversation_id)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_conversation_summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


# ---------------------------------------------------------------------------
# AI: Compose reply + pre‑send checks
# ---------------------------------------------------------------------------


@router.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageResponse)
async def create_message(
    conversation_id: UUID,
    msg: schemas.MessageCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Verify conversation exists
    conv = await crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get author information from authenticated user
    author_id = None
    author_name = None
    if current_user:
        author_id = current_user.get("user_id")
        author_name = current_user.get("name") or current_user.get("email") or author_id
    
    # Create message with status=queued and author information
    db_msg = await crud.create_message(
        db,
        conversation_id,
        msg,
        MessageDirection.OUTBOUND,
        author_id=author_id,
        author_name=author_name
    )

    # Handle dict from MongoDB
    msg_id = db_msg.get('id') if isinstance(db_msg, dict) else db_msg.id
    msg_channel = db_msg.get('channel') if isinstance(db_msg, dict) else db_msg.channel
    msg_body = db_msg.get('body') if isinstance(db_msg, dict) else db_msg.body
    msg_status = db_msg.get('status') if isinstance(db_msg, dict) else db_msg.status
    msg_author_id = db_msg.get('author_id') if isinstance(db_msg, dict) else db_msg.author_id
    msg_author_name = db_msg.get('author_name') if isinstance(db_msg, dict) else db_msg.author_name
    msg_created_at = db_msg.get('created_at') if isinstance(db_msg, dict) else db_msg.created_at

    # --- AI processing moved to background task to prevent blocking ---
    # Queue AI processing task (non-blocking with timeout)
    from app.workers.tasks import process_message_ai_task
    import asyncio

    async def _enqueue_ai_task():
        try:
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(
                    executor,
                    lambda: process_message_ai_task.delay(str(msg_id), str(conversation_id), msg_body)
                )
                # Fast timeout - AI processing is optional
                await asyncio.wait_for(future, timeout=1.0)
                print(f"✅ AI task queued: process_message_ai_task({msg_id})")
        except asyncio.TimeoutError:
            print(f"⚠️ AI task enqueue timed out after 1s (non-critical)")
        except Exception as e:
            print(f"❌ Failed to queue AI processing task: {e}")
    
    # Fire and forget - don't await, runs in background
    try:
        asyncio.create_task(_enqueue_ai_task())
    except Exception as e:
        print(f"❌ Failed to create AI task queue: {e}")

    # Create audit log (non-blocking - wrap in timeout and continue even if it fails)
    try:
        import asyncio
        await asyncio.wait_for(
            crud.create_audit_log(
                db,
                user=None,
                action="message_created",
                target_type="message",
                target_id=str(msg_id),
                details={"conversation_id": str(conversation_id), "channel": msg_channel if isinstance(msg_channel, str) else msg_channel.value}
            ),
            timeout=2.0
        )
    except asyncio.TimeoutError:
        print(f"Audit log creation timed out (non-critical)")
    except Exception as e:
        print(f"Audit log creation failed (non-critical): {e}")
    
    # Publish WebSocket event immediately for real-time updates (with timeout)
    try:
        from app.websocket_manager import manager
        import asyncio
        created_at_str = msg_created_at.isoformat() if hasattr(msg_created_at, 'isoformat') else str(msg_created_at)
        event_data = {
            "conversation_id": str(conversation_id),
            "type": "new_message",
            "message": {
                "id": str(msg_id),
                "direction": MessageDirection.OUTBOUND.value,
                "channel": msg_channel if isinstance(msg_channel, str) else msg_channel.value,
                "body": msg_body,
                "status": msg_status if isinstance(msg_status, str) else msg_status.value,
                "author_id": msg_author_id,
                "author_name": msg_author_name,
                "created_at": created_at_str
            }
        }
        # Add timeout to prevent hanging
        await asyncio.wait_for(manager.publish_event(conversation_id, event_data), timeout=3.0)
    except asyncio.TimeoutError:
        print(f"WebSocket publish timed out for conversation {conversation_id}")
    except Exception as e:
        print(f"Error publishing WebSocket event: {e}")
    
    # Queue Celery task (non-blocking with timeout)
    # IMPORTANT: This must not block the request response
    from app.workers.tasks import send_message_task
    import asyncio

    async def _enqueue_task():
        try:
            # Run in thread pool to avoid blocking the event loop
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(
                    executor,
                    lambda: send_message_task.delay(str(msg_id))
                )
                # Add timeout to prevent hanging - if Redis is slow, fail fast
                await asyncio.wait_for(future, timeout=1.0)
                print(f"✅ Celery task queued: send_message_task({msg_id})")
        except asyncio.TimeoutError:
            print(f"⚠️ Celery task enqueue timed out after 1s (task may still be queued)")
        except Exception as e:
            print(f"❌ Celery enqueue failed: {e}")
            # Don't fail the request - email sending will be retried by worker if needed
    
    # Fire and forget - don't await, runs in background
    try:
        asyncio.create_task(_enqueue_task())
    except Exception as e:
        print(f"❌ Failed to create Celery task queue: {e}")
    
    # Map message_metadata to metadata for response
    if isinstance(db_msg, dict):
        if 'message_metadata' in db_msg and 'metadata' not in db_msg:
            db_msg['metadata'] = db_msg.pop('message_metadata')
    elif hasattr(db_msg, 'message_metadata'):
        db_msg.metadata = db_msg.message_metadata
    
    return db_msg


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query("test")):
    conv_id = None
    try:
        # Accept the WebSocket connection first (do this immediately)
        await websocket.accept()
        print(f"WebSocket connection accepted for token: {token}")
        
        # Start Redis listener if not already started (non-blocking - won't fail if Redis unavailable)
        # Use asyncio.create_task to make it truly non-blocking
        try:
            asyncio.create_task(manager.start_listening())
        except Exception as e:
            print(f"Warning: Could not start Redis listener: {e}. WebSocket will still work.")
        
        # Wait for subscribe message with timeout
        try:
            # Set a timeout for receiving the subscribe message
            data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            print(f"Received subscribe message: {data}")
        except asyncio.TimeoutError:
            print("Timeout waiting for subscribe message")
            try:
                await websocket.close(code=1008, reason="Timeout waiting for subscribe")
            except:
                pass
            return
        except WebSocketDisconnect:
            # Client disconnected before sending subscribe message
            print("Client disconnected before subscribe")
            return
        except Exception as e:
            print(f"Error receiving subscribe message: {e}")
            import traceback
            traceback.print_exc()
            try:
                await websocket.close(code=1008, reason="Failed to receive subscribe message")
            except:
                pass
            return
        
        if data.get("action") != "subscribe":
            await websocket.send_json({"error": "Expected 'subscribe' action"})
            await websocket.close(code=1008, reason="Invalid action")
            return
        
        conversation_id = data.get("conversation_id")
        if not conversation_id:
            await websocket.send_json({"error": "Missing conversation_id"})
            await websocket.close(code=1008, reason="Missing conversation_id")
            return
        
        try:
            conv_id = UUID(conversation_id)
        except ValueError:
            await websocket.send_json({"error": "Invalid conversation_id format"})
            await websocket.close(code=1008, reason="Invalid conversation_id")
            return
        
        # Connect to manager
        try:
            await manager.connect(websocket, conv_id)
            await websocket.send_json({"status": "subscribed", "conversation_id": str(conv_id)})
        except Exception as e:
            print(f"Error connecting to manager: {e}")
            await websocket.close(code=1011, reason="Connection error")
            return
        
        # Keep connection alive and forward messages
        while True:
            try:
                # Wait for any message to keep connection alive
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                # Echo ping messages for keepalive
                if message.get("type") == "websocket.receive":
                    text = message.get("text", "")
                    if text == "ping":
                        await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket receive error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conv_id:
            try:
                await manager.disconnect(websocket, conv_id)
            except:
                pass


# Thread endpoints
@router.post("/threads", response_model=schemas.ThreadResponse)
async def create_thread(
    thread: schemas.ThreadCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Create a new thread with correct visibility semantics."""
    user_email = (current_user or {}).get("email")
    if not user_email:
        raise HTTPException(status_code=403, detail="Authentication required to create threads")

    # CRITICAL: Enforce study_id + site_id requirement for data isolation
    if not thread.related_study_id and not thread.site_id:
        raise HTTPException(
            status_code=400,
            detail="Either related_study_id or site_id is required for thread creation",
        )
    if thread.site_id and not thread.related_study_id:
        raise HTTPException(
            status_code=400,
            detail="related_study_id is required when site_id is provided",
        )

    # Normalize visibility scope
    visibility_scope = (thread.visibility_scope or "private").strip().lower()
    if visibility_scope not in ("private", "site"):
        visibility_scope = "private"

    creator_email = user_email.strip().lower()
    raw_participants = thread.participants_emails or []
    participants_emails = [
        str(e).strip().lower() for e in raw_participants if e and str(e).strip()
    ]

    if visibility_scope == "site":
        # Site-visible threads: no per-user participant list is needed for access control.
        participants_emails = []
    else:
        # Private threads: must contain creator + any selected users.
        if creator_email and creator_email not in participants_emails:
            participants_emails.append(creator_email)
        if not participants_emails:
            raise HTTPException(
                status_code=400,
                detail="participants_emails is required for private threads",
            )

    thread = thread.model_copy(
        update={
            "participants_emails": participants_emails,
            "visibility_scope": visibility_scope,
        }
    )
    db_thread = await crud.create_thread(db, thread)
    # Load with participants (db_thread is now a dict)
    thread_id = db_thread.get('id') if isinstance(db_thread, dict) else db_thread.id
    return await crud.get_thread(db, thread_id)


@router.get("/threads", response_model=List[schemas.ThreadResponse])
async def list_threads(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    thread_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    participant_id: Optional[str] = Query(None),
    study_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List threads. NEW: Only returns threads where logged-in user's email is in participants_emails."""
    # Get user email for filtering
    user_email = None
    if current_user:
        user_email = current_user.get("email")
    
    if not user_email:
        # If no user email, return empty list (threads are private)
        return []
    
    threads = await crud.list_threads(
        db, limit, offset, thread_type, status, participant_id, 
        study_id=study_id, site_id=site_id, user_email=user_email
    )
    return threads


@router.get("/threads/suggest-combinations", response_model=List[schemas.ThreadCombinationSuggestion])
async def suggest_thread_combinations(
    study_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    AI-powered endpoint to suggest which threads should be combined.
    Analyzes all threads and returns suggestions with similarity scores.
    """
    print(f"🔍 suggest-combinations called with study_id={study_id}, site_id={site_id}, limit={limit}")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        from app.repositories import ThreadRepository, ThreadMessageRepository
        
        # Get all threads for the study/site
        threads = await ThreadRepository.list(
            limit=limit * 2,  # Get more threads to analyze
            offset=0,
            study_id=study_id,
            site_id=site_id
        )
        
        if len(threads) < 2:
            return []
        
        suggestions = []
        
        # Compare each pair of threads
        for i in range(len(threads)):
            for j in range(i + 1, len(threads)):
                thread1 = threads[i]
                thread2 = threads[j]
                
                # Pre-check for exact matches (same title, same conversation, same patient)
                thread1_title = thread1.get('title', '').strip().lower()
                thread2_title = thread2.get('title', '').strip().lower()
                thread1_conv = thread1.get('conversation_id')
                thread2_conv = thread2.get('conversation_id')
                thread1_patient = thread1.get('related_patient_id')
                thread2_patient = thread2.get('related_patient_id')
                
                # Normalize conversation_id to string for comparison
                if thread1_conv:
                    thread1_conv = str(thread1_conv) if not isinstance(thread1_conv, str) else thread1_conv
                if thread2_conv:
                    thread2_conv = str(thread2_conv) if not isinstance(thread2_conv, str) else thread2_conv
                
                # Debug logging
                print(f"\n🔍 Comparing threads:")
                print(f"  Thread 1: '{thread1.get('title')}' | conv: {thread1_conv} | patient: {thread1_patient}")
                print(f"  Thread 2: '{thread2.get('title')}' | conv: {thread2_conv} | patient: {thread2_patient}")
                print(f"  Titles match: {thread1_title == thread2_title}")
                print(f"  Conversations match: {thread1_conv == thread2_conv}")
                
                # Check 1: Same title (even without conversation)
                if thread1_title == thread2_title and thread1_title:
                    # Same title - check if same conversation or same patient
                    if thread1_conv and thread2_conv and thread1_conv == thread2_conv:
                        # Exact match: same title and same conversation
                        print(f"  ✅ EXACT MATCH: Same title + same conversation")
                        # Ensure IDs are UUIDs
                        thread1_uuid = thread1['id'] if isinstance(thread1['id'], UUID) else UUID(str(thread1['id']))
                        thread2_uuid = thread2['id'] if isinstance(thread2['id'], UUID) else UUID(str(thread2['id']))
                        suggestions.append(schemas.ThreadCombinationSuggestion(
                            thread1_id=thread1_uuid,
                            thread2_id=thread2_uuid,
                            thread1_title=thread1.get('title', 'Untitled'),
                            thread2_title=thread2.get('title', 'Untitled'),
                            should_combine=True,
                            similarity_score=95.0,  # High score for exact matches
                            reasoning=f"Exact match: Both threads have the same title '{thread1.get('title')}' and belong to the same conversation. These should be combined to avoid duplication.",
                            factors=["Same title", "Same conversation", "Exact match"],
                            recommendation="strong"
                        ))
                        continue
                    elif thread1_patient and thread2_patient and thread1_patient == thread2_patient:
                        # Same title and same patient
                        print(f"  ✅ STRONG MATCH: Same title + same patient")
                        # Ensure IDs are UUIDs
                        thread1_uuid = thread1['id'] if isinstance(thread1['id'], UUID) else UUID(str(thread1['id']))
                        thread2_uuid = thread2['id'] if isinstance(thread2['id'], UUID) else UUID(str(thread2['id']))
                        suggestions.append(schemas.ThreadCombinationSuggestion(
                            thread1_id=thread1_uuid,
                            thread2_id=thread2_uuid,
                            thread1_title=thread1.get('title', 'Untitled'),
                            thread2_title=thread2.get('title', 'Untitled'),
                            should_combine=True,
                            similarity_score=90.0,
                            reasoning=f"Strong match: Both threads have the same title '{thread1.get('title')}' and are for the same patient '{thread1_patient}'. These should be combined.",
                            factors=["Same title", "Same patient", "Strong match"],
                            recommendation="strong"
                        ))
                        continue
                    else:
                        # Just same title - still suggest combining
                        print(f"  ✅ TITLE MATCH: Same title (no conversation/patient match)")
                        # Ensure IDs are UUIDs
                        thread1_uuid = thread1['id'] if isinstance(thread1['id'], UUID) else UUID(str(thread1['id']))
                        thread2_uuid = thread2['id'] if isinstance(thread2['id'], UUID) else UUID(str(thread2['id']))
                        suggestions.append(schemas.ThreadCombinationSuggestion(
                            thread1_id=thread1_uuid,
                            thread2_id=thread2_uuid,
                            thread1_title=thread1.get('title', 'Untitled'),
                            thread2_title=thread2.get('title', 'Untitled'),
                            should_combine=True,
                            similarity_score=85.0,
                            reasoning=f"Title match: Both threads have the same title '{thread1.get('title')}'. These may be duplicates and should be combined.",
                            factors=["Same title", "Possible duplicate"],
                            recommendation="moderate"
                        ))
                        continue
                
                # Get messages for both threads
                thread1_messages = await ThreadMessageRepository.list_by_thread(
                    thread1['id'], limit=50, offset=0
                )
                thread2_messages = await ThreadMessageRepository.list_by_thread(
                    thread2['id'], limit=50, offset=0
                )
                
                # Analyze similarity with AI
                analysis = await ai_service.analyze_thread_similarity(
                    thread1, thread2, thread1_messages, thread2_messages
                )
                
                if analysis and analysis.get('should_combine'):
                    # Ensure IDs are UUIDs
                    thread1_uuid = thread1['id'] if isinstance(thread1['id'], UUID) else UUID(str(thread1['id']))
                    thread2_uuid = thread2['id'] if isinstance(thread2['id'], UUID) else UUID(str(thread2['id']))
                    suggestions.append(schemas.ThreadCombinationSuggestion(
                        thread1_id=thread1_uuid,
                        thread2_id=thread2_uuid,
                        thread1_title=thread1.get('title', 'Untitled'),
                        thread2_title=thread2.get('title', 'Untitled'),
                        should_combine=analysis['should_combine'],
                        similarity_score=analysis['similarity_score'],
                        reasoning=analysis['reasoning'],
                        factors=analysis['factors'],
                        recommendation=analysis['recommendation']
                    ))
        
        # Sort by similarity score (highest first)
        suggestions.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Return top suggestions
        return suggestions[:limit]
        
    except Exception as e:
        print(f"Error suggesting thread combinations: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to suggest combinations: {str(e)}")


@router.get("/threads/{thread_id}", response_model=schemas.ThreadWithMessages)
async def get_thread(
    thread_id: UUID,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get a thread with its messages. NEW: Only accessible if user email is in participants_emails."""
    # Get user email for access check
    user_email = None
    if current_user:
        user_email = current_user.get("email")
    
    if not user_email:
        raise HTTPException(status_code=403, detail="Authentication required to access threads")
    
    thread = await crud.get_thread_with_messages(db, thread_id, limit, offset)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # NEW VISIBILITY LOGIC: Allow access if visibility_scope='site' OR user_email in participants_emails
    visibility_scope = thread.get('visibility_scope', 'private')
    participants_emails = thread.get('participants_emails', [])
    user_email_lower = user_email.lower().strip()
    participant_emails_lower = [str(e).lower().strip() for e in participants_emails if e]
    
    # Check access: site-wide threads OR user is a participant
    has_access = (
        visibility_scope == 'site' or
        user_email_lower in participant_emails_lower
    )
    
    if not has_access:
        # Legacy fallback: check old thread_participants table
        from app.repositories import ThreadParticipantRepository
        participants = await ThreadParticipantRepository.list_by_thread(thread_id)
        participant_emails = [str(p.get("participant_email", "")).lower().strip() for p in participants if p.get("participant_email")]
        if user_email_lower not in participant_emails:
            raise HTTPException(status_code=403, detail="You don't have access to this thread")
    
    return thread


@router.get("/threads/{thread_id}/summary")
async def get_thread_summary(
    thread_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated summary of a thread."""
    # Get thread with messages
    thread = await crud.get_thread_with_messages(db, thread_id, limit=200, offset=0)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # NEW VISIBILITY LOGIC: Allow access if visibility_scope='site' OR user_email in participants_emails
    user_email = (current_user or {}).get("email")
    if not user_email:
        raise HTTPException(status_code=403, detail="Authentication required to access threads")
    
    visibility_scope = thread.get('visibility_scope', 'private')
    allowed_emails = [str(e).lower().strip() for e in (thread.get("participants_emails") or []) if e]
    user_email_lower = user_email.lower().strip()
    
    has_access = (
        visibility_scope == 'site' or
        user_email_lower in allowed_emails
    )
    
    if not has_access:
        # Legacy fallback: check old thread_participants table
        from app.repositories import ThreadParticipantRepository
        participants = await ThreadParticipantRepository.list_by_thread(thread_id)
        participant_emails = [str(p.get("participant_email", "")).lower().strip() for p in participants if p.get("participant_email")]
        if user_email_lower not in participant_emails:
            raise HTTPException(status_code=403, detail="You don't have access to this thread")
    
    # Check if AI service is available
    if not ai_service.is_available():
        api_key_status = "configured" if settings.gemini_api_key else "not configured"
        raise HTTPException(
            status_code=503, 
            detail=f"AI service is not available. GEMINI_API_KEY is {api_key_status}. Please check your .env file."
        )
    
    # Generate summary
    try:
        # Handle dict from MongoDB
        messages = thread.get('messages', []) if isinstance(thread, dict) else thread.messages
        summary = await ai_service.summarize_thread(thread, messages)
        
        if summary is None:
            raise HTTPException(status_code=500, detail="Failed to generate summary. Check backend logs for details.")
        
        return {"summary": summary, "thread_id": str(thread_id)}
    except Exception as e:
        print(f"Error in get_thread_summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.post("/threads/{thread_id}/participants", response_model=schemas.ThreadParticipantResponse)
async def add_participant(
    thread_id: UUID,
    participant: schemas.ThreadParticipantCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a participant to a thread."""
    # Check if thread exists
    thread = await crud.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    db_participant = await crud.add_thread_participant(db, thread_id, participant)
    return db_participant


@router.post("/threads/{thread_id}/participants/emails", response_model=schemas.ThreadResponse)
async def add_thread_participant_email(
    thread_id: UUID,
    email: str = Body(..., embed=True, description="Email address to add to participants_emails"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Add an email to thread's participants_emails list. Only thread creator or existing participant can modify."""
    user_email = (current_user or {}).get("email") if current_user else None
    
    try:
        updated_thread = await crud.add_thread_participant_email(
            db=db,
            thread_id=thread_id,
            email=email,
            user_email=user_email
        )
        return updated_thread
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add participant email: {str(e)}")


@router.delete("/threads/{thread_id}/participants/emails/{email}", response_model=schemas.ThreadResponse)
async def remove_thread_participant_email(
    thread_id: UUID,
    email: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Remove an email from thread's participants_emails list. Only thread creator or existing participant can modify."""
    user_email = (current_user or {}).get("email") if current_user else None
    
    try:
        updated_thread = await crud.remove_thread_participant_email(
            db=db,
            thread_id=thread_id,
            email=email,
            user_email=user_email
        )
        return updated_thread
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove participant email: {str(e)}")


@router.post("/conversations/{conversation_id}/create-thread", response_model=schemas.ThreadResponse)
async def create_thread_from_conversation(
    conversation_id: UUID,
    request: schemas.CreateThreadFromConversationRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Create a thread from selected messages in a conversation."""
    try:
        thread = await crud.create_thread_from_conversation(
            db=db,
            conversation_id=conversation_id,
            title=request.title,
            description=request.description,
            thread_type=request.thread_type,
            message_ids=request.message_ids,
            created_by=request.created_by,
            creator_email=(current_user or {}).get("email"),
            related_study_id=request.related_study_id,
            visibility_scope=request.visibility_scope,
            participants_emails=request.participants_emails,
        )
        return thread
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


@router.post("/threads/{thread_id}/messages", response_model=schemas.ThreadMessageResponse)
async def create_thread_message(
    thread_id: UUID,
    message: schemas.ThreadMessageCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a thread (participants only)."""
    # Check if thread exists
    thread = await crud.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    user_email = (current_user or {}).get("email")
    if not user_email:
        raise HTTPException(status_code=403, detail="Authentication required to post in threads")

    participants_emails = [str(e).lower().strip() for e in (thread.get("participants_emails") or []) if e]
    if user_email.lower() not in participants_emails:
        # Legacy fallback: support old thread_participants rows.
        from app.repositories import ThreadParticipantRepository
        participants = await ThreadParticipantRepository.list_by_thread(thread_id)
        participant_emails = [str(p.get("participant_email", "")).lower().strip() for p in participants if p.get("participant_email")]
        if user_email.lower() not in participant_emails:
            raise HTTPException(status_code=403, detail="You don't have access to this thread")
    
    db_message = await crud.create_thread_message(db, thread_id, message)

    # Reuse unified email worker pipeline for thread messages.
    try:
        from app.repositories import ThreadMessageRepository
        from app.workers.tasks import send_message_task

        thread_msg_id = db_message.get("id") if isinstance(db_message, dict) else db_message.id
        mentioned_emails = db_message.get("mentioned_emails", []) if isinstance(db_message, dict) else []
        if mentioned_emails:
            await ThreadMessageRepository.update_fields(
                thread_msg_id,
                {"status": MessageStatus.QUEUED.value},
            )
            send_message_task.delay(str(thread_msg_id), source_type="thread")
        else:
            await ThreadMessageRepository.update_fields(
                thread_msg_id,
                {
                    "status": MessageStatus.DELIVERED.value,
                    "delivered_at": datetime.now(timezone.utc),
                },
            )
    except Exception as e:
        print(f"Thread message email pipeline enqueue failed: {e}")

    # --- AI tone/delta + thread summary (for threads) ---
    try:
        if ai_service.is_available():
            from app.repositories import ThreadMessageRepository, ThreadRepository
            # Load recent thread messages (latest first)
            history = await ThreadMessageRepository.list_by_thread(thread_id, limit=50, offset=0)
            if history:
                latest = history[0]
                older = history[1:]
                history_text = ai_service._format_thread_messages_for_summary(older[::-1])
                analysis = await ai_service.analyse_new_message(history_text, latest.get('body', ''))
                if analysis:
                    await ThreadMessageRepository.update_fields(latest.get('id'), {
                        'ai_tone': analysis.get('tone'),
                        'ai_delta_summary': analysis.get('delta_summary'),
                    })
                # Update thread‑level summary as well
                summary = await ai_service.summarize_thread(thread, history[::-1])
                if summary:
                    from datetime import datetime, timezone
                    await ThreadRepository.update(thread_id, {
                        'ai_summary': summary,
                        'ai_summary_updated_at': datetime.now(timezone.utc),
                    })
    except Exception as e:
        print(f"AI post-processing failed for thread message: {e}")

    # Publish to Redis for real-time updates
    try:
        from app.websocket_manager import manager
        msg_id = db_message.get("id") if isinstance(db_message, dict) else db_message.id
        msg_body = db_message.get("body") if isinstance(db_message, dict) else db_message.body
        msg_author_id = db_message.get("author_id") if isinstance(db_message, dict) else db_message.author_id
        msg_author_name = db_message.get("author_name") if isinstance(db_message, dict) else db_message.author_name
        msg_created_at = db_message.get("created_at") if isinstance(db_message, dict) else db_message.created_at
        await manager.publish_thread_update(thread_id, {
            "type": "new_message",
            "thread_id": str(thread_id),
            "message": {
                "id": str(msg_id),
                "body": msg_body,
                "author_id": msg_author_id,
                "author_name": msg_author_name,
                "created_at": msg_created_at.isoformat() if hasattr(msg_created_at, "isoformat") else str(msg_created_at)
            }
        })
    except Exception as e:
        print(f"Error publishing thread update: {e}")
    
    return db_message


@router.patch("/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: UUID,
    status: str = Query(..., regex="^(open|in_progress|resolved|closed)$"),
    db: AsyncSession = Depends(get_db)
):
    """Update thread status."""
    thread = await crud.update_thread_status(db, thread_id, status)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"status": "updated", "thread_id": str(thread_id), "new_status": status}


@router.post("/threads/{thread_id}/file-in-tmf")
async def file_thread_in_tmf(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Mark a thread for TMF filing.
    This is a placeholder implementation that:
    - Updates the thread with tmf_filed = True
    - Creates a system message in the thread
    - Logs the action
    
    Future implementation will integrate with actual TMF system.
    """
    # Check if thread exists
    thread = await crud.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if already filed
    thread_dict = thread if isinstance(thread, dict) else thread.__dict__
    if thread_dict.get('tmf_filed'):
        raise HTTPException(status_code=400, detail="Thread is already marked for TMF filing")
    
    # Call the TMF service
    from app.services.tmf_service import send_thread_to_tmf
    success = await send_thread_to_tmf(thread_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark thread for TMF filing")
    
    # Refresh thread to get updated data
    updated_thread = await crud.get_thread(db, thread_id)
    
    return {
        "status": "success",
        "message": "Thread marked for TMF filing",
        "thread_id": str(thread_id),
        "tmf_filed": True,
        "tmf_filed_at": updated_thread.get('tmf_filed_at') if isinstance(updated_thread, dict) else getattr(updated_thread, 'tmf_filed_at', None)
    }


# Access Control Endpoints
@router.patch("/conversations/{conversation_id}/access", response_model=schemas.ConversationResponse)
async def update_conversation_access(
    conversation_id: UUID,
    request: schemas.UpdateConversationAccessRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation access settings. All authenticated users can update for now."""
    current_user_id = current_user["user_id"]
    # For now, allow all authenticated users to update access settings
    
    conv = await crud.update_conversation_access(
        db=db,
        conversation_id=conversation_id,
        is_restricted=request.is_restricted,
        is_confidential=request.is_confidential,
        privileged_users=request.privileged_users
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.post("/conversations/{conversation_id}/grant-access", response_model=schemas.ConversationAccessResponse)
async def grant_access(
    conversation_id: UUID,
    request: schemas.GrantAccessRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grant access to a conversation for a user. All authenticated users can grant access for now."""
    current_user_id = current_user["user_id"]
    # For now, allow all authenticated users to grant access
    
    access = schemas.ConversationAccessCreate(
        user_id=request.user_id,
        access_type=request.access_type,
        granted_by=current_user_id
    )
    return await crud.grant_conversation_access(db, conversation_id, access)


@router.delete("/conversations/{conversation_id}/revoke-access/{user_id}")
async def revoke_access(
    conversation_id: UUID,
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revoke access to a conversation for a user. All authenticated users can revoke access for now."""
    current_user_id = current_user["user_id"]
    # For now, allow all authenticated users to revoke access
    
    success = await crud.revoke_conversation_access(db, conversation_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Access grant not found")
    return {"status": "revoked", "conversation_id": str(conversation_id), "user_id": user_id}


@router.get("/conversations/{conversation_id}/access", response_model=List[schemas.ConversationAccessResponse])
async def get_access_list(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of all users with access to a conversation."""
    # For now, all authenticated users have equal access - no restrictions
    return await crud.get_conversation_access_list(db, conversation_id)


@router.get("/conversations/{conversation_id}/check-access")
async def check_access(
    conversation_id: UUID,
    user_id: str = Query(..., description="User ID to check"),
    db: AsyncSession = Depends(get_db)
):
    """Check if a user has access to a conversation."""
    access_type = await crud.check_user_access(db, conversation_id, user_id)
    return {
        "has_access": access_type is not None,
        "access_type": access_type
    }


# Authentication endpoints
@router.post("/conversations/{conversation_id}/attachments", response_model=schemas.AttachmentResponse)
async def upload_conversation_attachment(
    conversation_id: UUID,
    file: UploadFile = File(...),
    message_id: Optional[UUID] = Form(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file attachment to a conversation."""
    # Verify conversation exists
    conv = await crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access conversations")
    if not await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
        raise HTTPException(status_code=403, detail="You don't have access to this conversation")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix if file.filename else ""
    file_id = uuid.uuid4()
    file_name = f"{file_id}{file_ext}"
    file_path = upload_dir / file_name
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate file size and checksum
        file_size = file_path.stat().st_size
        checksum = None
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                checksum = file_hash.hexdigest()
        except Exception:
            pass  # Checksum is optional
        
        # Create attachment record
        attachment = await crud.create_attachment(
            db=db,
            conversation_id=conversation_id,
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            message_id=message_id,
            checksum=checksum
        )
        
        # Add file_name to response
        response_data = schemas.AttachmentResponse.model_validate(attachment)
        response_data.file_name = file.filename
        return response_data
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.post("/threads/{thread_id}/attachments", response_model=schemas.ThreadAttachmentResponse)
async def upload_thread_attachment(
    thread_id: UUID,
    file: UploadFile = File(...),
    thread_message_id: Optional[UUID] = Form(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file attachment to a thread."""
    # Verify thread exists
    thread = await crud.get_thread(db, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix if file.filename else ""
    file_id = uuid.uuid4()
    file_name = f"{file_id}{file_ext}"
    file_path = upload_dir / file_name
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Calculate file size and checksum
        file_size = file_path.stat().st_size
        checksum = None
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.md5()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                checksum = file_hash.hexdigest()
        except Exception:
            pass  # Checksum is optional
        
        # Create attachment record (linked to conversation)
        attachment = await crud.create_attachment(
            db=db,
            conversation_id=thread.conversation_id,
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            message_id=None,  # Thread attachments are not linked to messages
            checksum=checksum
        )
        
        # Link attachment to thread
        thread_attachment = await crud.create_thread_attachment(
            db=db,
            thread_id=thread_id,
            attachment_id=attachment.id,
            thread_message_id=thread_message_id
        )
        
        # Load attachment details
        await db.refresh(thread_attachment)
        result = await db.execute(
            select(ThreadAttachment)
            .where(ThreadAttachment.id == thread_attachment.id)
            .options(selectinload(ThreadAttachment.attachment))
        )
        thread_attachment = result.scalar_one()
        
        response_data = schemas.ThreadAttachmentResponse.model_validate(thread_attachment)
        if thread_attachment.attachment:
            att_resp = schemas.AttachmentResponse.model_validate(thread_attachment.attachment)
            att_resp.file_name = file.filename
            response_data.attachment = att_resp
        return response_data
        
    except Exception as e:
        # Clean up file if database operation fails
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/conversations/{conversation_id}/attachments", response_model=List[schemas.AttachmentResponse])
async def list_conversation_attachments(
    conversation_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List all attachments for a conversation."""
    conv = await crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access conversations")
    if not await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
        raise HTTPException(status_code=403, detail="You don't have access to this conversation")
    
    attachments = await crud.list_conversation_attachments(db, conversation_id)
    # Add file_name to each attachment
    result: List[schemas.AttachmentResponse] = []
    for att in attachments:
        # att may be a SQLAlchemy object or a dict from Mongo‑backed CRUD
        att_resp = schemas.AttachmentResponse.model_validate(att)
        file_path = att_resp.file_path
        att_resp.file_name = Path(file_path).name if file_path else None
        result.append(att_resp)
    return result


@router.get("/threads/{thread_id}/attachments", response_model=List[schemas.ThreadAttachmentResponse])
async def list_thread_attachments(
    thread_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List all attachments for a thread."""
    thread_attachments = await crud.list_thread_attachments(db, thread_id)
    # Load attachment details
    result = []
    for ta in thread_attachments:
        await db.refresh(ta)
        db_result = await db.execute(
            select(ThreadAttachment)
            .where(ThreadAttachment.id == ta.id)
            .options(selectinload(ThreadAttachment.attachment))
        )
        ta_loaded = db_result.scalar_one()
        ta_resp = schemas.ThreadAttachmentResponse.model_validate(ta_loaded)
        if ta_loaded.attachment:
            att_resp = schemas.AttachmentResponse.model_validate(ta_loaded.attachment)
            att_resp.file_name = Path(ta_loaded.attachment.file_path).name if ta_loaded.attachment.file_path else None
            ta_resp.attachment = att_resp
        result.append(ta_resp)
    return result


@router.post("/threads/combine", response_model=schemas.ThreadResponse)
async def combine_threads(
    request: schemas.CombineThreadsRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    Combine two threads into one. Merges participants, messages, and attachments.
    The target_thread_id is the thread that will be kept.
    """
    try:
        combined_thread = await crud.combine_threads(
            db=db,
            thread1_id=request.thread1_id,
            thread2_id=request.thread2_id,
            target_thread_id=request.target_thread_id
        )
        
        if not combined_thread:
            raise HTTPException(status_code=404, detail="Failed to combine threads")
        
        return combined_thread
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error combining threads: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to combine threads: {str(e)}")


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Download an attachment file."""
    attachment = await crud.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    conv = await crud.get_conversation(db, attachment.conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_id = (current_user or {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Authentication required to access attachments")
    if not await crud.check_user_can_access_conversation_by_role(db, user_id, conv):
        raise HTTPException(status_code=403, detail="You don't have access to this attachment")
    
    file_path = Path(attachment.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Get original filename if available, otherwise use file path name
    file_name = Path(attachment.file_path).name
    
    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type=attachment.content_type
    )


# User Profile Endpoints
