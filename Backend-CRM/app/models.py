from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, JSON, Enum as SQLEnum, TypeDecorator, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
import uuid
import enum
from app.db import Base


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(str, enum.Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class MessageStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class ConversationAccessLevel(str, enum.Enum):
    PUBLIC = "public"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_phone = Column(String(50), nullable=True)
    participant_email = Column(String(255), nullable=True)  # Primary/legacy email for backward compatibility
    participant_emails = Column(JSON, nullable=True, default=list)  # Array of email addresses for multiple recipients
    subject = Column(String(500), nullable=True)
    title = Column(String(500), nullable=True)
    study_id = Column(String(100), nullable=True)
    site_id = Column(String(100), nullable=True)  # Site ID for site-centric filtering
    conversation_type = Column(String(50), nullable=True, default="notice_board")
    is_pinned = Column(String(10), nullable=False, default='false')
    # Access control fields
    is_restricted = Column(String(10), nullable=False, default='false')  # 'true' or 'false' as string for simplicity
    is_confidential = Column(String(10), nullable=False, default='false')
    created_by = Column(String(255), nullable=True)  # User who created the conversation
    sponsor_id = Column(String(255), nullable=True)  # Sponsor who initiated (if applicable)
    access_level = Column(String(50), nullable=False, default='PUBLIC')  # Use String instead of Enum to avoid case issues
    privileged_users = Column(JSON, nullable=True, default=list)  # List of user IDs with privileged access
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="conversation", cascade="all, delete-orphan")
    access_grants = relationship("ConversationAccess", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    direction = Column(SQLEnum(MessageDirection), nullable=False)
    channel = Column(SQLEnum(MessageChannel), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(SQLEnum(MessageStatus), nullable=False, default=MessageStatus.QUEUED)
    provider_message_id = Column(String(255), nullable=True)
    message_metadata = Column(JSON, nullable=True, default=dict)
    mentioned_emails = Column(JSON, nullable=True, default=list)
    author_id = Column(String(255), nullable=True)  # User who sent the message (user_id)
    author_name = Column(String(255), nullable=True)  # Display name of the sender
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    conversation = relationship("Conversation", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    checksum = Column(String(64), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    message = relationship("Message", back_populates="attachments")
    conversation = relationship("Conversation", back_populates="attachments")


class Thread(Base):
    __tablename__ = "threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    thread_type = Column(String(50), nullable=False)  # 'issue', 'patient', 'general'
    related_patient_id = Column(String(255), nullable=True)  # Reference to patient/participant
    related_study_id = Column(String(100), nullable=True)  # Reference to study
    site_id = Column(String(100), nullable=True)  # Site ID for site-centric filtering
    status = Column(String(50), nullable=False, default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    priority = Column(String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'urgent'
    participants_emails = Column(JSON, nullable=True, default=list)
    visibility_scope = Column(String(50), nullable=False, default='private')  # 'private' or 'site'
    created_by = Column(String(255), nullable=True)  # User who created the thread
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    participants = relationship("ThreadParticipant", back_populates="thread", cascade="all, delete-orphan")
    messages = relationship("ThreadMessage", back_populates="thread", cascade="all, delete-orphan")
    attachments = relationship("ThreadAttachment", back_populates="thread", foreign_keys="ThreadAttachment.thread_id", cascade="all, delete-orphan")


class ThreadParticipant(Base):
    __tablename__ = "thread_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    participant_id = Column(String(255), nullable=False)  # User/participant identifier
    participant_name = Column(String(255), nullable=True)  # Display name
    participant_email = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default='participant')  # 'creator', 'participant', 'assignee'
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thread = relationship("Thread", back_populates="participants")


class ThreadMessage(Base):
    __tablename__ = "thread_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)  # Link to existing message if applicable
    body = Column(Text, nullable=False)
    author_id = Column(String(255), nullable=False)  # User who wrote the message
    author_name = Column(String(255), nullable=True)
    mentioned_emails = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thread = relationship("Thread", back_populates="messages")
    message = relationship("Message", foreign_keys=[message_id])
    attachments = relationship("ThreadAttachment", back_populates="thread_message", cascade="all, delete-orphan")


class ThreadAttachment(Base):
    __tablename__ = "thread_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    thread_message_id = Column(UUID(as_uuid=True), ForeignKey("thread_messages.id"), nullable=True)  # Optional: link to specific message
    attachment_id = Column(UUID(as_uuid=True), ForeignKey("attachments.id"), nullable=False)  # Link to the actual attachment
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thread = relationship("Thread", foreign_keys=[thread_id])
    thread_message = relationship("ThreadMessage", back_populates="attachments")
    attachment = relationship("Attachment", foreign_keys=[attachment_id])


class UserRole(str, enum.Enum):
    SPONSOR = "sponsor"
    SITE_MANAGER = "site_manager"
    COORDINATOR = "coordinator"
    PARTICIPANT = "participant"
    CRA = "cra"  # Clinical Research Associate
    STUDY_MANAGER = "study_manager"  # Study Manager
    MEDICAL_MONITOR = "medical_monitor"  # Medical Monitor


class AccessType(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False)  # Unique identifier (email, username, etc.)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, unique=True)  # Email should be unique for login
    password_hash = Column(String(255), nullable=True)  # Hashed password for authentication
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.PARTICIPANT)
    is_privileged = Column(String(10), nullable=False, default='false')  # Can manage confidential conversations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    access_grants = relationship(
        "ConversationAccess", 
        back_populates="user",
        primaryjoin="User.user_id == foreign(ConversationAccess.user_id)"
    )


class ConversationAccess(Base):
    __tablename__ = "conversation_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String(255), nullable=False)  # Reference to User.user_id
    access_type = Column(SQLEnum(AccessType), nullable=False, default=AccessType.READ)
    granted_by = Column(String(255), nullable=True)  # User who granted access
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="access_grants")
    user = relationship(
        "User", 
        back_populates="access_grants",
        primaryjoin="foreign(ConversationAccess.user_id) == User.user_id"
    )


class ThreadFromConversation(Base):
    __tablename__ = "thread_from_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    source_message_ids = Column(JSON, nullable=False)  # List of message IDs that were used to create thread
    created_by = Column(String(255), nullable=True)  # User who created the thread from conversation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thread = relationship("Thread", foreign_keys=[thread_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


# User Profile Models
class RDStudy(Base):
    __tablename__ = "rd_studies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    study_title = Column(String(500), nullable=False)
    nct_number = Column(String(50), nullable=True)
    asset = Column(String(255), nullable=True)
    indication = Column(String(255), nullable=True)
    enrollment = Column(Integer, nullable=True)
    phases = Column(String(50), nullable=True)  # PHASE1, PHASE2, PHASE3, etc.
    start_date = Column(DateTime(timezone=True), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class IISStudy(Base):
    __tablename__ = "iis_studies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    study_title = Column(String(500), nullable=False)
    asset = Column(String(255), nullable=True)
    indication = Column(String(255), nullable=True)
    phases = Column(String(50), nullable=True)
    enrollment = Column(Integer, nullable=True)
    enrollment_start_date = Column(DateTime(timezone=True), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    other_associated_hcp_ids = Column(JSON, nullable=True, default=list)  # List of HCP IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    event_name = Column(String(500), nullable=False)
    internal_external = Column(String(20), nullable=False)  # 'Internal' or 'External'
    event_type = Column(String(100), nullable=True)  # 'Adboard', 'Conference', etc.
    date_of_event = Column(DateTime(timezone=True), nullable=True)
    event_description = Column(Text, nullable=True)
    event_report = Column(Text, nullable=True)
    relevant_internal_stakeholders = Column(JSON, nullable=True, default=list)  # List of stakeholder names/IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    affiliation = Column(String(500), nullable=True)
    specialty = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id], primaryjoin="UserProfile.user_id == User.user_id")


# Study and Site Models for Site-Centric Workspace
class Study(Base):
    __tablename__ = "studies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(String(100), unique=True, nullable=False)  # External study identifier
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)  # 'active', 'completed', 'on_hold', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Site(Base):
    __tablename__ = "sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(String(100), unique=True, nullable=False)  # External site identifier
    name = Column(String(500), nullable=False)
    code = Column(String(100), nullable=True)  # Site code
    location = Column(String(500), nullable=True)
    principal_investigator = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)  # 'active', 'inactive', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user_associations = relationship("UserSite", back_populates="site", cascade="all, delete-orphan")


