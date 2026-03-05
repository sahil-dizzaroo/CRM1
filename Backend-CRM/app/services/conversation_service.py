"""
Conversation service helpers.
"""
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import ConversationRepository
from app.schemas import ConversationCreate
from app import crud


async def ensure_public_notice_board(db: AsyncSession, site_id: str, study_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Ensure a pinned Public Notice Board conversation exists for a site and study (study-specific).
    Each study+site combination has its own notice board.
    """
    existing = await ConversationRepository.get_pinned_notice_board(site_id, study_id)
    if existing:
        return existing

    conv = ConversationCreate(
        site_id=site_id,
        study_id=study_id,  # Study-specific notice board
        title="Public Notice Board",
        subject="Public Notice Board",
        conversation_type="notice_board",
        is_pinned=True,
        created_by="system",
    )
    return await crud.create_conversation(db, conv)

