from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, date
from uuid import UUID
from app.models import MessageDirection, MessageChannel, MessageStatus, PrimarySiteStatus


class ConversationCreate(BaseModel):
    participant_phone: Optional[str] = None
    participant_email: Optional[str] = None  # Legacy: single email (will be converted to participant_emails)
    participant_emails: Optional[List[str]] = None  # Array of email addresses for multiple recipients
    subject: Optional[str] = None
    title: Optional[str] = None
    study_id: Optional[str] = None
    site_id: Optional[str] = None
    is_pinned: Optional[bool] = False
    is_restricted: Optional[bool] = False
    is_confidential: Optional[bool] = False
    created_by: Optional[str] = None
    sponsor_id: Optional[str] = None
    conversation_type: str = "notice_board"  # notice_board | thread


class ConversationResponse(BaseModel):
    id: UUID
    participant_phone: Optional[str] = None
    participant_email: Optional[str] = None  # Primary/legacy email for backward compatibility
    participant_emails: Optional[List[str]] = None  # Array of email addresses for multiple recipients
    subject: Optional[str] = None
    title: Optional[str] = None
    study_id: Optional[str] = None
    site_id: Optional[str] = None
    is_pinned: Optional[str] = 'false'
    is_restricted: Optional[str] = 'false'
    is_confidential: Optional[str] = 'false'
    created_by: Optional[str] = None
    sponsor_id: Optional[str] = None
    conversation_type: str = "notice_board"  # notice_board | thread
    access_level: Optional[str] = 'public'
    privileged_users: Optional[List[str]] = []
    tracker_code: Optional[str] = None
    # AI auto‑classification fields (stored on conversation docs in MongoDB)
    ai_category: Optional[str] = None  # ops | admission | sales | support | other
    ai_priority: Optional[str] = None  # low | medium | high | urgent
    ai_sentiment: Optional[str] = None  # negative | neutral | positive
    ai_next_best_action: Optional[str] = None
    # Persisted AI summary (conversation‑level)
    ai_summary: Optional[str] = None
    ai_summary_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    channel: MessageChannel
    body: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    direction: MessageDirection
    channel: MessageChannel
    body: str
    status: MessageStatus
    provider_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    author_id: Optional[str] = None
    author_name: Optional[str] = None
    mentioned_emails: Optional[List[str]] = []  # Email addresses mentioned via @email pattern
    origin: Optional[str] = "user"  # "user" or "system" - indicates message origin
    event_type: Optional[str] = None  # Event type for system messages (e.g., "cda_sent", "cda_signed")
    is_activity_event: Optional[bool] = False  # True for system activity events, False for user messages
    # AI per‑message analysis
    ai_tone: Optional[str] = None
    ai_delta_summary: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @staticmethod
    def _map_message(obj):
        """Map message_metadata field to metadata for response"""
        if hasattr(obj, '__dict__'):
            data = dict(obj.__dict__)
            if 'message_metadata' in data:
                data['metadata'] = data.pop('message_metadata')
            # Remove SQLAlchemy internal attributes
            data = {k: v for k, v in data.items() if not k.startswith('_')}
            return data
        return obj


class ConversationWithMessages(BaseModel):
    id: UUID
    participant_phone: Optional[str] = None
    participant_email: Optional[str] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    study_id: Optional[str] = None
    site_id: Optional[str] = None
    is_pinned: Optional[str] = 'false'
    conversation_type: str = "notice_board"  # notice_board | thread
    tracker_code: Optional[str] = None
    # Same AI fields as ConversationResponse for detail view
    ai_category: Optional[str] = None
    ai_priority: Optional[str] = None
    ai_sentiment: Optional[str] = None
    ai_next_best_action: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_summary_updated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]
    
    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    event_type: str  # "delivery" or "inbound"
    provider_message_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    channel: Optional[MessageChannel] = None
    body: Optional[str] = None
    from_number: Optional[str] = None
    from_email: Optional[str] = None
    to_number: Optional[str] = None
    to_email: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# AI‑related request/response schemas