class UserSite(Base):
    __tablename__ = "user_sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    role = Column(String(50), nullable=True)  # 'principal_investigator', 'coordinator', 'monitor', etc.
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    site = relationship("Site", back_populates="user_associations")


class StudySite(Base):
    """
    Mapping table to link studies and sites.
    Allows a single site to participate in multiple studies.
    Used for study-specific workflow steps.
    """
    __tablename__ = "study_sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    study = relationship("Study", foreign_keys=[study_id])
    site = relationship("Site", foreign_keys=[site_id])
    
    __table_args__ = (
        UniqueConstraint('study_id', 'site_id', name='uq_study_site'),
        {"comment": "Maps studies to sites, enabling many-to-many relationship for study-specific workflow steps"},
    )


class UserRoleAssignment(Base):
    """
    Links users to roles (CRA, Study Manager, Medical Monitor) with specific site/study access.
    
    Access rules:
    - CRA: Has access to specific sites and studies assigned to them
    - Study Manager: Has site-level access, so all studies in assigned sites are accessible
    - Medical Monitor: Same as CRA - has access to specific sites and studies assigned
    """
    __tablename__ = "user_role_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)  # CRA, STUDY_MANAGER, or MEDICAL_MONITOR
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)  # Optional: for site-level access
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id"), nullable=True)  # Optional: for study-level access
    assigned_by = Column(String(255), nullable=True)  # User who assigned this role
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    site = relationship("Site", foreign_keys=[site_id])
    study = relationship("Study", foreign_keys=[study_id])


