"""
AI Service for Gemini API integration.

Existing responsibilities:
- Conversation and thread summarisation.

New responsibilities (extended, but backwards‑compatible):
- AI compose assist (draft replies + summary + key facts)
- Conversation auto‑classification (category/priority/sentiment/next best action)
- Per‑message analysis (tone + delta summary)
- Pre‑send message checks (missing info / attachments)
"""
import google.generativeai as genai
import asyncio
import json
from typing import Optional, List, Dict, Any
from app.config import settings
from app.models import Conversation, Message, Thread, ThreadMessage


class AIService:
    """Service for AI-powered features using Gemini API."""

    def __init__(self):
        self.api_key = None
        self.model = None  # GenerativeModel instance
        self.model_name = None
        self._initialized = False
        self._init_error = None
        self._try_initialize()
    
    def _try_initialize(self):
        """Try to initialize the Gemini API using GenerativeModel."""
        # Reload settings to get latest API key
        from app.config import settings
        self.api_key = settings.gemini_api_key
        
        if not self.api_key:
            print("⚠️ GEMINI_API_KEY not configured in settings")
            self._init_error = "API key not configured"
            self.model = None
            self._initialized = False
            return
        
        print(f"🔑 Loading API key: {self.api_key[:10]}...{self.api_key[-5:]} (length: {len(self.api_key)})")
        
        try:
            # Configure genai with API key (using GenerativeModel API)
            genai.configure(api_key=self.api_key)
            print("✅ Configured genai with API key")
            
            # Use Gemini 2.5 Flash (or fallback to other models if not available)
            # Note: gemini-2.5-flash might not exist, so we'll try it first then fallback
            models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-pro"]
            
            for model_to_try in models_to_try:
                try:
                    # Test the API key with a simple call using GenerativeModel
                    print(f"🔄 Testing API key with {model_to_try}...")
                    self.model = genai.GenerativeModel(model_to_try)
                    test_response = self.model.generate_content("Say OK")
                    if test_response and hasattr(test_response, 'text'):
                        print(f"✅ API key test successful with {model_to_try}: {test_response.text[:50]}")
                        self.model_name = model_to_try
                        self._initialized = True
                        break
                    else:
                        print(f"⚠️ API key test returned no response for {model_to_try}")
                        # Continue to next model
                        continue
                except Exception as e:
                    error_msg = str(e)
                    print(f"⚠️ {model_to_try} failed: {type(e).__name__}: {error_msg}")
                    
                    # If it's an API key error, stop trying
                    if "API key" in error_msg or "API_KEY" in error_msg or "expired" in error_msg.lower() or "invalid" in error_msg.lower():
                        self._init_error = f"API key error: {error_msg}"
                        self.model = None
                        self._initialized = False
                        return
                    
                    # If it's a model not found error, try next model
                    if "not found" in error_msg.lower() or "does not exist" in error_msg.lower() or "404" in error_msg:
                        print(f"   Model {model_to_try} not available, trying next...")
                        continue
                    
                    # For other errors, try next model
                    continue
            
            if not self._initialized:
                print("❌ All Gemini models failed to initialize")
                self._init_error = "All models failed to initialize. Check backend logs for details."
                self.model = None
                self._initialized = False
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error initializing Gemini API: {type(e).__name__}: {error_msg}")
            import traceback
            traceback.print_exc()
            self._init_error = error_msg
            self.model = None
    
    def is_available(self) -> bool:
        """Check if AI service is available (API key configured)."""
        # Always re-check API key in case it was set after initialization
        # Reload settings to get latest API key
        from app.config import settings
        current_api_key = settings.gemini_api_key
        
        # If API key changed or service not initialized, re-initialize
        if current_api_key != self.api_key or not self._initialized:
            if current_api_key:
                print(f"🔄 Re-initializing AI service with API key: {current_api_key[:10]}...{current_api_key[-5:]}")
                self._try_initialize()
            else:
                print("⚠️ No API key available, AI service unavailable")
                self.model = None
                self._initialized = False
        
        return self.model is not None and self._initialized
    
    # ------------------------------------------------------------------
    # Helper formatters + low level helpers
    # ------------------------------------------------------------------

    def _format_messages_for_summary(self, messages: List[Message]) -> str:
        """Format messages into a readable text format for summarization.

        NOTE: This is intentionally generic and is reused for compose‑assist /
        classification prompts as well.
        """
        formatted: List[str] = []
        for msg in messages:
            try:
                # Support both SQLAlchemy objects and MongoDB dicts
                if isinstance(msg, dict):
                    author = msg.get("author_name") or msg.get("author_id") or "Unknown"
                    direction_val = msg.get("direction", "outbound")
                    direction = "Sent" if str(direction_val) == "outbound" else "Received"
                    channel_val = msg.get("channel", "email")
                    channel = str(channel_val).upper()
                    ts = msg.get("created_at")
                    # Handle datetime objects or ISO string timestamps from MongoDB
                    if ts is None:
                        timestamp = "Unknown time"
                    elif hasattr(ts, "strftime"):
                        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(ts, str):
                        # Try to parse ISO format string
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp = ts[:19] if len(ts) >= 19 else ts  # Take first 19 chars if ISO format
                    else:
                        timestamp = str(ts)
                    body = str(msg.get("body", "") or "")
                else:
                    author = msg.author_name or msg.author_id or "Unknown"
                    direction = "Sent" if msg.direction.value == "outbound" else "Received"
                    channel = msg.channel.value.upper()
                    if hasattr(msg.created_at, "strftime"):
                        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp = str(msg.created_at)
                    body = str(msg.body or "")

                formatted.append(f"[{timestamp}] {author} ({direction} via {channel}): {body}")
            except Exception as e:
                # Skip malformed messages but log the error
                print(f"⚠️ Error formatting message for summary: {e}")
                continue

        return "\n".join(formatted) if formatted else "No messages to format."
    
    def _format_thread_messages_for_summary(self, messages: List[ThreadMessage]) -> str:
        """Format thread messages into a readable text format for summarization."""
        formatted: List[str] = []
        for msg in messages:
            try:
                if isinstance(msg, dict):
                    author = msg.get("author_name") or msg.get("author_id") or "Unknown"
                    ts = msg.get("created_at")
                    # Handle datetime objects or ISO string timestamps from MongoDB
                    if ts is None:
                        timestamp = "Unknown time"
                    elif hasattr(ts, "strftime"):
                        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(ts, str):
                        # Try to parse ISO format string
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            timestamp = ts[:19] if len(ts) >= 19 else ts  # Take first 19 chars if ISO format
                    else:
                        timestamp = str(ts)
                    body = str(msg.get("body", "") or "")
                else:
                    author = msg.author_name or msg.author_id or "Unknown"
                    if hasattr(msg.created_at, "strftime"):
                        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp = str(msg.created_at)
                    body = str(msg.body or "")

                formatted.append(f"[{timestamp}] {author}: {body}")
            except Exception as e:
                # Skip malformed messages but log the error
                print(f"⚠️ Error formatting thread message for summary: {e}")
                continue

        return "\n".join(formatted) if formatted else "No messages to format."

    async def _generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini with a prompt that is expected to return pure JSON.

        This helper centralises error‑handling and JSON parsing. If the
        response is not valid JSON we try to salvage the content, otherwise
        we return None so callers can apply sensible fallbacks.
        """
        if not self.is_available():
            print("❌ AI service not available in _generate_json")
            return None

        try:
            print(f"🔄 Calling Gemini API with prompt length: {len(prompt)}")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response:
                print("❌ Gemini API returned None response")
                return None
                
            raw_text = response.text if hasattr(response, "text") else str(response)
            if not raw_text:
                print("❌ Gemini API returned empty text")
                return None
                
            raw_text = raw_text.strip()
            print(f"✅ Got response from Gemini (length: {len(raw_text)})")

            # Some models wrap JSON in markdown fences; strip them if present.
            if raw_text.startswith("```"):
                # remove first fence
                raw_text = raw_text.split("```", 2)
                if len(raw_text) >= 3:
                    raw_text = raw_text[1] if "{" in raw_text[1] else raw_text[2]
                else:
                    raw_text = raw_text[-1]
            raw_text = raw_text.strip("`\n ")
            
            # Remove "json" prefix if present (some models return "json\n{...}")
            if raw_text.lower().startswith("json"):
                # Find the first { or [ after "json"
                json_start = raw_text.find("{")
                if json_start == -1:
                    json_start = raw_text.find("[")
                if json_start != -1:
                    raw_text = raw_text[json_start:]
                else:
                    # If no { or [, try to find JSON after newline
                    lines = raw_text.split("\n", 1)
                    if len(lines) > 1:
                        raw_text = lines[1].strip()

            parsed = json.loads(raw_text)
            print("✅ Successfully parsed JSON from Gemini")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in _generate_json: {e}")
            print(f"   Raw response (first 500 chars): {raw_text[:500]}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"❌ Error in _generate_json / Gemini API call: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def summarize_conversation(
        self,
        conversation: Conversation,
        messages: List[Message],
        max_messages: int = 50
    ) -> Optional[str]:
        """
        Generate a summary of a conversation using Gemini AI.
        
        Args:
            conversation: The conversation object
            messages: List of messages in the conversation
            max_messages: Maximum number of messages to include in summary (to avoid token limits)
        
        Returns:
            Summary string or None if AI is not available or error occurs
        """
        # Ensure service is available before proceeding
        if not self.is_available():
            print("❌ AI service not available in summarize_conversation")
            return None
        
        if not self.model:
            print("❌ AI model not initialized in summarize_conversation")
            return None
        
        if not messages:
            return "No messages in this conversation."

        # Take the most recent messages if there are too many
        messages_to_summarize = messages[-max_messages:] if len(messages) > max_messages else messages

        # Build context, supporting both SQLAlchemy objects and Mongo dicts
        context_parts: List[str] = []

        if isinstance(conversation, dict):
            subject = conversation.get("subject")
            study_id = conversation.get("study_id")
            participant_phone = conversation.get("participant_phone")
            participant_email = conversation.get("participant_email")
        else:
            subject = getattr(conversation, "subject", None)
            study_id = getattr(conversation, "study_id", None)
            participant_phone = getattr(conversation, "participant_phone", None)
            participant_email = getattr(conversation, "participant_email", None)

        if subject:
            context_parts.append(f"Subject: {subject}")
        if study_id:
            context_parts.append(f"Study ID: {study_id}")
        if participant_phone:
            context_parts.append(f"Participant Phone: {participant_phone}")
        if participant_email:
            context_parts.append(f"Participant Email: {participant_email}")

        context = "\n".join(context_parts) if context_parts else "No additional context"
        
        # Format messages
        messages_text = self._format_messages_for_summary(messages_to_summarize)
        
        # Create prompt
        prompt = f"""Please provide a concise summary of the following clinical trial CRM conversation. 
