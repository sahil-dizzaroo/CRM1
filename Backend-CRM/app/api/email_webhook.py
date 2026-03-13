
from fastapi import APIRouter, HTTPException, Form
from typing import Optional
import hmac
import hashlib

from app.config import settings
from app.workers.tasks import process_webhook_task

router = APIRouter(prefix="/webhooks/email", tags=["email-webhook"])


def verify_mailgun_signature(timestamp: str, token: str, signature: str):
    if not settings.mailgun_signing_key:
        raise RuntimeError("MAILGUN_SIGNING_KEY must be set")

    msg = f"{timestamp}{token}".encode()
    key = settings.mailgun_signing_key.encode()

    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Invalid Mailgun signature")


@router.post("/mailgun")
async def mailgun_inbound(
    timestamp: str = Form(...),
    token: str = Form(...),
    signature: str = Form(...),
    recipient: str = Form(...),
    sender: str = Form(...),
    subject: str = Form(""),
    body_plain: Optional[str] = Form(None, alias="body-plain"),
    stripped_text: Optional[str] = Form(None, alias="stripped-text"),
    stripped_html: Optional[str] = Form(None, alias="stripped-html"),
    message_id: Optional[str] = Form(None, alias="Message-Id"),
):
    verify_mailgun_signature(timestamp, token, signature)

    payload = {
        "event_type": "inbound",
        "message_id": message_id,
        "recipient": recipient,
        "sender": sender,
        "subject": subject,
        # 🔑 NORMALIZED KEYS
        "body_plain": body_plain,
        "stripped_text": stripped_text,
        "stripped_html": stripped_html,
    }

    process_webhook_task.delay(payload)

    return {"status": "ok"}