# Chat Models for Private AI Conversations
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    mode = Column(String(20), nullable=False, default='general')  # 'general' or 'document'
    document_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to chat document if applicable
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatDocument(Base):
    __tablename__ = "chat_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Site Status Models (Primary + History)
# ---------------------------------------------------------------------------


class PrimarySiteStatus(str, enum.Enum):
    """
    Primary site status enum – source of truth for site lifecycle.

    NOTE: Backed by the Postgres type `site_primary_status` created by
    `create_site_status_tables.py`.
    """

    UNDER_EVALUATION = "UNDER_EVALUATION"
    STARTUP = "STARTUP"
    INITIATING = "INITIATING"
    INITIATED_NOT_RECRUITING = "INITIATED_NOT_RECRUITING"
    RECRUITING = "RECRUITING"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    COMPLETED = "COMPLETED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    CLOSED = "CLOSED"


class SiteStatus(Base):
    """
    Current primary status per site.

    - Exactly one row per site (DB unique constraint on site_id)
    - Secondary statuses and milestone metadata are stored in `metadata`
    """

    __tablename__ = "site_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, unique=True)
    current_status = Column(SQLEnum(PrimarySiteStatus, name="site_primary_status"), nullable=False)
    previous_status = Column(SQLEnum(PrimarySiteStatus, name="site_primary_status"), nullable=True)
    # NOTE: attribute name cannot be `metadata` in SQLAlchemy declarative models
    # so we map to a column named "metadata" while using a different attribute.
    status_metadata = Column("metadata", JSON, nullable=True, default=dict)
    effective_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SiteStatusHistory(Base):
    """
    Immutable audit trail of all site status transitions.
    """

    __tablename__ = "site_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    status = Column(SQLEnum(PrimarySiteStatus, name="site_primary_status"), nullable=False)
    previous_status = Column(SQLEnum(PrimarySiteStatus, name="site_primary_status"), nullable=True)
    status_metadata = Column("metadata", JSON, nullable=True, default=dict)
    triggering_event = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())


