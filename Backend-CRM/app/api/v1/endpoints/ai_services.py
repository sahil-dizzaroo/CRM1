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
import uuid
import logging
# Tasks imported where needed to avoid circular imports


router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)

@router.get("/health/ai")
async def health_ai():
    """Check AI service health and configuration."""
    api_key_configured = bool(settings.gemini_api_key)
    ai_available = ai_service.is_available()
    model_info = "not initialized"
    init_error = None
    
    if ai_service.model:
        try:
            model_info = ai_service.model_name or "initialized"
        except:
            model_info = "initialized (unknown model name)"
    
    if hasattr(ai_service, '_init_error') and ai_service._init_error:
        init_error = ai_service._init_error
    
    # Debug info
    debug_info = {
        "api_key_configured": api_key_configured,
        "api_key_length": len(settings.gemini_api_key) if settings.gemini_api_key else 0,
        "api_key_preview": f"{settings.gemini_api_key[:10]}...{settings.gemini_api_key[-5:]}" if settings.gemini_api_key else None,
        "ai_service_available": ai_available,
        "model_info": model_info,
        "model_is_none": ai_service.model is None,
        "initialized": ai_service._initialized if hasattr(ai_service, '_initialized') else False,
        "init_error": init_error,
        "stored_api_key": f"{ai_service.api_key[:10]}...{ai_service.api_key[-5:]}" if ai_service.api_key else None
    }
    
    return debug_info


@router.get("/health/ai/test")
async def test_ai_api_key():
    """Test the API key with a direct Gemini API call."""
    import google.generativeai as genai
    import asyncio
    
    api_key = settings.gemini_api_key
    if not api_key:
        return {
            "success": False,
            "error": "API key not configured",
            "api_key_preview": None
        }
    
    try:
        # Configure and test using old SDK
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Make a test call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content("Say 'OK' in JSON: {\"status\": \"ok\"}")
        )
        
        if response and hasattr(response, 'text'):
            return {
                "success": True,
                "message": "API key is working!",
                "response_preview": response.text[:100],
                "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}"
            }
        else:
            return {
                "success": False,
                "error": "API call returned no response",
                "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}"
            }
    except Exception as e:
        error_msg = str(e)
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(e).__name__,
            "api_key_preview": f"{api_key[:10]}...{api_key[-5:]}" if api_key else None
        }