Focus on key points, decisions, issues, and action items.

Conversation Context:
{context}

Messages ({len(messages_to_summarize)} of {len(messages)} total):
{messages_text}

Please provide a summary that includes:
1. Main topic or issue discussed
2. Key participants and their contributions
3. Important decisions or outcomes
4. Any action items or next steps
5. Overall status or resolution

Summary:"""
        
        try:
            # Run synchronous Gemini API call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            # Handle response - it might be a string or have a .text attribute
            if hasattr(response, 'text'):
                return response.text.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
        except Exception as e:
            print(f"Error generating conversation summary: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def summarize_thread(
        self,
        thread: Thread,
        messages: List[ThreadMessage],
        max_messages: int = 50
    ) -> Optional[str]:
        """
        Generate a summary of a thread using Gemini AI.
        
        Args:
            thread: The thread object
            messages: List of messages in the thread
            max_messages: Maximum number of messages to include in summary
        
        Returns:
            Summary string or None if AI is not available or error occurs
        """
        if not self.is_available():
            return None
        
        if not messages:
            return "No messages in this thread."

        # Take the most recent messages if there are too many
        messages_to_summarize = messages[-max_messages:] if len(messages) > max_messages else messages

        # Build context, supporting both SQLAlchemy objects and Mongo dicts
        if isinstance(thread, dict):
            title = thread.get("title")
            thread_type = thread.get("thread_type")
            status = thread.get("status")
            priority = thread.get("priority")
            description = thread.get("description")
            related_patient_id = thread.get("related_patient_id")
            related_study_id = thread.get("related_study_id")
        else:
            title = getattr(thread, "title", None)
            thread_type = getattr(thread, "thread_type", None)
            status = getattr(thread, "status", None)
            priority = getattr(thread, "priority", None)
            description = getattr(thread, "description", None)
            related_patient_id = getattr(thread, "related_patient_id", None)
            related_study_id = getattr(thread, "related_study_id", None)

        context_parts: List[str] = [
            f"Thread Title: {title}",
            f"Thread Type: {thread_type}",
            f"Status: {status}",
            f"Priority: {priority}",
        ]

        if description:
            context_parts.append(f"Description: {description}")
        if related_patient_id:
            context_parts.append(f"Related Patient ID: {related_patient_id}")
        if related_study_id:
            context_parts.append(f"Related Study ID: {related_study_id}")

        context = "\n".join(context_parts)
        
        # Format messages
        messages_text = self._format_thread_messages_for_summary(messages_to_summarize)
        
        # Create prompt
        prompt = f"""Please provide a concise summary of the following clinical trial CRM thread discussion.