class SiteProfile(Base):
    """
    Site Profile model - stores detailed site information.
    One-to-one relationship with Site.
    """
    
    __tablename__ = "site_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False, unique=True)
    site_name = Column(String(500), nullable=True)
    hospital_name = Column(String(500), nullable=True)
    pi_name = Column(String(255), nullable=True)
    pi_email = Column(String(255), nullable=True)
    pi_phone = Column(String(50), nullable=True)
    primary_contracting_entity = Column(String(500), nullable=True)
    authorized_signatory_name = Column(String(255), nullable=True)
    authorized_signatory_email = Column(String(255), nullable=True)
    authorized_signatory_title = Column(String(255), nullable=True)
    address_line_1 = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    postal_code = Column(String(50), nullable=True)
    site_coordinator_name = Column(String(255), nullable=True)
    site_coordinator_email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    site = relationship("Site", backref="profile")

    @property
    def full_address(self) -> str:
        """
        Dynamically computes the full address by combining address components.
        Missing components are ignored. Returns empty string if no components exist.
        """
        components = [
            self.address_line_1,
            self.city,
            self.state,
            self.country,
            self.postal_code
        ]
        # Filter out None, 'null', or purely whitespace components
        valid_components = [str(c).strip() for c in components if c and str(c).strip() and str(c).strip().lower() != 'null']
        
        return ", ".join(valid_components) if valid_components else ""


# ---------------------------------------------------------------------------
# Site Workflow Models
# ---------------------------------------------------------------------------

class WorkflowStepName(str, enum.Enum):
    """Workflow step names for Under Consideration stage."""
    SITE_IDENTIFICATION = "site_identification"
    CDA_EXECUTION = "cda_execution"
    FEASIBILITY = "feasibility"
    SITE_SELECTION_OUTCOME = "site_selection_outcome"


class StepStatus(str, enum.Enum):
    """Status of a workflow step."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    LOCKED = "locked"


class EnumValueType(TypeDecorator):
    """TypeDecorator that converts between Python enum instances and database enum string values."""
    impl = String
    cache_ok = True
    
    def __init__(self, enum_class, enum_type_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class
        self.enum_type_name = enum_type_name
    
    def process_bind_param(self, value, dialect):
        """Convert enum instance to its string value for database storage."""
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value.value  # Return enum value (lowercase string like "site_identification")
        # If it's already a string, return as-is
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert database string value back to enum instance."""
        if value is None:
            return None
        # Value from DB will be a string like "site_identification" (when using String as base)
        # OR it might be pre-processed by SQLAlchemy's ENUM type
        if isinstance(value, str):
            try:
                # Try to find enum member by value
                for enum_member in self.enum_class:
                    if enum_member.value == value:
                        return enum_member
                # If not found by value, try direct construction (should work for string enums)
                return self.enum_class(value)
            except ValueError:
                # If string doesn't match any enum value, return as-is
                return value
        # If it's already an enum instance, return as-is
        return value
    
    def load_dialect_impl(self, dialect):
        """Use String as base, but cast to enum type in SQL when needed."""
        # Use String as the base type - this ensures our process_result_value runs
        # We'll cast to enum type in SQL using bind_expression
        return String(50)
    
    def bind_expression(self, bindvalue):
        """Explicitly cast string value to enum type in SQL for PostgreSQL."""
        from sqlalchemy.sql import cast
        from sqlalchemy.dialects.postgresql import ENUM
        # Cast the bound parameter to the enum type so PostgreSQL accepts it
        return cast(bindvalue, ENUM(name=self.enum_type_name, create_type=False))