# ---------------------------------------------------------------------------


class AIComposeReplyRequest(BaseModel):
    """Request body for /api/ai/compose-reply."""
    conversation_id: Optional[UUID] = None
    thread_id: Optional[UUID] = None
    latest_draft: Optional[str] = None


class AIComposeReplyDrafts(BaseModel):
    professional: str
    short: str
    detailed: str


class AIComposeReplyResponse(BaseModel):
    drafts: AIComposeReplyDrafts
    summary: str
    facts: List[str]


class AICheckMessageIssue(BaseModel):
    type: str
    message: str


class AICheckMessageRequest(BaseModel):
    """Request body for /api/ai/check-message."""
    conversation_id: Optional[UUID] = None
    thread_id: Optional[UUID] = None
    draft_body: str
    attachments: List[str] = []


class AICheckMessageResponse(BaseModel):
    issues: List[AICheckMessageIssue]
    okToSend: bool


class WebSocketMessage(BaseModel):
    action: str
    conversation_id: Optional[UUID] = None


class WebSocketEvent(BaseModel):
    conversation_id: UUID
    type: str
    message: Optional[Dict[str, Any]] = None


# Thread Schemas
class ThreadParticipantCreate(BaseModel):
    participant_id: str
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    role: str = "participant"


class ThreadParticipantResponse(BaseModel):
    id: UUID
    thread_id: UUID
    participant_id: str
    participant_name: Optional[str]
    participant_email: Optional[str]
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


class ThreadMessageCreate(BaseModel):
    body: str
    author_id: str
    author_name: Optional[str] = None
    message_id: Optional[UUID] = None  # Link to existing message if applicable
    message_type: Optional[str] = None  # 'system' or None (regular message)


class ThreadMessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    message_id: Optional[UUID]
    body: str
    author_id: str
    author_name: Optional[str]
    mentioned_emails: Optional[List[str]] = []  # Email addresses mentioned via @email pattern
    created_at: datetime
    message_type: Optional[str] = None  # 'system' or None (regular message)
    
    class Config:
        from_attributes = True


class CreateThreadFromConversationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    thread_type: str = Field(..., pattern="^(issue|patient|general)$")
    message_ids: List[UUID]
    created_by: Optional[str] = None
    related_study_id: Optional[str] = None
    # NEW: Thread visibility and participants for private threads
    visibility_scope: Optional[str] = Field(
        default="private",
        description="Thread visibility scope: 'private' or 'site'"
    )
    participants_emails: Optional[List[str]] = Field(
        default=None,
        description="Email-based participants to include in the thread"
    )