Focus on key points, issues, decisions, and action items.

Thread Context:
{context}

Messages ({len(messages_to_summarize)} of {len(messages)} total):
{messages_text}

Please provide a summary that includes:
1. Main issue or topic being discussed
2. Key participants and their contributions
3. Important decisions or resolutions
4. Any action items or next steps
5. Current status and any blockers

Summary:"""
        
        try:
            # Run synchronous Gemini API call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            # Handle response - it might be a string or have a .text attribute
            if hasattr(response, 'text'):
                return response.text.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
        except Exception as e:
            print(f"Error generating thread summary: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ------------------------------------------------------------------
    # NEW: AI Compose Assist (3.1)
    # ------------------------------------------------------------------

    async def compose_reply(
        self,
        history_text: str,
        latest_draft: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate multiple reply drafts + summary + key facts for an email thread.

        This is a generic helper; the caller is responsible for preparing
        `history_text` (conversation or thread) and passing any partial draft.
        """
        if not self.is_available():
            return None

        draft_section = f"\nUser current draft (may be empty):\n{latest_draft}\n" if latest_draft else "\nUser has not written a draft yet.\n"

        prompt = f"""
You are an AI assistant helping a CRM user reply to an email thread.
Read the full thread below and generate suggested replies.

Thread history:
{history_text}
{draft_section}

Your task:
1. Propose three alternative reply drafts:
   - professional: well‑structured, formal but friendly.
   - short: very concise, minimal but clear.
   - detailed: longer, addresses all points explicitly.
2. Write a short overall summary of the thread.
3. Extract key facts as a bullet‑style list (names, dates, commitments, decisions, open questions).

CRITICAL OUTPUT FORMAT:
Respond with ONLY valid JSON, no extra text, with this exact structure:
{{
  "drafts": {{
    "professional": "string",
    "short": "string",
    "detailed": "string"
  }},
  "summary": "string",
  "facts": ["string", "string"]
}}

Make sure the JSON is syntactically valid and does not contain comments.
"""

        # First, try strict JSON mode
        data = await self._generate_json(prompt)
        if data:
            drafts = data.get("drafts") or {}
            return {
                "drafts": {
                    "professional": str(drafts.get("professional") or ""),
                    "short": str(drafts.get("short") or ""),
                    "detailed": str(drafts.get("detailed") or ""),
                },
                "summary": str(data.get("summary") or ""),
                "facts": [str(f) for f in (data.get("facts") or [])],
            }

        # Fallback: ask for three labelled drafts in plain text and parse them
        try:
            loop = asyncio.get_event_loop()
            fallback_prompt = f"""
You are helping a CRM user reply to an email thread.

Thread history:
{history_text}

User draft (may be empty):
{latest_draft or "(no draft)"}

Write THREE alternative reply drafts in this exact plain‑text format (no JSON, no markdown fences):

[PROFESSIONAL]
<professional_reply_here>

[SHORT]
<short_reply_here>

[DETAILED]
<detailed_reply_here>

Do not add any extra commentary before or after these sections.
"""
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(fallback_prompt)
            )
            raw = response.text if hasattr(response, "text") else str(response)
            raw = (raw or "").strip()
        except Exception as e:
            print(f"Error in compose_reply fallback: {e}")
            return None

        # Simple parser for the labelled sections
        professional = ""
        short = ""
        detailed = ""
        try:
            sections = raw.split("[PROFESSIONAL]")
            if len(sections) > 1:
                rest = sections[1]
                parts = rest.split("[SHORT]")
                professional = parts[0].strip()
                if len(parts) > 1:
                    rest2 = parts[1]
                    parts2 = rest2.split("[DETAILED]")
                    short = parts2[0].strip()
                    if len(parts2) > 1:
                        detailed = parts2[1].strip()
        except Exception as e:
            print(f"Error parsing compose_reply fallback output: {e}")

        # If parsing failed badly, fall back to using the whole text for all
        if not (professional or short or detailed):
            professional = raw
            short = raw
            detailed = raw

        return {
            "drafts": {
                "professional": professional,
                "short": short,
                "detailed": detailed,
            },
            "summary": "",
            "facts": [],
        }

    # ------------------------------------------------------------------
    # NEW: Auto‑classification (3.3) + tone / delta summary (3.2)
    # ------------------------------------------------------------------

    async def classify_conversation(
        self,
        context_text: str,
        latest_message_text: str
    ) -> Optional[Dict[str, Any]]:
        """Classify a conversation into category/priority/sentiment/next action.

        Returns a normalised dict with keys:
          ai_category, ai_priority, ai_sentiment, ai_next_best_action
        """
        if not self.is_available():
            return None

        prompt = f"""
You are analysing a CRM conversation.

Conversation context:
{context_text}

Most recent message:
{latest_message_text}

Classify the conversation and suggest a next best action.

Allowed values:
- aiCategory: "ops", "admission", "sales", "support", "other"
- aiPriority: "low", "medium", "high", "urgent"
- aiSentiment: "negative", "neutral", "positive"

Output STRICTLY the following JSON (no comments, no extra text):
{{
  "aiCategory": "ops|admission|sales|support|other",
  "aiPriority": "low|medium|high|urgent",
  "aiSentiment": "negative|neutral|positive",
  "aiNextBestAction": "short natural‑language recommendation"
}}
"""
        data = await self._generate_json(prompt)
        if not data:
            # If Gemini fails or returns invalid JSON, skip classification for this conversation.
            # UI will simply not show any pills instead of showing generic defaults.
            return None

        # Normalise / validate with safe fallbacks
        cat = str(data.get("aiCategory") or "other").lower()
        if cat not in {"ops", "admission", "sales", "support", "other"}:
            cat = "other"

        prio = str(data.get("aiPriority") or "medium").lower()
        if prio not in {"low", "medium", "high", "urgent"}:
            prio = "medium"

        sent = str(data.get("aiSentiment") or "neutral").lower()
        if sent not in {"negative", "neutral", "positive"}:
            sent = "neutral"

        nba = str(data.get("aiNextBestAction") or "")

        return {
            "ai_category": cat,
            "ai_priority": prio,
            "ai_sentiment": sent,
            "ai_next_best_action": nba,
        }

    async def analyse_new_message(
        self,
        history_text: str,
        new_message_text: str
    ) -> Optional[Dict[str, Any]]:
        """Analyse a new message: update summary delta + tone.

        Returns dict { 'delta_summary': str, 'tone': str }.
        """
        if not self.is_available():
            return None

        prompt = f"""
You are analysing the latest message in a CRM conversation or thread.

Conversation / thread history (including older messages):
{history_text}

Newest message:
{new_message_text}

Tasks:
1. Briefly summarise what changed with this latest message compared to the previous history.
2. Classify the tone of the latest message into one of:
   "neutral", "polite", "angry", "confused", "urgent".

Output STRICTLY this JSON (no extra text):
{{
  "deltaSummary": "string",
  "tone": "neutral|polite|angry|confused|urgent"
}}
"""
        data = await self._generate_json(prompt)
        if not data:
            return None

        tone = str(data.get("tone") or "neutral").lower()
        if tone not in {"neutral", "polite", "angry", "confused", "urgent"}:
            tone = "neutral"

        return {
            "delta_summary": str(data.get("deltaSummary") or ""),
            "tone": tone,
        }

    # ------------------------------------------------------------------
    # NEW: Pre‑send message checks (3.4)
    # ------------------------------------------------------------------

    async def check_message_before_send(
        self,
        context_text: str,
        draft_body: str,
        attachments: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Ask Gemini to check a draft message for missing information.

        Returns dict: { 'issues': [...], 'okToSend': bool }.
        """
        issues: List[Dict[str, str]] = []
        body_lower = (draft_body or "").lower()

        # ------------------------------------------------------------------
        # Deterministic rule‑based checks (run even if Gemini is unavailable)
        # ------------------------------------------------------------------

        # 1) Relative time words without any explicit date digits → missing_date
        relative_keywords = ["tomorrow", "tonight", "next week", "next month", "next year", "this week"]
        has_relative = any(k in body_lower for k in relative_keywords)
        has_digit = any(ch.isdigit() for ch in body_lower)
        if has_relative and not has_digit:
            issues.append({
                "type": "missing_date",
                "message": "You used a relative time (e.g. 'tomorrow') but did not specify an exact date/time."
            })

        # 2) Mentions of attachments but no actual files selected → missing_attachment
        if ("attach" in body_lower or "attached" in body_lower) and not attachments:
            issues.append({
                "type": "missing_attachment",
                "message": "You mentioned an attachment but have not added any file."
            })

        # 3) Vague 'follow steps' without any list → unclear_next_step
        if "follow the steps" in body_lower or "follow steps" in body_lower:
            has_list = any(prefix in body_lower for prefix in ["1.", "1)", "step 1", "first,"])
            if not has_list:
                issues.append({
                    "type": "unclear_next_step",
                    "message": "You asked the recipient to 'follow steps' but did not list the steps."
                })

        # ------------------------------------------------------------------
        # Optional AI‑based checks via Gemini (augment, not replace)
        # ------------------------------------------------------------------
        attachments_list = ", ".join(attachments) if attachments else "none"

        prompt = f"""
You are reviewing an email draft before it is sent from a CRM.

Conversation / thread context:
{context_text}

Draft message body:
{draft_body}

Attachments currently selected (file names): {attachments_list}

Identify potential issues before sending, such as:
- missing or ambiguous dates / times,
- mentioned attachments that are not actually attached,
- missing clear next step,
- any other critical missing information.

Respond STRICTLY with JSON:
{{
  "issues": [
    {{
      "type": "missing_date|missing_attachment|unclear_next_step|other",
      "message": "human readable guidance"
    }}
  ],
  "okToSend": true|false
}}

If there are no issues, use an empty array and okToSend = true.
"""
        data = None
        if self.is_available():
            data = await self._generate_json(prompt)

        if data:
            issues_raw = data.get("issues") or []
            for item in issues_raw:
                try:
                    itype = str(item.get("type") or "other")
                    msg = str(item.get("message") or "")
                    if msg:
                        issues.append({"type": itype, "message": msg})
                except Exception:
                    continue
            ai_ok = bool(data.get("okToSend")) if issues_raw else True
        else:
            ai_ok = True  # if AI fails, rely on deterministic rules only

        # If any issues (either from rules or AI), default to okToSend = False,
        # otherwise fall back to AI's ok flag or True.
        ok_to_send = False if issues else ai_ok

        return {
            "issues": issues,
            "okToSend": ok_to_send,
        }
    
    async def chat_with_document(
        self,
        question: str,
        document_path: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "general"  # "general" or "document"
    ) -> Optional[str]:
        """
        Chat with AI, optionally using a document for context.
        
        Args:
            question: User's question
            document_path: Path to uploaded document (optional)
            chat_history: Previous messages in format [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            mode: "general" for general chat, "document" for document-based Q&A
        
        Returns:
            AI response string or None if error
        """
        if not self.is_available():
            return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # If document mode, use document-based Q&A
            if mode == "document" and document_path:
                import os
                import pathlib
                
                if not os.path.exists(document_path):
                    raise FileNotFoundError(f"Document file not found at path: {document_path}")
                
                try:
                    # Read file and pass it directly to Gemini
                    # For version 0.3.2, we need to read the file and pass it as content
                    file_path_obj = pathlib.Path(document_path)
                    print(f"Reading file for Gemini: {file_path_obj}")
                    
                    # Read file content as bytes
                    with open(file_path_obj, 'rb') as f:
                        file_data = f.read()
                    
                    # Get file mime type
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(str(file_path_obj))
                    if not mime_type:
                        # Default based on extension
                        if str(file_path_obj).lower().endswith('.pdf'):
                            mime_type = "application/pdf"
                        elif str(file_path_obj).lower().endswith(('.doc', '.docx')):
                            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        elif str(file_path_obj).lower().endswith('.txt'):
                            mime_type = "text/plain"
                        else:
                            mime_type = "application/octet-stream"
                    
                    print(f"File read: {len(file_data)} bytes, MIME type: {mime_type}")
                    
                    # Build prompt for document Q&A
                    prompt_text = f"""Please answer the following question based on the uploaded document. 
Be thorough, accurate, and cite specific information from the document when possible.
If the question cannot be fully answered from the document, provide the best answer you can based on the document content.

Question: {question}"""
                    
                    # Generate content with file - pass file data as part of content
                    print(f"Generating response with document...")
                    
                    # Try multiple methods to pass file to Gemini
                    response = None
                    last_error = None
                    
                    # Method 1: Use upload_file (available in 0.8.0+)
                    try:
                        file_part = await loop.run_in_executor(
                            None,
                            lambda: genai.upload_file(path=str(file_path_obj), mime_type=mime_type)
                        )
                        
                        print(f"File uploaded: {file_part.name}, state: {getattr(file_part, 'state', 'unknown')}")
                        
                        # Wait for file to be processed (if it has a state attribute)
                        if hasattr(file_part, 'state'):
                            max_wait = 60
                            wait_time = 0
                            while wait_time < max_wait:
                                # Check state - it might be an enum or string
                                state = file_part.state
                                state_str = str(state).upper() if hasattr(state, 'upper') else str(state)
                                
                                if "ACTIVE" in state_str or "READY" in state_str:
                                    break
                                elif "PROCESSING" in state_str or "PENDING" in state_str:
                                    await asyncio.sleep(2)
                                    wait_time += 2
                                    # Refresh file state
                                    if hasattr(genai, 'get_file') and hasattr(file_part, 'name'):
                                        file_part = await loop.run_in_executor(
                                            None,
                                            lambda: genai.get_file(file_part.name)
                                        )
                                else:
                                    # Unknown state, proceed anyway
                                    break
                        
                        print(f"File ready, generating response...")
                        response = await loop.run_in_executor(
                            None,
                            lambda: self.model.generate_content([prompt_text, file_part])
                        )
                    except Exception as e1:
                        last_error = e1
                        print(f"Method 1 (upload_file) failed: {e1}")
                        
                        # Method 2: Try passing file data directly as dict
                        try:
                            response = await loop.run_in_executor(
                                None,
                                lambda: self.model.generate_content([
                                    prompt_text,
                                    {
                                        "mime_type": mime_type,
                                        "data": file_data
                                    }
                                ])
                            )
                        except Exception as e2:
                            last_error = e2
                            print(f"Method 2 (direct dict) failed: {e2}")
                            
                            # Method 3: Try using Part if available
                            try:
                                from google.generativeai.types import Part
                                file_part = Part.from_data(mime_type=mime_type, data=file_data)
                                response = await loop.run_in_executor(
                                    None,
                                    lambda: self.model.generate_content([prompt_text, file_part])
                                )
                            except ImportError:
                                # Part not available, try one more method
                                raise Exception(f"Unable to process file. Please upgrade google-generativeai package to version >= 0.8.0 for file support. Current error: {str(e2)}")
                            except Exception as e3:
                                last_error = e3
                                raise Exception(f"Unable to process file with Gemini API. All methods failed. Last error: {str(e3)}. Please ensure the file is a supported format (PDF, DOC, DOCX, TXT) and the google-generativeai package is up to date.")
                    
                    if response is None:
                        raise Exception(f"Failed to generate response. Last error: {str(last_error)}")
                    
                    print(f"Response generated successfully")
                    
                except FileNotFoundError as e:
                    print(f"File not found error: {e}")
                    raise Exception(f"Document file not found: {str(e)}")
                except Exception as e:
                    error_details = str(e)
                    print(f"Error processing document: {error_details}")
                    import traceback
                    traceback.print_exc()
                    # Provide more helpful error message
                    if "not supported" in error_details.lower() or "format" in error_details.lower():
                        raise Exception(f"Document format not supported. Please upload a PDF, DOC, DOCX, or TXT file.")
                    elif "timeout" in error_details.lower() or "timed out" in error_details.lower():
                        raise Exception(f"Document processing timed out. The file might be too large. Please try a smaller file.")
                    else:
                        raise Exception(f"Failed to process document: {error_details}. Please ensure the file is valid and try again.")
            else:
                # General chat mode - build conversation with history
                # Build prompt with conversation history
                prompt_parts = []
                
                if chat_history:
                    for msg in chat_history:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "user":
                            prompt_parts.append(f"User: {content}")
                        elif role == "assistant":
                            prompt_parts.append(f"Assistant: {content}")
                
                # Add current question
                prompt_parts.append(f"User: {question}")
                prompt_parts.append("Assistant:")
                
                prompt = "\n\n".join(prompt_parts)
                
                # Generate response
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(prompt)
                )
            
            # Extract response text
            if hasattr(response, 'text'):
                return response.text.strip()
            elif isinstance(response, str):
                return response.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"Error in chat_with_document: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def analyze_thread_similarity(
        self,
        thread1_data: Dict[str, Any],
        thread2_data: Dict[str, Any],
        thread1_messages: List[Dict[str, Any]],
        thread2_messages: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze similarity between two threads and suggest if they should be combined.
        Returns: {
            "should_combine": bool,
            "similarity_score": float (0-100),
            "reasoning": str,
            "factors": List[str],  # e.g., ["Same patient", "Same side effect"]
            "recommendation": str  # "strong", "moderate", "weak", "no"
        }
        """
        if not self.is_available():
            print("⚠️ AI service not available for thread similarity analysis")
            return None
        
        try:
            # Format thread messages for analysis
            thread1_text = self._format_thread_messages_for_analysis(thread1_messages)
            thread2_text = self._format_thread_messages_for_analysis(thread2_messages)
            
            # Build prompt
            prompt = f"""Analyze two threads from a clinical trials CRM system and determine if they should be combined.

Thread 1:
- Title: {thread1_data.get('title', 'N/A')}
- Type: {thread1_data.get('thread_type', 'N/A')}
- Patient ID: {thread1_data.get('related_patient_id', 'N/A')}
- Study ID: {thread1_data.get('related_study_id', 'N/A')}
- Description: {thread1_data.get('description', 'N/A')}
- Messages:
{thread1_text}

Thread 2:
- Title: {thread2_data.get('title', 'N/A')}
- Type: {thread2_data.get('thread_type', 'N/A')}
- Patient ID: {thread2_data.get('related_patient_id', 'N/A')}
- Study ID: {thread2_data.get('related_study_id', 'N/A')}
- Description: {thread2_data.get('description', 'N/A')}
- Messages:
{thread2_text}

Analyze if these threads should be combined. Consider:
1. Same patient (if patient IDs match or are mentioned) - HIGH PRIORITY
2. Same title - HIGH PRIORITY (if titles match exactly, strongly recommend combining)
3. Same conversation (if conversation_id matches) - HIGH PRIORITY
4. Same medical condition/side effect/disease
5. Same topic or issue
6. Related discussions that would benefit from being together
7. Temporal proximity (recent related discussions)

IMPORTANT RULES:
- If titles are EXACTLY the same (case-insensitive), recommend combining with score 80-100
- If conversation_id is the same AND titles are similar, recommend combining with score 70-90
- If patient IDs match AND titles are similar, recommend combining with score 70-90
- Be generous with recommendations when there are clear matches

Return a JSON object with this exact structure:
{{
    "should_combine": true/false,
    "similarity_score": 0-100,
    "reasoning": "Detailed explanation of why they should or shouldn't be combined",
    "factors": ["Factor 1", "Factor 2", ...],
    "recommendation": "strong" | "moderate" | "weak" | "no"
}}

Be reasonable: recommend combining when there are clear matches (same title, same conversation, same patient, or similar topics)."""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if not response:
                return None
            
            raw_text = response.text if hasattr(response, 'text') else str(response)
            raw_text = raw_text.strip()
            
            # Parse JSON response
            parsed = self._parse_json_response(raw_text)
            if parsed:
                # Validate structure
                if 'should_combine' in parsed and 'similarity_score' in parsed:
                    return {
                        'should_combine': bool(parsed['should_combine']),
                        'similarity_score': float(parsed.get('similarity_score', 0)),
                        'reasoning': parsed.get('reasoning', ''),
                        'factors': parsed.get('factors', []),
                        'recommendation': parsed.get('recommendation', 'no')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error in analyze_thread_similarity: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _format_thread_messages_for_analysis(self, messages: List[Dict[str, Any]]) -> str:
        """Format thread messages for AI analysis."""
        if not messages:
            return "No messages"
        
        formatted = []
        for msg in messages:
            author = msg.get('author_name') or msg.get('author_id', 'Unknown')
            body = msg.get('body', '')
            created_at = msg.get('created_at', '')
            formatted.append(f"- {author}: {body} ({created_at})")
        
        return "\n".join(formatted)
    
    def _parse_json_response(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from AI response, handling markdown fences and prefixes."""
        try:
            # Remove markdown fences
            if raw_text.startswith("```"):
                parts = raw_text.split("```", 2)
                if len(parts) >= 3:
                    raw_text = parts[1] if "{" in parts[1] else parts[2]
                else:
                    raw_text = parts[-1]
            raw_text = raw_text.strip("`\n ")
            
            # Remove "json" prefix if present
            if raw_text.lower().startswith("json"):
                json_start = raw_text.find("{")
                if json_start != -1:
                    raw_text = raw_text[json_start:]
                else:
                    lines = raw_text.split("\n", 1)
                    if len(lines) > 1:
                        raw_text = lines[1].strip()
            
            return json.loads(raw_text)
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
            return None
    
    async def extract_task_from_message(
        self,
        message_text: str,
        recent_messages: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract task information from a conversation message using AI.
        
        Args:
            message_text: The message text to analyze
            recent_messages: Optional list of recent messages for context
                Format: [{"author": "...", "text": "...", "createdAt": "..."}]
        
        Returns:
            Dict with keys: title, description, suggestedStatus, suggestedDueDate
            or None if AI unavailable or error
        """
        if not self.is_available():
            print("⚠️ AI service not available for task extraction")
            return None
        
        try:
            # Build context from recent messages
            context_text = ""
            if recent_messages:
                context_lines = []
                for msg in recent_messages[-5:]:  # Last 5 messages for context
                    author = msg.get("author", "Unknown")
                    text = msg.get("text", "")
                    context_lines.append(f"- {author}: {text}")
                if context_lines:
                    context_text = "\nRecent conversation context:\n" + "\n".join(context_lines)
            
            prompt = f"""Analyze the following message from a clinical trials CRM conversation and extract task information.

Message to analyze:
"{message_text}"
{context_text}

Extract actionable task information:
1. Title: A short, actionable task title (1 sentence, max 80 characters)
2. Description: A brief description explaining what needs to be done (1-3 sentences)
3. Suggested status: Usually "open" for new tasks
4. Suggested due date: If a date/time is mentioned, extract it (ISO format YYYY-MM-DD or null)

Return STRICTLY as JSON:
{{
  "title": "Short actionable task title",
  "description": "Brief description of the task and context",
  "suggestedStatus": "open",
  "suggestedDueDate": "YYYY-MM-DD" or null
}}

Guidelines:
- Title should be concise and action-oriented (e.g., "Follow up with patient 001", "Schedule site visit")
- Description should include relevant context from the message
- Only extract a due date if explicitly mentioned or strongly implied
- If no clear task can be extracted, return null for all fields"""
            
            result = await self._generate_json(prompt)
            
            if result:
                # Validate and normalize response
                return {
                    "title": result.get("title", "").strip()[:80] or None,
                    "description": result.get("description", "").strip() or None,
                    "suggestedStatus": result.get("suggestedStatus", "open"),
                    "suggestedDueDate": result.get("suggestedDueDate") or None
                }
            
            return None
            
        except Exception as e:
            print(f"Error in extract_task_from_message: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global AI service instance
ai_service = AIService()