class SiteWorkflowStep(Base):
    """
    Workflow step state per site for sequential action-based workflows.
    
    For study-specific steps (Site Identification, CDA, Feasibility, Site Visit),
    this uses study_site_id to scope steps to a (study + site) combination.
    For other steps, site_id is used directly.
    """
    __tablename__ = "site_workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)  # Nullable for study-specific steps
    study_site_id = Column(UUID(as_uuid=True), ForeignKey("study_sites.id"), nullable=True)  # For study-specific steps
    # Use custom TypeDecorator to handle enum value conversion properly
    step_name = Column(EnumValueType(WorkflowStepName, "workflow_step_name", 50), nullable=False)
    status = Column(EnumValueType(StepStatus, "step_status", 50), nullable=False, default=StepStatus.NOT_STARTED)
    step_data = Column(JSON, nullable=True, default=dict)  # Flexible JSON storage for step-specific data
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    site = relationship("Site", foreign_keys=[site_id])
    study_site = relationship("StudySite", foreign_keys=[study_site_id])
    
    __table_args__ = (
        {"comment": "Workflow steps. Study-specific steps (site_identification, cda_execution, feasibility) use study_site_id. Others use site_id."}
    )


class DocumentCategory(str, enum.Enum):
    """Categories for site documents."""
    INVESTIGATOR_CV = "investigator_cv"
    SIGNED_CDA = "signed_cda"
    CTA = "cta"
    IRB_PACKAGE = "irb_package"
    FEASIBILITY_QUESTIONNAIRE = "feasibility_questionnaire"
    FEASIBILITY_RESPONSE = "feasibility_response"
    ONSITE_VISIT_REPORT = "onsite_visit_report"
    SITE_VISIBILITY_REPORT = "site_visibility_report"
    OTHER = "other"


class DocumentType(str, enum.Enum):
    """Type of document: sponsor-provided or site-uploaded."""
    SPONSOR = "sponsor"
    SITE = "site"


