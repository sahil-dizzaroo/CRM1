from app.workers.celery_app import celery_app
from app.workers.provider import MockProvider
from app.db import AsyncSessionLocal, engine
from app import crud
from app.models import MessageStatus, MessageDirection, MessageChannel
from app.config import settings
from app.websocket_manager import manager
from app.ai_service import ai_service

from app.repositories.mongo_repository import (
    ConversationRepository,
    MessageRepository,
    ThreadRepository,
    ThreadMessageRepository,
)

from datetime import datetime, timezone
from uuid import UUID
import asyncio
import re
import logging

logger = logging.getLogger(__name__)
provider = MockProvider()


# -------------------------------------------------
# Async runner (Celery-safe)
# -------------------------------------------------
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(coro)

    # ✅ dispose SQLAlchemy connections ONLY
    loop.run_until_complete(engine.dispose())

    return result


# -------------------------------------------------
# Timeout helper for async operations
# -------------------------------------------------
async def with_timeout(coro, timeout=10, default=None, operation_name="operation"):
    """Wrap async operations with timeout to prevent hanging."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"{operation_name} timed out after {timeout}s")
        return default
    except Exception as e:
        logger.error(f"{operation_name} failed: {e}")
        return default



# =================================================
# OUTBOUND MESSAGE TASK
# =================================================
@celery_app.task
def send_message_task(message_id: str, source_type: str = "conversation"):
    async def _send():
        async with AsyncSessionLocal() as db:
            # Load source-specific message + context while reusing one delivery pipeline.
            msg = None
            context = None
            is_email_send = False
            if source_type == "thread":
                msg = await with_timeout(
                    ThreadMessageRepository.get_by_id(UUID(message_id)),
                    timeout=5,
                    default=None,
                    operation_name="Get thread message for sending",
                )
                if not msg:
                    logger.warning(f"Thread message {message_id} not found")
                    return
                context = await with_timeout(
                    ThreadRepository.get_by_id(msg["thread_id"]),
                    timeout=5,
                    default=None,
                    operation_name="Get thread for sending",
                )
                if not context:
                    logger.warning(f"Thread {msg['thread_id']} not found")
                    return
                is_email_send = True
            else:
                msg = await with_timeout(
                    crud.get_message(db, UUID(message_id)),
                    timeout=5,
                    default=None,
                    operation_name="Get message for sending",
                )
                if not msg:
                    logger.warning(f"Message {message_id} not found")
                    return
                context = await with_timeout(
                    crud.get_conversation(db, msg["conversation_id"]),
                    timeout=5,
                    default=None,
                    operation_name="Get conversation for sending",
                )
                if not context:
                    logger.warning(f"Conversation {msg['conversation_id']} not found")
                    return
                channel = msg.get("channel")
                if isinstance(channel, str):
                    channel = MessageChannel(channel)
                is_email_send = channel == MessageChannel.EMAIL

            if is_email_send:
                # Mention-only delivery for both conversation and thread sources.
                mentioned_emails = msg.get("mentioned_emails", [])
                recipient_emails = []
                seen = set()
                for email in mentioned_emails or []:
                    normalized = str(email).strip().lower()
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        recipient_emails.append(normalized)

                if not recipient_emails:
                    logger.info(f"📧 Message {message_id} has no valid @email mentions - skipping email send")
                    if source_type == "thread":
                        await with_timeout(
                            ThreadMessageRepository.update_fields(
                                UUID(message_id),
                                {
                                    "status": MessageStatus.DELIVERED.value,
                                    "delivered_at": datetime.now(timezone.utc),
                                },
                            ),
                            timeout=5,
                            default=None,
                            operation_name="Update thread message status to DELIVERED (no email sent)",
                        )
                    else:
                        await with_timeout(
                            crud.update_message_status(
                                db,
                                UUID(message_id),
                                MessageStatus.DELIVERED,
                                sent_at=None,
                            ),
                            timeout=5,
                            default=None,
                            operation_name="Update message status to DELIVERED (no email sent)",
                        )
                    return

                logger.info(f"📧 Final recipient list: {recipient_emails} (count: {len(recipient_emails)})")

                smtp_user = settings.smtp_user or ""
                smtp_domain = smtp_user.split("@")[1] if "@" in smtp_user else "dizzaroo.com"

                # Build from_email address
                if context.get("study_id") and context.get("site_id"):
                    # Raw values from conversation (e.g. "MK-6547", "site01", "001")
                    study_id_raw = str(context["study_id"]).strip()
                    site_id_raw = str(context["site_id"]).strip()

                    # Strip leading "study"/"site" *only* for numeric IDs
                    study_core = re.sub(r"^study+", "", study_id_raw, flags=re.IGNORECASE)
                    site_core = re.sub(r"^site+", "", site_id_raw, flags=re.IGNORECASE)

                    study_is_numeric = study_core.isdigit()
                    site_is_numeric = site_core.isdigit()

                    if study_is_numeric and site_is_numeric:
                        # Numeric IDs: keep explicit prefixes so pattern is stable
                        local_part = f"study{study_core}site{site_core}"
                    else:
                        # Text / mixed IDs: concatenate cleaned study + cleaned site
                        # Examples:
                        #   study_id="MK-6547", site_id="site01" -> "mk6547site01"
                        #   study_id="New study", site_id="site01" -> "newstudysite01"
                        study_clean = re.sub(r"[^a-z0-9]+", "", study_id_raw.lower())
                        site_clean = re.sub(r"[^a-z0-9]+", "", site_id_raw.lower())
                        combined = f"{study_clean}{site_clean}"
                        local_part = combined or "noreply"

                    from_email = f"{local_part}@{smtp_domain}"
                else:
                    from_email = f"noreply@{smtp_domain}"

                subject = context.get("subject") or context.get("title") or "Message from Clinical Trials CRM"
                raw_body = msg.get("body") or ""
                # Remove @email mentions from the outbound email body; mentions are for routing only.
                body = re.sub(r'@([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', '', raw_body)
                body = re.sub(r'[ \t]{2,}', ' ', body)
                body = re.sub(r'\n{3,}', '\n\n', body).strip()
                if not body:
                    body = "Message sent"

                tracker = context.get("tracker_code")
                if tracker and tracker not in subject:
                    subject = f"{subject} [{tracker}]"

                from app.services.smtp_service import smtp_service
                try:
                    # Send to all recipients (can be single string or list)
                    result = smtp_service.send_email(
                        to=recipient_emails,
                        subject=subject,
                        body=body,
                        from_email=from_email,
                        from_name="Clinical Trials CRM",
                    )
                except Exception as e:
                    logger.error(f"SMTP send_email raised exception: {e}")
                    result = {"success": False, "error": str(e)}

                if result.get("success"):
                    if source_type == "thread":
                        await with_timeout(
                            ThreadMessageRepository.update_fields(
                                UUID(message_id),
                                {
                                    "status": MessageStatus.SENT.value,
                                    "provider_message_id": result.get("message_id"),
                                    "sent_at": datetime.now(timezone.utc),
                                },
                            ),
                            timeout=5,
                            default=None,
                            operation_name="Update thread message status to SENT",
                        )
                    else:
                        await with_timeout(
                            crud.update_message_status(
                                db,
                                UUID(message_id),
                                MessageStatus.SENT,
                                provider_message_id=result.get("message_id"),
                                sent_at=datetime.now(timezone.utc),
                            ),
                            timeout=5,
                            default=None,
                            operation_name="Update message status to SENT",
                        )
                        # Publish event with timeout
                        await with_timeout(
                            manager.publish_event(
                                context["id"],
                                {
                                    "type": "message_status",
                                    "message_id": message_id,
                                    "status": "sent",
                                },
                            ),
                            timeout=3,
                            default=None,
                            operation_name="Publish message status event",
                        )
                    return

                if source_type == "thread":
                    await with_timeout(
                        ThreadMessageRepository.update_fields(
                            UUID(message_id),
                            {"status": MessageStatus.FAILED.value},
                        ),
                        timeout=5,
                        default=None,
                        operation_name="Update thread message status to FAILED",
                    )
                else:
                    await with_timeout(
                        crud.update_message_status(db, UUID(message_id), MessageStatus.FAILED),
                        timeout=5,
                        default=None,
                        operation_name="Update message status to FAILED",
                    )
                return

            # ---------------- NON-EMAIL (MOCK) ----------------
            provider_id = provider.send(
                channel=channel,
                to=context.get("participant_phone"),
                body=msg.get("body"),
            )

            await with_timeout(
                crud.update_message_status(
                    db,
                    UUID(message_id),
                    MessageStatus.SENT,
                    provider_message_id=provider_id,
                    sent_at=datetime.now(timezone.utc),
                ),
                timeout=5,
                default=None,
                operation_name="Update message status to SENT (non-email)"
            )

    run_async(_send())


# =================================================
# AI PROCESSING TASK (BACKGROUND)
# =================================================
@celery_app.task
def process_message_ai_task(message_id: str, conversation_id: str, message_body: str):
    """Process AI analysis for a message in the background without blocking the request."""
    async def _process_ai():
        try:
            if not ai_service.is_available():
                logger.info("AI service not available, skipping AI processing")
                return

            from app.repositories import MessageRepository, ConversationRepository
            
            # Get conversation with timeout
            conv = await with_timeout(
                ConversationRepository.get_by_id(UUID(conversation_id)),
                timeout=5,
                default=None,
                operation_name="Get conversation for AI"
            )
            if not conv:
                logger.warning(f"Conversation {conversation_id} not found for AI processing")
                return

            # Load recent messages with timeout
            history = await with_timeout(
                MessageRepository.list_by_conversation(UUID(conversation_id), limit=50, offset=0),
                timeout=5,
                default=[],
                operation_name="Load message history for AI"
            )

            if history:
                latest = history[0]
                older = history[1:]
                history_text = ai_service._format_messages_for_summary(older[::-1])  # oldest->newest
                
                # Analyze new message with timeout
                analysis = await with_timeout(
                    ai_service.analyse_new_message(history_text, latest.get('body', '')),
                    timeout=10,
                    default=None,
                    operation_name="AI message analysis"
                )
                if analysis:
                    await with_timeout(
                        MessageRepository.update_fields(latest.get('id'), {
                            'ai_tone': analysis.get('tone'),
                            'ai_delta_summary': analysis.get('delta_summary'),
                        }),
                        timeout=5,
                        default=None,
                        operation_name="Update message AI fields"
                    )

            # Auto-classify conversation and refresh summary with timeouts
            messages_text = ai_service._format_messages_for_summary(history[::-1] if history else [])
            
            classification = await with_timeout(
                ai_service.classify_conversation(messages_text or "", message_body),
                timeout=10,
                default=None,
                operation_name="AI conversation classification"
            )
            
            summary = await with_timeout(
                ai_service.summarize_conversation(conv, history[::-1] if history else []),
                timeout=10,
                default=None,
                operation_name="AI conversation summary"
            )
            
            updates = {}
            if classification:
                updates.update(classification)
            if summary:
                updates['ai_summary'] = summary
                updates['ai_summary_updated_at'] = datetime.now(timezone.utc)
            
            if updates:
                await with_timeout(
                    ConversationRepository.update(UUID(conversation_id), updates),
                    timeout=5,
                    default=None,
                    operation_name="Update conversation AI fields"
                )
                
            logger.info(f"✅ AI processing completed for message {message_id}")
        except Exception as e:
            logger.error(f"AI processing failed for message {message_id}: {e}", exc_info=True)

    run_async(_process_ai())


# =================================================
# INBOUND MAILGUN WEBHOOK TASK
# =================================================
@celery_app.task
def process_webhook_task(payload: dict):
    async def _process():
        async with AsyncSessionLocal() as db:

            if payload.get("event_type") != "inbound":
                return

            recipient = payload.get("recipient")
            sender = payload.get("sender")

            body = (
                payload.get("stripped_text")
                or payload.get("body_plain")
                or payload.get("stripped_html")
                or ""
            )

            logger.warning("📩 Inbound email received")
            logger.warning(f"   From: {sender}")
            logger.warning(f"   To: {recipient}")
            logger.warning(f"   Body preview: {body[:200]}")

            if not recipient:
                logger.warning("Missing recipient")
                return

            # Parse study and site IDs from email alias
            # Handles formats: study1site1@, studystudy1sitesite1@, study-1-site-2@, etc.
            local_part = recipient.split("@")[0] if "@" in recipient else recipient
            local_part_norm = re.sub(r"[^a-z0-9]+", "", local_part.lower())
            study_id = None
            site_id = None
            
            # Try multiple patterns
            # Pattern 1: study1site1@ or studystudy1sitesite1@
            match1 = re.search(r"study(?:study)?(\d+)site(?:site)?(\d+)", local_part, re.IGNORECASE)
            if match1:
                study_id, site_id = match1.groups()
            else:
                # Pattern 2: study-1-site-2@ or study_1_site_2@
                match2 = re.search(r"study[-_]?(\d+)[-_]?site[-_]?(\d+)", local_part, re.IGNORECASE)
                if match2:
                    study_id, site_id = match2.groups()
                else:
                    # Pattern 3: Extract any digits after "study" and "site" (fallback for unusual formats)
                    study_match = re.search(r"study.*?(\d+)", local_part, re.IGNORECASE)
                    site_match = re.search(r"site.*?(\d+)", local_part, re.IGNORECASE)
                    if study_match and site_match:
                        study_id = study_match.group(1)
                        site_id = site_match.group(1)

            # Pattern 4: compact alias format generated by outbound sender
            # Example: ASLAN001-009 + site01 => aslan001009site01
            if not study_id or not site_id:
                match4 = re.search(r"^(.+?)site(\d+)$", local_part_norm, re.IGNORECASE)
                if match4:
                    study_id = match4.group(1)
                    site_id = f"site{match4.group(2)}"
            
            if not study_id or not site_id:
                logger.warning(f"Invalid alias format: {recipient} (could not extract study_id and site_id)")
                return
            
            logger.info(f"Parsed from {recipient}: study_id={study_id}, site_id={site_id}")

            # -------- Mongo lookup (system-level) --------
            from app.db_mongo import get_mongo_db
            mongo = await with_timeout(
                get_mongo_db(),
                timeout=5,
                default=None,
                operation_name="Get MongoDB connection"
            )
            if mongo is None:
                logger.error("Failed to get MongoDB connection, aborting webhook processing")
                return

            # Try multiple formats: parsed values might be "1" but DB has "study1" and "site1"
            # Format 1: Try with parsed values as-is
            conv_doc = await with_timeout(
                mongo["conversations"].find_one(
                    {"study_id": study_id, "site_id": site_id},
                    sort=[("updated_at", -1)],
                ),
                timeout=5,
                default=None,
                operation_name="Find conversation in MongoDB (format 1)"
            )
            
            # Format 2: Try with "study" and "site" prefixes
            if not conv_doc:
                conv_doc = await with_timeout(
                    mongo["conversations"].find_one(
                        {"study_id": f"study{study_id}", "site_id": f"site{site_id}"},
                        sort=[("updated_at", -1)],
                    ),
                    timeout=5,
                    default=None,
                    operation_name="Find conversation in MongoDB (format 2)"
                )
            
            # Format 3: Try with just study_id matching (any site)
            if not conv_doc:
                conv_doc = await with_timeout(
                    mongo["conversations"].find_one(
                        {"study_id": f"study{study_id}"},
                        sort=[("updated_at", -1)],
                    ),
                    timeout=5,
                    default=None,
                    operation_name="Find conversation in MongoDB (format 3)"
                )

            # Format 4: Alias-local-part exact reconstruction fallback.
            # This handles non-numeric study IDs (e.g., ASLAN001-009).
            if not conv_doc:
                def _norm(v: str) -> str:
                    return re.sub(r"[^a-z0-9]+", "", str(v or "").lower())

                def _build_local_alias(study_raw: str, site_raw: str) -> str:
                    study_raw = str(study_raw or "").strip()
                    site_raw = str(site_raw or "").strip()
                    study_core = re.sub(r"^study+", "", study_raw, flags=re.IGNORECASE)
                    site_core = re.sub(r"^site+", "", site_raw, flags=re.IGNORECASE)
                    if study_core.isdigit() and site_core.isdigit():
                        return f"study{study_core}site{site_core}".lower()
                    return f"{_norm(study_raw)}{_norm(site_raw)}" or "noreply"

                candidates = await with_timeout(
                    mongo["conversations"]
                    .find({}, {"id": 1, "study_id": 1, "site_id": 1, "updated_at": 1})
                    .sort([("updated_at", -1)])
                    .limit(500)
                    .to_list(length=500),
                    timeout=8,
                    default=[],
                    operation_name="Find conversation in MongoDB (format 4 alias fallback)",
                )

                for candidate in candidates:
                    if _build_local_alias(
                        candidate.get("study_id"), candidate.get("site_id")
                    ) == local_part_norm:
                        conv_doc = candidate
                        break

            if not conv_doc:
                logger.warning(
                    f"No conversation found for study={study_id}, site={site_id} (tried formats: '{study_id}'/'{site_id}', 'study{study_id}'/'site{site_id}', 'study{study_id}'/any). Inbound email will not be processed."
                )
                return
            
            logger.info(f"✅ Found conversation: {conv_doc.get('id')} for study={study_id}, site={site_id}")

            conversation = ConversationRepository._normalize_doc(conv_doc)
            
            # Verify sender email matches any recipient email in the conversation
            participant_emails = conversation.get("participant_emails") or []
            participant_email = conversation.get("participant_email")
            
            # Build list of all valid recipient emails
            all_recipient_emails = []
            if participant_emails:
                all_recipient_emails.extend([email.lower().strip() if email else None for email in participant_emails])
            if participant_email:
                all_recipient_emails.append(participant_email.lower().strip())
            
            # Remove None/empty values and normalize
            all_recipient_emails = [email for email in all_recipient_emails if email]
            
            # Check if sender matches any recipient (case-insensitive)
            sender_normalized = sender.lower().strip() if sender else ""
            if all_recipient_emails and sender_normalized not in all_recipient_emails:
                logger.warning(
                    f"Sender email '{sender}' does not match any recipient in conversation {conversation.get('id')}. "
                    f"Recipients: {all_recipient_emails}. Email will still be processed."
                )
                # Note: We continue processing even if there's no match, as the conversation was found by study_id/site_id
            
            conv_id_str = conversation["id"]
            
            # Convert conv_id to UUID if it's a string
            if isinstance(conv_id_str, str):
                try:
                    conv_id = UUID(conv_id_str)
                except ValueError:
                    logger.error(f"Invalid conversation ID format: {conv_id_str}")
                    return
            else:
                conv_id = conv_id_str

            # -------- Create inbound message --------
            from app.schemas import MessageCreate

            msg_create = MessageCreate(
                channel=MessageChannel.EMAIL,
                body=body,
                metadata={
                    "subject": payload.get("subject"),
                    "from": sender,
                },
            )

            try:
                db_msg = await with_timeout(
                    crud.create_message(
                        db,
                        conv_id,
                        msg_create,
                        MessageDirection.INBOUND,
                        author_id=sender,
                        author_name=sender,
                    ),
                    timeout=5,
                    default=None,
                    operation_name="Create inbound message"
                )
                if not db_msg:
                    logger.error("Failed to create inbound message (timeout or error)")
                    return
                msg_id = db_msg.get('id') if isinstance(db_msg, dict) else db_msg.id
                msg_body = db_msg.get('body') if isinstance(db_msg, dict) else db_msg.body
                msg_created_at = db_msg.get('created_at') if isinstance(db_msg, dict) else db_msg.created_at
                msg_conv_id = db_msg.get('conversation_id') if isinstance(db_msg, dict) else db_msg.conversation_id
                logger.info(f"✅ Created inbound message: {msg_id} for conversation: {conv_id} (stored as: {msg_conv_id})")
            except Exception as e:
                logger.error(f"Exception creating inbound message: {e}", exc_info=True)
                return

            # Publish WebSocket event
            try:
                created_at_str = msg_created_at.isoformat() if hasattr(msg_created_at, 'isoformat') else str(msg_created_at)
                await with_timeout(
                    manager.publish_event(
                        conv_id,
                        {
                            "type": "new_message",
                            "conversation_id": str(conv_id),
                            "message": {
                                "id": str(msg_id),
                                "direction": "inbound",
                                "channel": "email",
                                "body": msg_body,
                                "author_id": sender,
                                "author_name": sender,
                                "created_at": created_at_str,
                            },
                        },
                    ),
                    timeout=3,
                    default=None,
                    operation_name="Publish inbound message event"
                )
                logger.info(f"✅ WebSocket event published for message: {msg_id}")
            except Exception as e:
                logger.error(f"Failed to publish WebSocket event: {e}", exc_info=True)
                # Don't fail the whole process if WebSocket fails

            logger.warning("✅ Inbound email saved & broadcast")

            # =================================================
            # AI PROCESSING (ASYNC, SAFE, OPTIONAL) - WITH TIMEOUTS
            # =================================================
            try:
                if ai_service.is_available():
                    history = await with_timeout(
                        MessageRepository.list_by_conversation(conv_id, limit=50),
                        timeout=5,
                        default=[],
                        operation_name="Load message history for inbound AI"
                    )

                    if history:
                        summary = await with_timeout(
                            ai_service.summarize_conversation(conversation, history[::-1]),
                            timeout=10,
                            default=None,
                            operation_name="AI summarize conversation (inbound)"
                        )

                        if summary:
                            await with_timeout(
                                ConversationRepository.update(
                                    conv_id,
                                    {
                                        "ai_summary": summary,
                                        "ai_summary_updated_at": datetime.now(timezone.utc),
                                    },
                                ),
                                timeout=5,
                                default=None,
                                operation_name="Update conversation summary (inbound)"
                            )

            except Exception as e:
                logger.warning(f"AI processing failed: {e}")

    run_async(_process())
