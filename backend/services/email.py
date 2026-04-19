"""
services/email.py Email sending with SendGrid (primary) → SMTP (fallback).

Both methods run through a single send_email() interface.
The caller never needs to know which transport was used.
"""

import asyncio
import base64
import logging
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    """
    Unified email sending interface.

    Priority:
      1. SendGrid  (API-based, scalable, with tracking)
      2. SMTP      (Gmail or any SMTP server)

    If neither is configured, send_email() returns a 'preview_only' result.
    """

    def __init__(
        self,
        sendgrid_api_key: str = "",
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "",
        from_name: str = "FireReach AI",
        google_client_id: str = "",
        google_client_secret: str = "",
    ):
        self.sendgrid_api_key = sendgrid_api_key.strip()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user.strip()
        self.smtp_password = smtp_password
        self.from_email = from_email.strip() or smtp_user.strip()
        self.from_name = from_name
        self.google_client_id = google_client_id.strip()
        self.google_client_secret = google_client_secret.strip()

        self._has_sendgrid = bool(self.sendgrid_api_key)
        self._has_smtp = bool(self.smtp_user and self.smtp_password)

        if self._has_sendgrid:
            logger.info("Email service: SendGrid (primary) + SMTP (fallback)")
        elif self._has_smtp:
            logger.info("Email service: SMTP only (no SendGrid key)")
        else:
            logger.warning("Email service: No credentials — preview-only mode")

    # ──────────────────────────────────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────────────────────────────────

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        company: str = "",
        track_metadata: Optional[Dict[str, Any]] = None,
        sender_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send email. Returns a result dict with status, message_id, method.

        Result schema:
        {
            "status":     "sent" | "failed" | "preview_only",
            "method":     "sendgrid" | "smtp" | "none",
            "message_id": str | None,
            "timestamp":  ISO string,
            "error":      str | None,
        }
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # ── Per-user Google OAuth sender (highest priority) ──────────────────
        if sender_profile and sender_profile.get("google_refresh_token") and sender_profile.get("google_email"):
            try:
                result = await self._send_google_oauth(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    sender_email=sender_profile.get("google_email"),
                    sender_name=sender_profile.get("name") or self.from_name,
                    refresh_token=sender_profile.get("google_refresh_token"),
                    reply_to=sender_profile.get("reply_to"),
                )
                logger.info("Email sent via Google OAuth to %s", to_email)
                return result
            except Exception as exc:
                logger.warning("Google OAuth send failed (%s) — trying fallback transport", exc)

        # ── Try SendGrid first ───────────────────────────────────────────────
        if self._has_sendgrid:
            try:
                result = await self._send_sendgrid(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    sender_name=(sender_profile or {}).get("name"),
                    reply_to=(sender_profile or {}).get("reply_to"),
                )
                logger.info("Email sent via SendGrid to %s", to_email)
                return result
            except Exception as exc:
                logger.warning("SendGrid failed (%s) — trying SMTP fallback", exc)

        # ── SMTP fallback ────────────────────────────────────────────────────
        if self._has_smtp:
            try:
                result = await self._send_smtp(
                    to_email=to_email,
                    subject=subject,
                    body=body,
                    sender_name=(sender_profile or {}).get("name"),
                    reply_to=(sender_profile or {}).get("reply_to"),
                )
                logger.info("Email sent via SMTP to %s", to_email)
                return result
            except Exception as exc:
                logger.error("SMTP also failed: %s", exc)
                return {
                    "status": "failed",
                    "method": "smtp",
                    "message_id": None,
                    "timestamp": timestamp,
                    "error": str(exc),
                }

        # ── No credentials — preview mode ────────────────────────────────────
        logger.info("No email credentials — returning preview_only result")
        return {
            "status": "preview_only",
            "method": "none",
            "message_id": None,
            "timestamp": timestamp,
            "error": "No email credentials configured. Add SENDGRID_API_KEY or SMTP credentials.",
        }

    async def validate_config(self) -> Dict[str, bool]:
        """Return which transports are available."""
        return {
            "sendgrid_configured": self._has_sendgrid,
            "smtp_configured": self._has_smtp,
            "google_oauth_configured": bool(self.google_client_id and self.google_client_secret),
            "can_send": self._has_sendgrid or self._has_smtp or bool(self.google_client_id and self.google_client_secret),
        }

    async def _send_google_oauth(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_email: str,
        sender_name: str,
        refresh_token: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.google_client_id or not self.google_client_secret:
            raise RuntimeError("Google OAuth client credentials are not configured")

        token_data = await self._google_refresh_access_token(refresh_token)
        access_token = token_data["access_token"]

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = reply_to or sender_email
        msg.attach(MIMEText(body, "plain"))
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"raw": raw_message},
            )
            if res.status_code >= 400:
                raise RuntimeError(f"Gmail API send failed: {res.status_code} {res.text}")
            payload = res.json()

        return {
            "status": "sent",
            "method": "google_oauth",
            "message_id": payload.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }

    async def _google_refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if res.status_code >= 400:
                raise RuntimeError(f"Google token refresh failed: {res.status_code} {res.text}")
            return res.json()

    # ──────────────────────────────────────────────────────────────────────────
    # SendGrid
    # ──────────────────────────────────────────────────────────────────────────

    async def _send_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=(self.from_email, sender_name or self.from_name),
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )
        message.reply_to = reply_to or self.from_email

        def _sync_send():
            sg = SendGridAPIClient(self.sendgrid_api_key)
            return sg.send(message)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, _sync_send)

        return {
            "status": "sent",
            "method": "sendgrid",
            "message_id": response.headers.get("X-Message-Id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None,
            "http_status": response.status_code,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # SMTP
    # ──────────────────────────────────────────────────────────────────────────

    async def _send_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        sender_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name or self.from_name} <{self.smtp_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(body, "plain"))

        def _sync_send():
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, to_email, msg.as_string())

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_send)

        return {
            "status": "sent",
            "method": "smtp",
            "message_id": f"smtp_{int(datetime.now(timezone.utc).timestamp())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
