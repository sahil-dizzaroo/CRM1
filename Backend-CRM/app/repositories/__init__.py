"""
Repository module for dual-database architecture.
Exports MongoDB and PostgreSQL repositories.
"""
from app.repositories.mongo_repository import (
    ConversationRepository,
    MessageRepository,
    AttachmentRepository,
    ThreadRepository,
    ThreadParticipantRepository,
    ThreadMessageRepository,
    ThreadAttachmentRepository,
    ThreadFromConversationRepository,
    TaskRepository
)
from app.repositories.postgres_repository import (
    UserRepository,
    ConversationAccessRepository,
    StudyRepository,
    SiteRepository,
    UserRoleAssignmentRepository
)

__all__ = [
    # MongoDB repositories
    "ConversationRepository",
    "MessageRepository",
    "AttachmentRepository",
    "ThreadRepository",
    "ThreadParticipantRepository",
    "ThreadMessageRepository",
    "ThreadAttachmentRepository",
    "ThreadFromConversationRepository",
    "TaskRepository",
    # PostgreSQL repositories
    "UserRepository",
    "ConversationAccessRepository",
    "StudyRepository",
    "SiteRepository",
    "UserRoleAssignmentRepository",
]