# Access Control Schemas
class UserCreate(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None  # For signup
    role: str = "participant"
    is_privileged: bool = False


class UserSignup(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: str
    password: str
    role: str = "participant"


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: UUID
    user_id: str
    name: Optional[str]
    email: Optional[str]
    role: str
    is_privileged: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationAccessCreate(BaseModel):
    user_id: str
    access_type: str = "read"  # 'read', 'write', 'admin'
    granted_by: Optional[str] = None


class ConversationAccessResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    user_id: str
    access_type: str
    granted_by: Optional[str]
    granted_at: datetime
    
    class Config:
        from_attributes = True


class UpdateConversationAccessRequest(BaseModel):
    is_restricted: Optional[bool] = None
    is_confidential: Optional[bool] = None
    privileged_users: Optional[List[str]] = None


class GrantAccessRequest(BaseModel):
    user_id: str
    access_type: str = "read"  # 'read', 'write', 'admin'


class UserRoleAssignmentCreate(BaseModel):
    user_id: str
    role: str  # 'cra', 'study_manager', 'medical_monitor'
    site_id: Optional[UUID] = None
    study_id: Optional[UUID] = None


class UserRoleAssignmentResponse(BaseModel):
    id: UUID
    user_id: str
    role: str
    site_id: Optional[UUID] = None
    study_id: Optional[UUID] = None
    assigned_by: Optional[str] = None
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ThreadCreate(BaseModel):
    conversation_id: Optional[UUID] = None  # Optional: threads can be created independently
    title: str
    description: Optional[str] = None
    thread_type: str = "general"  # 'issue', 'patient', 'general', 'agreement'
    related_patient_id: Optional[str] = None
    related_study_id: Optional[str] = None
    site_id: Optional[str] = None
    priority: str = "medium"  # 'low', 'medium', 'high', 'urgent'
    created_by: Optional[str] = None
    participants: Optional[List[ThreadParticipantCreate]] = []
    participants_emails: Optional[List[str]] = []  # List of participant email addresses for access control
    visibility_scope: Optional[str] = "private"  # 'private' or 'site' - controls thread visibility
    agreement_type: Optional[str] = None  # 'CDA', 'CTA', etc.


class ThreadResponse(BaseModel):
    id: UUID
    conversation_id: Union[UUID, None] = None  # Optional: threads can be independent
    title: str
    description: Optional[str]
    thread_type: str
    related_patient_id: Optional[str] = None
    related_study_id: Optional[str]
    site_id: Optional[str]
    status: str
    priority: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    participants: List[ThreadParticipantResponse] = []
    participants_emails: Optional[List[str]] = []  # List of participant email addresses for access control
    visibility_scope: Optional[str] = "private"  # 'private' or 'site' - controls thread visibility
    tmf_filed: Optional[bool] = False
    tmf_filed_at: Optional[datetime] = None
    conversation_address: Optional[str] = None
    agreement_type: Optional[str] = None  # 'CDA', 'CTA', etc.
    
    class Config:
        from_attributes = True


class ThreadWithMessages(BaseModel):
    id: UUID
    conversation_id: Union[UUID, None] = None  # Optional: threads can be independent
    title: str
    description: Optional[str]
    thread_type: str
    related_patient_id: Optional[str] = None
    related_study_id: Optional[str]
    status: str
    priority: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    participants: List[ThreadParticipantResponse] = []
    participants_emails: Optional[List[str]] = []  # List of participant email addresses for access control
    messages: List[ThreadMessageResponse] = []
    tmf_filed: Optional[bool] = False
    tmf_filed_at: Optional[datetime] = None
    conversation_address: Optional[str] = None
    agreement_type: Optional[str] = None  # 'CDA', 'CTA', etc.
    
    class Config:
        from_attributes = True


# Attachment Schemas
class AttachmentResponse(BaseModel):
    id: UUID
    message_id: Optional[UUID]
    conversation_id: UUID
    file_path: str
    content_type: str
    size: int
    checksum: Optional[str]
    uploaded_at: datetime
    file_name: Optional[str] = None  # Extracted from file_path
    
    class Config:
        from_attributes = True


class ThreadAttachmentResponse(BaseModel):
    id: UUID
    thread_id: UUID
    thread_message_id: Optional[UUID]
    attachment_id: UUID
    created_at: datetime
    attachment: Optional[AttachmentResponse] = None  # Include full attachment details
    
    class Config:
        from_attributes = True


# User Profile Schemas
class RDStudyCreate(BaseModel):
    study_title: str
    nct_number: Optional[str] = None
    asset: Optional[str] = None
    indication: Optional[str] = None
    enrollment: Optional[int] = None
    phases: Optional[str] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None


class RDStudyResponse(BaseModel):
    id: UUID
    user_id: str
    study_title: str
    nct_number: Optional[str]
    asset: Optional[str]
    indication: Optional[str]
    enrollment: Optional[int]
    phases: Optional[str]
    start_date: Optional[datetime]
    completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IISStudyCreate(BaseModel):
    study_title: str
    asset: Optional[str] = None
    indication: Optional[str] = None
    phases: Optional[str] = None
    enrollment: Optional[int] = None
    enrollment_start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    other_associated_hcp_ids: Optional[List[str]] = []


class IISStudyResponse(BaseModel):
    id: UUID
    user_id: str
    study_title: str
    asset: Optional[str]
    indication: Optional[str]
    phases: Optional[str]
    enrollment: Optional[int]
    enrollment_start_date: Optional[datetime]
    completion_date: Optional[datetime]
    other_associated_hcp_ids: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    event_name: str
    internal_external: str  # 'Internal' or 'External'
    event_type: Optional[str] = None
    date_of_event: Optional[datetime] = None
    event_description: Optional[str] = None
    event_report: Optional[str] = None
    relevant_internal_stakeholders: Optional[List[str]] = []


class EventResponse(BaseModel):
    id: UUID
    user_id: str
    event_name: str
    internal_external: str
    event_type: Optional[str]
    date_of_event: Optional[datetime]
    event_description: Optional[str]
    event_report: Optional[str]
    relevant_internal_stakeholders: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileCreate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    affiliation: Optional[str] = None
    specialty: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: UUID
    user_id: str
    name: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    affiliation: Optional[str]
    specialty: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ResearchPaperSummary(BaseModel):
    title: str
    link: str
    snippet: str
    source: Optional[str] = None


# Chat Schemas
class ChatMessageCreate(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    mode: str = "general"  # 'general' or 'document'
    document_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    id: UUID
    user_id: str
    role: str
    content: str
    mode: str
    document_id: Optional[UUID]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatDocumentResponse(BaseModel):
    id: UUID
    user_id: str
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# Thread Combination Schemas
class ThreadSimilarityAnalysis(BaseModel):
    thread1_id: UUID
    thread2_id: UUID
    should_combine: bool
    similarity_score: float
    reasoning: str
    factors: List[str]
    recommendation: str  # "strong", "moderate", "weak", "no"

class ThreadCombinationSuggestion(BaseModel):
    thread1_id: UUID
    thread2_id: UUID
    thread1_title: str
    thread2_title: str
    should_combine: bool
    similarity_score: float
    reasoning: str
    factors: List[str]
    recommendation: str

class CombineThreadsRequest(BaseModel):
    thread1_id: UUID
    thread2_id: UUID
    target_thread_id: UUID  # Which thread to keep (merge the other into this one)


# Task Schemas
class TaskLinks(BaseModel):
    siteId: Optional[str] = None
    monitoringVisitId: Optional[str] = None
    monitoringReportId: Optional[str] = None
    conversationId: Optional[str] = None
    messageId: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "open"  # 'open' | 'in-progress' | 'done' | 'cancelled'
    assigneeId: Optional[str] = None
    dueDate: Optional[date] = None
    createdByUserId: Optional[str] = None
    links: Optional[TaskLinks] = None
    # Legacy fields for backward compatibility
    siteId: Optional[str] = None
    monitoringVisitId: Optional[str] = None
    monitoringReportId: Optional[str] = None
    sourceConversationId: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigneeId: Optional[str] = None
    dueDate: Optional[date] = None
    links: Optional[TaskLinks] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    assigneeId: Optional[str] = None
    assigneeName: Optional[str] = None
    dueDate: Optional[date] = None
    createdAt: datetime
    updatedAt: datetime
    createdByUserId: Optional[str] = None
    links: Optional[TaskLinks] = None
    # Legacy fields
    siteId: Optional[str] = None
    monitoringVisitId: Optional[str] = None
    monitoringReportId: Optional[str] = None
    sourceConversationId: Optional[str] = None


# AI Task Suggestion Schemas
class AiTaskSuggestionRequest(BaseModel):
    conversationId: str
    messageId: str
    messageText: str
    recentMessages: Optional[List[Dict[str, str]]] = None  # [{"author": "...", "text": "...", "createdAt": "..."}]


class AiTaskSuggestionResponse(BaseModel):
    title: str
    description: Optional[str] = None
    suggestedStatus: str = "open"
    suggestedDueDate: Optional[str] = None  # ISO date string


# ---------------------------------------------------------------------------
# Site Status Dashboard Schemas
# ---------------------------------------------------------------------------


class UnderEvaluationMetadata(BaseModel):
    """Secondary status fields for UNDER_EVALUATION phase."""

    identified: bool
    cda_status: Literal["SENT", "SIGNED"]
    sfq_status: Literal["SENT", "RECEIVED"]
    sqv_status: Literal["SCHEDULED", "COMPLETED"]
    sqv_outcome: Literal["SELECTED", "NOT_SELECTED", "HOLD"]


class StartupMetadata(BaseModel):
    """Secondary status fields for STARTUP phase."""

    cta_status: Literal["INITIATED", "SIGNED"]
    ethics_status: Literal["NOT_SUBMITTED", "SUBMITTED", "APPROVED", "QUERY_RECEIVED", "REJECTED"]
    essential_documents_collected: bool


class InitiatingMetadata(BaseModel):
    """Secondary status fields for INITIATING phase."""

    siv_kit_dispatched: bool
    study_material_available: bool
    ip_available: bool
    non_ip_available: bool
    siv_date: date
    siv_completed: bool


class InitiatedNotRecruitingMetadata(BaseModel):
    """Secondary status fields for INITIATED_NOT_RECRUITING phase."""

    initiation_completed_at: datetime
    recruitment_blockers: List[str]


class RecruitingMetadata(BaseModel):
    """Secondary status fields for RECRUITING phase."""

    recruitment_enabled_at: datetime


class ActiveNotRecruitingMetadata(BaseModel):
    """Secondary status fields for ACTIVE_NOT_RECRUITING phase."""

    enrollment_closed_at: datetime


class CompletedMetadata(BaseModel):
    """Secondary status fields for COMPLETED phase."""

    all_subjects_completed_at: datetime


class ClosedMetadata(BaseModel):
    """Secondary status fields for CLOSED phase."""

    close_out_visit_date: date


SECONDARY_STATUS_MODELS: Dict[PrimarySiteStatus, Any] = {
    PrimarySiteStatus.UNDER_EVALUATION: UnderEvaluationMetadata,
    PrimarySiteStatus.STARTUP: StartupMetadata,
    PrimarySiteStatus.INITIATING: InitiatingMetadata,
    PrimarySiteStatus.INITIATED_NOT_RECRUITING: InitiatedNotRecruitingMetadata,
    PrimarySiteStatus.RECRUITING: RecruitingMetadata,
    PrimarySiteStatus.ACTIVE_NOT_RECRUITING: ActiveNotRecruitingMetadata,
    PrimarySiteStatus.COMPLETED: CompletedMetadata,
    PrimarySiteStatus.CLOSED: ClosedMetadata,
    # SUSPENDED and TERMINATED deliberately have no extra metadata schema
}


def validate_site_status_metadata(
    status: PrimarySiteStatus,
    raw_metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate secondary status metadata for a given primary status.

    Uses strict Pydantic schemas that mirror the clinical trial definition
    (e.g. CDA/SFQ/SQV milestones, ethics/CTA, SIV, recruitment, close‑out).
    Raises ValidationError on invalid shapes or values.
    """

    if raw_metadata is None:
        raw_metadata = {}

    model = SECONDARY_STATUS_MODELS.get(status)
    if model is None:
        # No structured schema for this status (e.g. SUSPENDED, TERMINATED)
        # Still ensure JSON-serialisable by forcing a shallow copy.
        return dict(raw_metadata)

    try:
        obj = model(**raw_metadata)
    except ValidationError as exc:
        # Re-raise so callers can turn this into a 4xx or audit event.
        raise exc
    return obj.model_dump()


class SiteStatusHistoryEntry(BaseModel):
    status: PrimarySiteStatus
    previous_status: Optional[PrimarySiteStatus] = None
    metadata: Optional[Dict[str, Any]] = None
    changed_at: datetime
    triggering_event: Optional[str] = None
    reason: Optional[str] = None


class SiteStatusDetail(BaseModel):
    site_id: str  # internal UUID
    site_external_id: Optional[str] = None
    study_id: Optional[str] = None  # Study.study_id string
    name: str
    country: Optional[str] = None
    current_status: Optional[PrimarySiteStatus] = None
    previous_status: Optional[PrimarySiteStatus] = None
    secondary_statuses: Optional[Dict[str, Any]] = None
    history: List[SiteStatusHistoryEntry] = []


class CountryStatusSummary(BaseModel):
    country: str
    status: Optional[PrimarySiteStatus] = None
    total_sites: int
    recruiting_sites: int
    status_counts: Dict[PrimarySiteStatus, int]


class WorkflowStepResponse(BaseModel):
    step_name: str
    status: str
    step_data: Optional[Dict[str, Any]] = {}
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkflowStepsResponse(BaseModel):
    site_id: str
    steps: List[WorkflowStepResponse]


class WorkflowStepUpdate(BaseModel):
    status: Optional[str] = None
    step_data: Optional[Dict[str, Any]] = None


class SiteDocumentResponse(BaseModel):
    id: UUID
    site_id: str
    category: str
    file_name: str
    content_type: str
    size: int
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    document_type: Optional[str] = None  # "sponsor" | "site"
    review_status: Optional[str] = None  # "pending" | "approved" | "rejected"
    tmf_filed: Optional[str] = "false"  # "true" | "false"


class SiteProfileCreate(BaseModel):
    """Schema for creating a site profile."""
    site_name: Optional[str] = None
    hospital_name: Optional[str] = None
    pi_name: Optional[str] = None
    pi_email: Optional[str] = None
    pi_phone: Optional[str] = None
    primary_contracting_entity: Optional[str] = None
    authorized_signatory_name: Optional[str] = None
    authorized_signatory_email: Optional[str] = None
    authorized_signatory_title: Optional[str] = None
    address_line_1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    site_coordinator_name: Optional[str] = None
    site_coordinator_email: Optional[str] = None


class SiteProfileUpdate(BaseModel):
    """Schema for updating a site profile."""
    site_name: Optional[str] = None
    hospital_name: Optional[str] = None
    pi_name: Optional[str] = None
    pi_email: Optional[str] = None
    pi_phone: Optional[str] = None
    primary_contracting_entity: Optional[str] = None
    authorized_signatory_name: Optional[str] = None
    authorized_signatory_email: Optional[str] = None
    authorized_signatory_title: Optional[str] = None
    address_line_1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    site_coordinator_name: Optional[str] = None
    site_coordinator_email: Optional[str] = None


class SiteProfileResponse(BaseModel):
    """Schema for site profile response."""
    id: UUID
    site_id: UUID
    site_name: Optional[str] = None
    hospital_name: Optional[str] = None
    pi_name: Optional[str] = None
    pi_email: Optional[str] = None
    pi_phone: Optional[str] = None
    primary_contracting_entity: Optional[str] = None
    authorized_signatory_name: Optional[str] = None
    authorized_signatory_email: Optional[str] = None
    authorized_signatory_title: Optional[str] = None
    address_line_1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    site_coordinator_name: Optional[str] = None
    site_coordinator_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StudyStatusSummary(BaseModel):
    study_id: str  # Study.study_id external identifier
    study_name: str
    study_status: Optional[PrimarySiteStatus] = None
    total_sites: int
    recruiting_sites: int
    status_counts: Dict[PrimarySiteStatus, int]
    countries: List[CountryStatusSummary]


# ---------------------------------------------------------------------------
# Feasibility Questionnaire Schemas
# ---------------------------------------------------------------------------

class FeasibilityQuestion(BaseModel):
    """Single question in a feasibility questionnaire."""
    text: str = Field(..., description="Question text")
    section: Optional[str] = Field(None, description="Section name for grouping")
    type: str = Field(..., description="Expected response type (e.g., 'text', 'number', 'yes_no')")
    source: str = Field(..., description="Source: 'external' (from MongoDB) or 'custom' (CRM-added)")
    criterion_reference: Optional[str] = Field(None, description="Reference to criterion/source document")
    display_order: Optional[int] = Field(0, description="Display order for sorting")
    id: Optional[UUID] = Field(None, description="Question ID (only for custom questions)")


class FeasibilityQuestionnaireResponse(BaseModel):
    """Response containing merged external and custom questions."""
    project_id: str = Field(..., description="Project/Study ID")
    questions: List[FeasibilityQuestion] = Field(default_factory=list, description="Merged list of questions")


class CustomQuestionCreate(BaseModel):
    """Schema for creating a custom feasibility question."""
    study_id: Union[UUID, str]  # Accept UUID or study_id/name string
    question_text: str
    section: Optional[str] = None
    expected_response_type: Optional[str] = "text"
    display_order: Optional[int] = 0


class CustomQuestionUpdate(BaseModel):
    """Schema for updating a custom feasibility question."""
    question_text: Optional[str] = None
    section: Optional[str] = None
    expected_response_type: Optional[str] = None
    display_order: Optional[int] = None


class CustomQuestionResponse(BaseModel):
    """Response schema for custom question."""
    id: UUID
    study_id: UUID
    workflow_step: str
    question_text: str
    section: Optional[str] = None
    expected_response_type: Optional[str] = None
    display_order: int
    created_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Feasibility Request and Response Schemas
# ---------------------------------------------------------------------------

class FeasibilityRequestCreate(BaseModel):
    """Schema for creating a feasibility request."""
    study_site_id: UUID
    email: Optional[str] = Field(None, description="Email address to send the form link to. If not provided, uses FEASIBILITY_DEFAULT_EMAIL from environment.")
    expires_in_days: Optional[int] = Field(30, description="Number of days until token expires")


class FeasibilityRequestResponse(BaseModel):
    """Response schema for feasibility request."""
    id: UUID
    study_site_id: UUID
    email: str
    token: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class FeasibilityFormQuestion(BaseModel):
    """Question schema for the public form."""
    text: str
    section: Optional[str] = None
    type: str
    id: Optional[UUID] = None
    display_order: Optional[int] = 0


class FeasibilityFormResponse(BaseModel):
    """Response schema for the public form (questions + study/site info)."""
    request_id: UUID
    study_name: str
    site_name: str
    questions: List[FeasibilityFormQuestion]
    protocol_synopsis: Optional["FeasibilityAttachmentResponse"] = None


class FeasibilityAnswerSubmit(BaseModel):
    """Schema for submitting a single answer."""
    question_text: str
    question_id: Optional[UUID] = None
    answer: str
    section: Optional[str] = None


class FeasibilityFormSubmit(BaseModel):
    """Schema for submitting the complete form."""
    token: str
    answers: List[FeasibilityAnswerSubmit]


class FeasibilityResponseDisplay(BaseModel):
    """Schema for displaying a response."""
    id: UUID
    question_text: str
    answer: str
    section: Optional[str] = None
    created_at: datetime


class FeasibilityResponsesDisplay(BaseModel):
    """Schema for displaying all responses for a study_site."""
    study_site_id: UUID
    request_id: UUID
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    responses: List[FeasibilityResponseDisplay]
    
    class Config:
        from_attributes = True


class FeasibilityAttachmentResponse(BaseModel):
    """Schema for feasibility attachment."""
    id: UUID
    study_site_id: UUID
    file_name: str
    file_path: str
    content_type: str
    size: int
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# Resolve forward reference
FeasibilityFormResponse.model_rebuild()


# ---------------------------------------------------------------------------
# Study Template Schemas
# ---------------------------------------------------------------------------

class StudyTemplateCreate(BaseModel):
    """Schema for creating a study template."""
    study_id: UUID
    template_name: str
    template_type: str  # TemplateType enum value
    template_content: dict  # TipTap JSON content


class StudyTemplateResponse(BaseModel):
    """Schema for study template response."""
    id: UUID
    study_id: UUID
    template_name: str
    template_type: str
    template_content: Optional[dict] = None  # TipTap JSON content (legacy, nullable for DOCX-only templates)
    template_file_path: Optional[str] = None  # Path to DOCX file
    placeholder_config: Optional[Dict[str, Dict[str, bool]]] = None  # Placeholder editability config
    field_mappings: Optional[Dict[str, str]] = None  # Dynamic field mappings: {"PLACEHOLDER_NAME": "data_source.field_name"}
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: str  # 'true' or 'false'
    
    class Config:
        from_attributes = True


class PlaceholderConfigUpdate(BaseModel):
    """Schema for updating placeholder configuration."""
    placeholder_config: Dict[str, Dict[str, bool]]  # {"PLACEHOLDER_NAME": {"editable": true/false}}


class FieldMappingsUpdate(BaseModel):
    """Schema for updating field mappings."""
    field_mappings: Dict[str, str]  # {"PLACEHOLDER_NAME": "data_source.field_name"}


# ---------------------------------------------------------------------------
# Agreement Workflow Schemas
# ---------------------------------------------------------------------------

class AgreementDocumentResponse(BaseModel):
    """Schema for agreement document response."""
    id: UUID
    agreement_id: UUID
    version_number: int
    document_content: Optional[dict] = None  # TipTap JSON content (legacy, nullable for DOCX-only documents)
    document_file_path: Optional[str] = None  # Path to DOCX file for ONLYOFFICE
    created_from_template_id: Optional[UUID] = None
    created_by: Optional[str] = None
    created_at: datetime
    is_signed_version: str  # 'true' or 'false'
    
    class Config:
        from_attributes = True


class AgreementCommentResponse(BaseModel):
    """Schema for agreement comment response."""
    id: UUID
    agreement_id: UUID
    version_id: Optional[UUID] = None
    comment_type: str  # CommentType enum value
    content: str
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgreementSignedDocumentResponse(BaseModel):
    """Schema for signed document response."""
    id: UUID
    agreement_id: UUID
    file_path: Optional[str] = None
    signed_at: Optional[datetime] = None
    downloaded_from_zoho_at: Optional[datetime] = None
    zoho_request_id: Optional[str] = None
    
    class Config:
        from_attributes = True




class AgreementCreate(BaseModel):
    """Schema for creating a new agreement."""
    title: str
    status: str  # AgreementStatus enum value
    template_id: Optional[UUID] = None  # Required for new agreements


class AgreementStatusUpdate(BaseModel):
    """Schema for updating agreement status."""
    status: str  # AgreementStatus enum value


class AgreementCommentCreate(BaseModel):
    """Schema for creating an agreement comment."""
    comment_type: str  # CommentType enum value (INTERNAL, EXTERNAL)
    content: str
    version_id: Optional[UUID] = None  # Optional: attach to specific version


class DocumentSaveRequest(BaseModel):
    """Schema for saving document content."""
    document_content: dict  # TipTap JSON content


class AgreementResponse(BaseModel):
    """Schema for agreement response."""
    id: UUID
    site_id: UUID
    title: str
    status: str  # AgreementStatus enum value
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_legacy: str  # 'true' or 'false'
    documents: List[AgreementDocumentResponse] = []
    comments: List[AgreementCommentResponse] = []
    can_upload_new_version: bool = False
    can_edit: bool = False
    can_comment: bool = False
    can_save: bool = False
    can_move_status: bool = False
    is_locked: bool = False
    current_document_version_number: Optional[int] = None
    zoho_request_id: Optional[str] = None
    signature_status: Optional[str] = None
    signed_documents: List[AgreementSignedDocumentResponse] = []
    
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Agreement Workflow Schemas
# ---------------------------------------------------------------------------
