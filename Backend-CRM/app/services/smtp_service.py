"""
SMTP Service for sending emails from CRM
Sends emails using SMTP (Gmail, SendGrid, or custom SMTP server)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Union
import os
import re

from app.config import settings


class SMTPService:
    """Service for sending emails via SMTP (Mailgun, Gmail, etc.)"""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None
    ):
        # Prefer explicit args, then settings, then sensible defaults
        self.smtp_host = smtp_host or getattr(settings, "smtp_host", "smtp.gmail.com")
        self.smtp_port = smtp_port or getattr(settings, "smtp_port", 587)
        self.smtp_user = smtp_user or getattr(settings, "smtp_user", None)
        self.smtp_password = smtp_password or getattr(settings, "smtp_password", None)
        
        # Log SMTP configuration status
        if self.smtp_user and self.smtp_password:
            print(f"✅ SMTP configured: {self.smtp_user}@{self.smtp_host}:{self.smtp_port}")
        else:
            print(f"⚠️  SMTP not fully configured - missing credentials (host: {self.smtp_host}:{self.smtp_port})")
    
    def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        body: str,
        from_email: str,
        from_name: Optional[str] = None,
        html: bool = False,
        attachments: Optional[List[str]] = None,
        reply_to: Optional[str] = None
    ) -> dict:
        """
        Send an email via SMTP
        
        Args:
            to: Recipient email address(es) - can be a single string or list of strings
            subject: Email subject
            body: Email body (plain text or HTML)
            from_email: Sender email address (e.g., study1site1@dizzaroo.com)
            from_name: Sender display name
            html: Whether body is HTML
            attachments: List of file paths to attach
            reply_to: Reply-To email address
        
        Returns:
            Dict with success status and message ID
        """
        try:
            # ------------------------------------------------------------------
            # Sanitize from_email to ALWAYS be a valid RFC-compliant address.
            # This protects us even if upstream passes something like "New study01@mg.dizzaroo.com".
            # ------------------------------------------------------------------
            raw_from_email = (from_email or "").strip()
            if "@" in raw_from_email:
                local_part, domain_part = raw_from_email.split("@", 1)
            else:
                # Fallback to configured SMTP domain if no domain provided
                local_part = raw_from_email or "noreply"
                smtp_user = settings.smtp_user or ""
                domain_part = smtp_user.split("@")[1] if "@" in smtp_user else "dizzaroo.com"

            # Normalize local part: lowercase, remove anything except letters, digits and hyphens
            safe_local = re.sub(r"[^a-z0-9-]+", "", local_part.lower())
            if not safe_local:
                safe_local = "noreply"

            sanitized_from_email = f"{safe_local}@{domain_part}"

            # Normalize to list of recipients
            if isinstance(to, str):
                recipient_list = [to]
            else:
                recipient_list = [email.strip() for email in to if email and email.strip()]
            
            if not recipient_list:
                return {
                    'success': False,
                    'error': 'No valid recipient email addresses provided',
                    'method': 'smtp'
                }
            
            # Create message
            msg = MIMEMultipart()
            # Set To header as comma-separated string for multiple recipients
            msg['To'] = ', '.join(recipient_list)
            msg['Subject'] = subject
            
            if from_name:
                msg['From'] = f"{from_name} <{sanitized_from_email}>"
            else:
                msg['From'] = sanitized_from_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                            msg.attach(part)
            
            # Send via SMTP
            if self.smtp_user and self.smtp_password:
                print(f"📧 Attempting to send email via SMTP ({self.smtp_host}:{self.smtp_port})")
                print(f"   From: {sanitized_from_email}")
                print(f"   To: {', '.join(recipient_list)}")
                print(f"   Recipient count: {len(recipient_list)}")
                print(f"   Recipient list: {recipient_list}")
                print(f"   Subject: {subject}")
                
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    print(f"   Connected to SMTP server")
                    server.starttls()
                    print(f"   TLS started")
                    server.login(self.smtp_user, self.smtp_password)
                    print(f"   Authenticated as {self.smtp_user}")
                    # Use send_message with to_addrs parameter for proper delivery to all recipients
                    # to_addrs can be a list of email addresses
                    server.send_message(msg, to_addrs=recipient_list)
                    print(f"   Message sent successfully to {len(recipient_list)} recipient(s)")
                
                print(f"✅ Email sent via SMTP to {len(recipient_list)} recipient(s): {', '.join(recipient_list)}")
                return {
                    'success': True,
                    'message_id': msg.get('Message-ID'),
                    'method': 'smtp',
                    'recipients': recipient_list
                }
            else:
                print(f"⚠️  SMTP credentials not configured, email not sent: {', '.join(recipient_list)}")
                return {
                    'success': False,
                    'error': 'SMTP credentials not configured',
                    'method': 'smtp'
                }
            
        except Exception as e:
            print(f'❌ SMTP error: {e}')
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'method': 'smtp',
                'recipients': recipient_list if 'recipient_list' in locals() else []
            }


# Create default instance
smtp_service = SMTPService()