class ReviewStatus(str, enum.Enum):
    """Review status for site-uploaded documents."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Feasibility Questionnaire Custom Questions (CRM-owned)
# ---------------------------------------------------------------------------

class ProjectFeasibilityCustomQuestion(Base):
    """
    Custom feasibility questions added by users in CRM.
    These are stored in CRM DB only (not in external MongoDB).
    Linked to study/project and workflow step.
    """
    __tablename__ = "project_feasibility_custom_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id"), nullable=False)  # Links to Study
    workflow_step = Column(String(50), nullable=False, default="feasibility")
    
    # Question fields
    question_text = Column(Text, nullable=False)
    section = Column(String(255), nullable=True)  # Optional section grouping
    expected_response_type = Column(String(50), nullable=True)  # e.g., "text", "number", "yes_no"
    display_order = Column(Integer, nullable=False, default=0)  # For ordering questions
    
    # Metadata
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    study = relationship("Study", foreign_keys=[study_id])


# ---------------------------------------------------------------------------
# Feasibility Request and Response Models
# ---------------------------------------------------------------------------

class FeasibilityRequestStatus(str, enum.Enum):
    """Status of a feasibility request."""
    SENT = "sent"
    COMPLETED = "completed"


class FeasibilityRequest(Base):
    """
    Feasibility request sent to external users.
    Contains a secure token for accessing the public form.
    """
    __tablename__ = "feasibility_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_site_id = Column(UUID(as_uuid=True), ForeignKey("study_sites.id"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)  # Secure token for form access
    status = Column(String(50), nullable=False, default=FeasibilityRequestStatus.SENT.value)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    study_site = relationship("StudySite", foreign_keys=[study_site_id])
    responses = relationship("FeasibilityResponse", back_populates="request", cascade="all, delete-orphan")


class FeasibilityResponse(Base):
    """
    Response to a feasibility request.
    Stores answers to feasibility questions.
    """
    __tablename__ = "feasibility_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("feasibility_requests.id"), nullable=False)
    question_text = Column(Text, nullable=False)  # Store question text for reference
    question_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to custom question if applicable
    answer = Column(Text, nullable=False)  # Store answer as text (can be JSON for complex answers)
    section = Column(String(255), nullable=True)  # Section grouping
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("FeasibilityRequest", back_populates="responses")


class FeasibilityAttachment(Base):
    """
    Protocol Synopsis attachment for feasibility requests.
    Scoped to a (study_id + site_id) combination via study_site_id.
    """
    __tablename__ = "feasibility_attachments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_site_id = Column(UUID(as_uuid=True), ForeignKey("study_sites.id"), nullable=False, unique=True)  # One attachment per study_site
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_by = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    study_site = relationship("StudySite", foreign_keys=[study_site_id])


class SiteDocument(Base):
    """
    Document storage per site - acts as Site Master File.
    Documents persist regardless of site status changes.
    """
    __tablename__ = "site_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    # Use custom TypeDecorator to handle enum value conversion properly
    category = Column(EnumValueType(DocumentCategory, "document_category", 50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    uploaded_by = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text, nullable=True)
    # NOTE: attribute name cannot be `metadata` in SQLAlchemy declarative models
    # so we map to a column named "metadata" while using a different attribute.
    document_metadata = Column("metadata", JSON, nullable=True, default=dict)
    # New fields for sponsor/site document workflow
    document_type = Column(EnumValueType(DocumentType, "document_type", 20), nullable=True, default=DocumentType.SITE)
    review_status = Column(EnumValueType(ReviewStatus, "review_status", 20), nullable=True, default=ReviewStatus.PENDING)
    tmf_filed = Column(String(10), nullable=False, default='false')  # 'true' or 'false' as string


# ---------------------------------------------------------------------------
# Agreement Workflow Models
# ---------------------------------------------------------------------------

class AgreementStatus(str, enum.Enum):
    """Status enum for Agreement workflow."""
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    UNDER_NEGOTIATION = "UNDER_NEGOTIATION"
    READY_FOR_SIGNATURE = "READY_FOR_SIGNATURE"
    SENT_FOR_SIGNATURE = "SENT_FOR_SIGNATURE"
    EXECUTED = "EXECUTED"
    CLOSED = "CLOSED"


class CommentType(str, enum.Enum):
    """Comment type enum for Agreement comments."""
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    SYSTEM = "SYSTEM"


class TemplateType(str, enum.Enum):
    """Template type enum for StudyTemplate."""
    CDA = "CDA"
    CTA = "CTA"
    BUDGET = "BUDGET"
    OTHER = "OTHER"


class StudyTemplate(Base):
    """
    Template model for storing reusable document templates per study.
    Templates store TipTap JSON content for agreement documents.
    """
    __tablename__ = "study_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id"), nullable=False)
    template_name = Column(String(255), nullable=False)
    template_type = Column(EnumValueType(TemplateType, "template_type", 50), nullable=False)
    template_content = Column(JSON, nullable=True)  # TipTap JSON content (legacy, nullable for DOCX-only templates)
    template_file_path = Column(Text, nullable=True)  # Path to original DOCX file
    document_html = Column(Text, nullable=True)  # Legacy HTML field (deprecated, kept for migration)
    placeholder_config = Column(JSON, nullable=True)  # Configuration for placeholder editability: {"PLACEHOLDER_NAME": {"editable": true/false}}
    field_mappings = Column(JSON, nullable=True)  # Dynamic field mappings: {"PLACEHOLDER_NAME": "data_source.field_name"}
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(String(10), nullable=False, default='true')  # 'true' or 'false' as string
    
    # Relationships
    study = relationship("Study", foreign_keys=[study_id])
    agreement_documents = relationship("AgreementDocument", back_populates="template")
    
    __table_args__ = (
        {"comment": "Reusable TipTap JSON document templates for study agreements"}
    )


class Agreement(Base):
    """
    Agreement model for tracking contract/agreement workflow per site.
    """
    __tablename__ = "agreements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    # Optional StudySite join – enables explicit (study + site) mapping without removing legacy fields.
    study_site_id = Column(UUID(as_uuid=True), ForeignKey("study_sites.id"), nullable=True)
    # NEW: Explicit study scoping for agreements (Study + Site pair)
    study_id = Column(UUID(as_uuid=True), ForeignKey("studies.id"), nullable=True)
    title = Column(String(500), nullable=False)
    status = Column(EnumValueType(AgreementStatus, "agreement_status", 50), nullable=False, default=AgreementStatus.DRAFT)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_legacy = Column(String(10), nullable=False, default='false')  # 'true' or 'false' - marks old file-based agreements
    zoho_request_id = Column(String(255), nullable=True)  # Zoho Sign request ID
    signature_status = Column(String(50), nullable=True)  # 'SENT', 'COMPLETED', 'DECLINED', 'EXPIRED'
    # NEW: Agreement type (CDA / CTA / BUDGET / OTHER) for uniqueness per study+site+type
    agreement_type = Column(EnumValueType(TemplateType, "template_type", 50), nullable=True)
    
    # Relationships
    site = relationship("Site", foreign_keys=[site_id])
    study_site = relationship("StudySite", foreign_keys=[study_site_id])
    comments = relationship("AgreementComment", back_populates="agreement", primaryjoin="Agreement.id == AgreementComment.agreement_id", cascade="all, delete-orphan", order_by="AgreementComment.created_at")
    documents = relationship("AgreementDocument", back_populates="agreement", primaryjoin="Agreement.id == AgreementDocument.agreement_id", cascade="all, delete-orphan", order_by="AgreementDocument.version_number")
    signed_documents = relationship("AgreementSignedDocument", foreign_keys="AgreementSignedDocument.agreement_id", cascade="all, delete-orphan")


class AgreementComment(Base):
    """
    Comment model for Agreement discussions and system logging.
    """
    __tablename__ = "agreement_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), nullable=True)
    comment_type = Column(EnumValueType(CommentType, "comment_type", 50), nullable=False)
    content = Column(Text, nullable=False)
    created_by = Column(String(255), nullable=True)  # Nullable for system comments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agreement = relationship("Agreement", back_populates="comments", foreign_keys=[agreement_id])


class AgreementDocument(Base):
    """
    Template-based document model for Agreement.
    Stores TipTap JSON documents created from StudyTemplate.
    """
    __tablename__ = "agreement_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    document_content = Column(JSON, nullable=True)  # TipTap JSON content (legacy, nullable for DOCX-only documents)
    document_html = Column(Text, nullable=True)  # Legacy HTML field (deprecated, kept for migration)
    document_file_path = Column(Text, nullable=True)  # Path to DOCX file for ONLYOFFICE
    created_from_template_id = Column(UUID(as_uuid=True), ForeignKey("study_templates.id"), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_signed_version = Column(String(10), nullable=False, default='false')  # 'true' or 'false' as string
    
    # Relationships
    agreement = relationship("Agreement", back_populates="documents", foreign_keys=[agreement_id])
    template = relationship("StudyTemplate", back_populates="agreement_documents", foreign_keys=[created_from_template_id])
    inline_comments = relationship("AgreementInlineComment", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('agreement_id', 'version_number', name='uq_agreement_document_version'),
        {"comment": "Template-based TipTap JSON documents for agreements."}
    )


class AgreementInlineComment(Base):
    """
    Inline comment model for Agreement documents.
    Comments are attached to specific positions in TipTap documents.
    """
    __tablename__ = "agreement_inline_comments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("agreement_documents.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    position_reference = Column(JSON, nullable=True)  # TipTap position/mark reference
    comment_type = Column(EnumValueType(CommentType, "comment_type", 50), nullable=False)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agreement = relationship("Agreement", foreign_keys=[agreement_id])
    document = relationship("AgreementDocument", back_populates="inline_comments", foreign_keys=[document_id])
    
    __table_args__ = (
        {"comment": "Inline comments attached to specific positions in agreement documents"}
    )


class AgreementSignedDocument(Base):
    """
    Model for storing signed PDF documents from Zoho Sign.
    """
    __tablename__ = "agreement_signed_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path to signed PDF file
    signed_at = Column(DateTime(timezone=True), nullable=True)  # When document was signed (from Zoho)
    downloaded_from_zoho_at = Column(DateTime(timezone=True), server_default=func.now())  # When we downloaded it
    zoho_request_id = Column(String(255), nullable=True)  # Zoho Sign request ID for reference
    
    # Relationships
    agreement = relationship("Agreement", foreign_keys=[agreement_id])
    
    __table_args__ = (
        {"comment": "Signed PDF documents downloaded from Zoho Sign for agreements"}
    )