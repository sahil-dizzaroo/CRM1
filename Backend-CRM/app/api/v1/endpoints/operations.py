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


router = APIRouter(tags=["Operations"])
logger = logging.getLogger(__name__)

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/tasks", response_model=schemas.TaskResponse)
async def create_task(
    task: schemas.TaskCreate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task."""
    try:
        # For now, store tasks in MongoDB (similar to conversations/threads)
        # In production, you might want a dedicated tasks collection
        from app.repositories import TaskRepository
        
        task_data = {
            "id": str(uuid.uuid4()),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "assigneeId": task.assigneeId,
            "dueDate": task.dueDate.isoformat() if task.dueDate else None,
            "createdByUserId": task.createdByUserId or (current_user.get("user_id") if current_user else None),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        
        # Handle links
        if task.links:
            task_data["links"] = {
                "siteId": task.links.siteId,
                "monitoringVisitId": task.links.monitoringVisitId,
                "monitoringReportId": task.links.monitoringReportId,
                "conversationId": task.links.conversationId,
                "messageId": task.links.messageId,
            }
        
        # Legacy fields for backward compatibility
        if task.siteId:
            task_data["siteId"] = task.siteId
        if task.monitoringVisitId:
            task_data["monitoringVisitId"] = task.monitoringVisitId
        if task.monitoringReportId:
            task_data["monitoringReportId"] = task.monitoringReportId
        if task.sourceConversationId:
            task_data["sourceConversationId"] = task.sourceConversationId
        
        created_task = await TaskRepository.create(task_data)
        
        # Convert to response format
        return schemas.TaskResponse(
            id=created_task.get("id"),
            title=created_task.get("title"),
            description=created_task.get("description"),
            status=created_task.get("status", "open"),
            assigneeId=created_task.get("assigneeId"),
            assigneeName=created_task.get("assigneeName"),
            dueDate=datetime.fromisoformat(created_task["dueDate"]) if created_task.get("dueDate") else None,
            createdAt=datetime.fromisoformat(created_task["createdAt"]),
            updatedAt=datetime.fromisoformat(created_task["updatedAt"]),
            createdByUserId=created_task.get("createdByUserId"),
            links=schemas.TaskLinks(**created_task["links"]) if created_task.get("links") else None,
            siteId=created_task.get("siteId"),
            monitoringVisitId=created_task.get("monitoringVisitId"),
            monitoringReportId=created_task.get("monitoringReportId"),
            sourceConversationId=created_task.get("sourceConversationId"),
        )
    except Exception as e:
        print(f"Error creating task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks", response_model=List[schemas.TaskResponse])
async def list_tasks(
    siteId: Optional[str] = Query(None),
    monitoringVisitId: Optional[str] = Query(None),
    conversationId: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """List tasks with optional filters."""
    try:
        from app.repositories import TaskRepository
        
        # Build filter
        filters = {}
        if siteId:
            filters["siteId"] = siteId
        if monitoringVisitId:
            filters["monitoringVisitId"] = monitoringVisitId
        if conversationId:
            filters["links.conversationId"] = conversationId
        if status:
            filters["status"] = status
        
        tasks = await TaskRepository.list(limit=limit, offset=offset, **filters)
        
        # Convert to response format
        result = []
        for task in tasks:
            result.append(schemas.TaskResponse(
                id=task.get("id"),
                title=task.get("title"),
                description=task.get("description"),
                status=task.get("status", "open"),
                assigneeId=task.get("assigneeId"),
                assigneeName=task.get("assigneeName"),
                dueDate=datetime.fromisoformat(task["dueDate"]) if task.get("dueDate") else None,
                createdAt=datetime.fromisoformat(task["createdAt"]),
                updatedAt=datetime.fromisoformat(task["updatedAt"]),
                createdByUserId=task.get("createdByUserId"),
                links=schemas.TaskLinks(**task["links"]) if task.get("links") else None,
                siteId=task.get("siteId"),
                monitoringVisitId=task.get("monitoringVisitId"),
                monitoringReportId=task.get("monitoringReportId"),
                sourceConversationId=task.get("sourceConversationId"),
            ))
        
        return result
    except Exception as e:
        print(f"Error listing tasks: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get a single task by ID."""
    try:
        from app.repositories import TaskRepository
        
        task = await TaskRepository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return schemas.TaskResponse(
            id=task.get("id"),
            title=task.get("title"),
            description=task.get("description"),
            status=task.get("status", "open"),
            assigneeId=task.get("assigneeId"),
            assigneeName=task.get("assigneeName"),
            dueDate=datetime.fromisoformat(task["dueDate"]) if task.get("dueDate") else None,
            createdAt=datetime.fromisoformat(task["createdAt"]),
            updatedAt=datetime.fromisoformat(task["updatedAt"]),
            createdByUserId=task.get("createdByUserId"),
            links=schemas.TaskLinks(**task["links"]) if task.get("links") else None,
            siteId=task.get("siteId"),
            monitoringVisitId=task.get("monitoringVisitId"),
            monitoringReportId=task.get("monitoringReportId"),
            sourceConversationId=task.get("sourceConversationId"),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: str,
    task_update: schemas.TaskUpdate,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Update a task."""
    try:
        from app.repositories import TaskRepository
        
        # Get existing task
        task = await TaskRepository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Build update dict
        updates = {}
        if task_update.title is not None:
            updates["title"] = task_update.title
        if task_update.description is not None:
            updates["description"] = task_update.description
        if task_update.status is not None:
            updates["status"] = task_update.status
        if task_update.assigneeId is not None:
            updates["assigneeId"] = task_update.assigneeId
        if task_update.dueDate is not None:
            updates["dueDate"] = task_update.dueDate.isoformat()
        if task_update.links is not None:
            updates["links"] = {
                "siteId": task_update.links.siteId,
                "monitoringVisitId": task_update.links.monitoringVisitId,
                "monitoringReportId": task_update.links.monitoringReportId,
                "conversationId": task_update.links.conversationId,
                "messageId": task_update.links.messageId,
            }
        
        updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        updated_task = await TaskRepository.update(task_id, updates)
        
        return schemas.TaskResponse(
            id=updated_task.get("id"),
            title=updated_task.get("title"),
            description=updated_task.get("description"),
            status=updated_task.get("status", "open"),
            assigneeId=updated_task.get("assigneeId"),
            assigneeName=updated_task.get("assigneeName"),
            dueDate=datetime.fromisoformat(updated_task["dueDate"]) if updated_task.get("dueDate") else None,
            createdAt=datetime.fromisoformat(updated_task["createdAt"]),
            updatedAt=datetime.fromisoformat(updated_task["updatedAt"]),
            createdByUserId=updated_task.get("createdByUserId"),
            links=schemas.TaskLinks(**updated_task["links"]) if updated_task.get("links") else None,
            siteId=updated_task.get("siteId"),
            monitoringVisitId=updated_task.get("monitoringVisitId"),
            monitoringReportId=updated_task.get("monitoringReportId"),
            sourceConversationId=updated_task.get("sourceConversationId"),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task."""
    try:
        from app.repositories import TaskRepository
        
        task = await TaskRepository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        await TaskRepository.delete(task_id)
        return {"status": "deleted", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


# ---------------------------------------------------------------------------
# Monitoring & Logistics Endpoints (Stub endpoints for Site Status)
# ---------------------------------------------------------------------------

@router.get("/monitoring/issues")
async def get_monitoring_issues(
    study_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get monitoring issues.
    Returns empty array for now - can be extended with real data later.
    """
    # TODO: Implement real monitoring issues fetching from database
    return []


@router.get("/logistics")
async def get_logistics(
    study_id: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Get site logistics data.
    Returns empty array for now - can be extended with real data later.
    """
    # TODO: Implement real logistics data fetching from database
    return []


# ---------------------------------------------------------------------------
# Site Status Dashboard Endpoints (READ‑ONLY)
# ---------------------------------------------------------------------------