@router.post("/ai/compose-reply", response_model=schemas.AIComposeReplyResponse)
async def ai_compose_reply(
    payload: schemas.AIComposeReplyRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """AI compose‑assist for conversations or threads."""
    if not ai_service.is_available():
        api_key_status = "configured" if settings.gemini_api_key else "not configured"
        raise HTTPException(
            status_code=503,
            detail=f"AI service is not available. GEMINI_API_KEY is {api_key_status}. Please check your .env file.",
        )

    if not payload.conversation_id and not payload.thread_id:
        raise HTTPException(status_code=400, detail="conversation_id or thread_id is required")

    try:
        history_text = ""

        if payload.conversation_id:
            # Access check if user is authenticated
            if current_user:
                user_id = current_user.get("user_id")
                access_type = await crud.check_user_access(db, payload.conversation_id, user_id)
                if access_type is None:
                    raise HTTPException(status_code=403, detail="You don't have access to this conversation")

            conv = await crud.get_conversation_with_messages(db, payload.conversation_id, limit=200, offset=0)
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")

            messages = conv.get("messages", []) if isinstance(conv, dict) else conv.messages
            if not messages:
                raise HTTPException(status_code=400, detail="No messages found in conversation. Cannot generate reply drafts.")
            # For compose‑reply we rely purely on the actual message history
            # to avoid leaking stale subject lines from older contexts.
            history_text = ai_service._format_messages_for_summary(messages)  # type: ignore[attr-defined]
            if not history_text or not history_text.strip():
                raise HTTPException(status_code=400, detail="No message history available. Cannot generate reply drafts.")

        elif payload.thread_id:
            thread = await crud.get_thread_with_messages(db, payload.thread_id, limit=200, offset=0)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            messages = thread.get("messages", []) if isinstance(thread, dict) else thread.messages
            if not messages:
                raise HTTPException(status_code=400, detail="No messages found in thread. Cannot generate reply drafts.")
            history_text = ai_service._format_thread_messages_for_summary(messages)  # type: ignore[attr-defined]
            if not history_text or not history_text.strip():
                raise HTTPException(status_code=400, detail="No message history available. Cannot generate reply drafts.")

        result = await ai_service.compose_reply(history_text=history_text, latest_draft=payload.latest_draft)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate AI drafts")

        return schemas.AIComposeReplyResponse(
            drafts=schemas.AIComposeReplyDrafts(**result["drafts"]),
            summary=result["summary"],
            facts=result["facts"],
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ai_compose_reply: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating AI reply drafts: {str(e)}")


@router.post("/ai/check-message", response_model=schemas.AICheckMessageResponse)
async def ai_check_message(
    payload: schemas.AICheckMessageRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """AI pre‑send check for a draft message."""
    if not ai_service.is_available():
        api_key_status = "configured" if settings.gemini_api_key else "not configured"
        raise HTTPException(
            status_code=503,
            detail=f"AI service is not available. GEMINI_API_KEY is {api_key_status}. Please check your .env file.",
        )

    if not payload.conversation_id and not payload.thread_id:
        raise HTTPException(status_code=400, detail="conversation_id or thread_id is required")

    try:
        history_text = ""

        if payload.conversation_id:
            # Access check if user is authenticated
            if current_user:
                user_id = current_user.get("user_id")
                access_type = await crud.check_user_access(db, payload.conversation_id, user_id)
                if access_type is None:
                    raise HTTPException(status_code=403, detail="You don't have access to this conversation")

            conv = await crud.get_conversation_with_messages(db, payload.conversation_id, limit=50, offset=0)
            if not conv:
                raise HTTPException(status_code=404, detail="Conversation not found")
            messages = conv.get("messages", []) if isinstance(conv, dict) else conv.messages
            messages_text = ai_service._format_messages_for_summary(messages)  # type: ignore[attr-defined]
            history_text = messages_text

        elif payload.thread_id:
            thread = await crud.get_thread_with_messages(db, payload.thread_id, limit=50, offset=0)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            messages = thread.get("messages", []) if isinstance(thread, dict) else thread.messages
            messages_text = ai_service._format_thread_messages_for_summary(messages)  # type: ignore[attr-defined]
            history_text = messages_text

        result = await ai_service.check_message_before_send(
            context_text=history_text,
            draft_body=payload.draft_body,
            attachments=payload.attachments or [],
        )
        if not result:
            # If AI is unavailable at runtime, allow send with no issues
            return schemas.AICheckMessageResponse(issues=[], okToSend=True)

        issues = [schemas.AICheckMessageIssue(**issue) for issue in result.get("issues", [])]
        ok_to_send = bool(result.get("okToSend"))
        return schemas.AICheckMessageResponse(issues=issues, okToSend=ok_to_send)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in ai_check_message: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking message before send: {str(e)}")


@router.post("/chat")
async def chat(
    question: str = Form(...),
    mode: str = Form("general"),  # "general" or "document"
    document_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Chat with AI assistant - general chat or document-based Q&A. Messages are stored privately per user."""
    if not ai_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="AI service is not available. Please check GEMINI_API_KEY configuration."
        )
    
    user_id = current_user["user_id"]
    
    # Load chat history from database for this user
    db_messages = await crud.get_chat_messages(db, user_id, limit=50)
    history = []
    for msg in db_messages:
        history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Get document path if document_id is provided (must belong to user)
    document_path = None
    document_uuid = None
    if mode == "document" and document_id:
        try:
            document_uuid = UUID(document_id)
            # Get chat document from database (user-specific)
            chat_doc = await crud.get_chat_document(db, document_uuid, user_id)
            if chat_doc:
                # Make sure path is absolute or relative to app directory
                if os.path.isabs(chat_doc.file_path):
                    document_path = chat_doc.file_path
                else:
                    # Relative path - make it absolute relative to app directory
                    import pathlib
                    app_dir = pathlib.Path(__file__).parent.parent
                    document_path = str(app_dir / chat_doc.file_path)
                
                # Verify file exists
                if not os.path.exists(document_path):
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Document file not found at path: {document_path}. The file may have been deleted."
                    )
            else:
                raise HTTPException(status_code=404, detail="Document not found or access denied")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid document ID format")
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            print(f"Error fetching document: {e}")
            raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}")
    
    # Save user's question to database
    user_message = await crud.create_chat_message(
        db,
        user_id,
        schemas.ChatMessageCreate(
            role="user",
            content=question,
            mode=mode,
            document_id=document_uuid
        )
    )
    
    # Generate response
    try:
        response = await ai_service.chat_with_document(
            question=question,
            document_path=document_path,
            chat_history=history,
            mode=mode
        )
        
        if response is None:
            raise HTTPException(status_code=500, detail="Failed to generate response. Please check backend logs for details.")
        
        # Save assistant's response to database
        assistant_message = await crud.create_chat_message(
            db,
            user_id,
            schemas.ChatMessageCreate(
                role="assistant",
                content=response,
                mode=mode,
                document_id=document_uuid
            )
        )
        
        return {
            "response": response,
            "mode": mode,
            "document_id": document_id,
            "message_id": str(assistant_message.id)
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error in chat endpoint: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Save error message to database so user can see what went wrong
        try:
            await crud.create_chat_message(
                db,
                user_id,
                schemas.ChatMessageCreate(
                    role="assistant",
                    content=f"I encountered an error processing your request: {error_msg}. Please try again or contact support if the issue persists.",
                    mode=mode,
                    document_id=document_uuid
                )
            )
        except:
            pass  # Don't fail if we can't save the error message
        
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/chat/upload-document")
async def upload_chat_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document for chat-based Q&A. Documents are private to each user."""
    try:
        user_id = current_user["user_id"]
        
        # Save file - use relative path for storage
        import pathlib
        app_dir = pathlib.Path(__file__).parent.parent
        upload_dir_path = app_dir / settings.upload_dir
        os.makedirs(upload_dir_path, exist_ok=True)
        
        file_id = uuid.uuid4()
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        # Store relative path (will be resolved to absolute when needed)
        relative_file_path = os.path.join(settings.upload_dir, f"{file_id}{file_ext}")
        abs_file_path = upload_dir_path / f"{file_id}{file_ext}"
        
        with open(abs_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = os.path.getsize(abs_file_path)
        
        # Create chat document record (user-specific) - store relative path
        chat_doc = await crud.create_chat_document(
            db,
            user_id,
            relative_file_path,  # Store relative path
            file.filename or "unknown",
            file.content_type or "application/octet-stream",
            file_size
        )
        
        return {
            "document_id": str(chat_doc.id),
            "filename": chat_doc.filename,
            "size": chat_doc.size,
            "content_type": chat_doc.content_type
        }
    except Exception as e:
        print(f"Error uploading chat document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.get("/chat/messages", response_model=List[schemas.ChatMessageResponse])
async def get_chat_messages(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat message history for the current user (private)."""
    user_id = current_user["user_id"]
    messages = await crud.get_chat_messages(db, user_id, limit, offset)
    return messages


@router.get("/chat/documents", response_model=List[schemas.ChatDocumentResponse])
async def get_chat_documents(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all chat documents for the current user (private)."""
    user_id = current_user["user_id"]
    documents = await crud.get_user_chat_documents(db, user_id)
    return documents


@router.delete("/chat/documents/{document_id}")
async def delete_chat_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat document (only if it belongs to the current user)."""
    user_id = current_user["user_id"]
    success = await crud.delete_chat_document(db, document_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or access denied")
    return {"status": "deleted", "document_id": str(document_id)}


# ============================================================================
# Task Management Endpoints
# ============================================================================

@router.post("/ai/task-suggestion", response_model=schemas.AiTaskSuggestionResponse)
async def get_ai_task_suggestion(
    request: schemas.AiTaskSuggestionRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    AI endpoint to extract task information from a conversation message.
    Uses the same AI service pattern as conversation summaries.
    """
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        # Extract task using AI
        result = await ai_service.extract_task_from_message(
            message_text=request.messageText,
            recent_messages=request.recentMessages
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to extract task information")
        
        return schemas.AiTaskSuggestionResponse(
            title=result.get("title") or "",
            description=result.get("description"),
            suggestedStatus=result.get("suggestedStatus", "open"),
            suggestedDueDate=result.get("suggestedDueDate")
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_ai_task_suggestion: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate task suggestion: {str(e)}")


