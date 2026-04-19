"""
main.py – FireReach AI FastAPI application.

Endpoints:
  POST /run-agent          → Full agent pipeline
  POST /batch-analyze      → Multi-company batch run
  GET  /history            → Outreach history
  GET  /status/{company}   → Dedup check
  GET  /record/{id}        → Single record
  DELETE /record/{id}      → Delete record
  GET  /stats              → Dashboard stats
  GET  /health             → Service health check
"""

import logging
import os
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
import httpx

from config import settings
from db.database import init_db, get_session_factory
from agent.graph import build_agent_graph
from services.serper import SerperService
from services.llm import LLMService
from services.email import EmailService
from services.memory import MemoryService
from services.contact_discovery import ContactDiscoveryService
from services.auth import AuthService
from db.models import User

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Global service instances ──────────────────────────────────────────────────
serper_service: SerperService = None
llm_service: LLMService = None
email_service: EmailService = None
memory_service: MemoryService = None
contact_discovery_service: ContactDiscoveryService = None
auth_service: AuthService = None
agent = None
bearer_scheme = HTTPBearer(auto_error=False)


# ── Lifespan (startup/shutdown) ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global serper_service, llm_service, email_service, memory_service, contact_discovery_service, auth_service, agent

    logger.info("🔥 FireReach AI starting up...")

    # Validate config
    issues = settings.validate()
    for issue in issues:
        logger.warning("Config warning: %s", issue)

    # Initialize database
    await init_db(settings.DATABASE_URL)

    # Initialize services
    serper_service = SerperService(
        api_key=settings.SERPER_API_KEY,
        base_url=settings.SERPER_BASE_URL,
    )
    llm_service = LLMService(
        groq_api_key=settings.LLM_API_KEY,
        groq_model=settings.GROQ_MODEL,
        ollama_url=settings.OLLAMA_URL,
        ollama_model=settings.OLLAMA_MODEL,
    )
    email_service = EmailService(
        sendgrid_api_key=settings.SENDGRID_API_KEY,
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        from_email=settings.FROM_EMAIL,
        from_name=settings.FROM_NAME,
        google_client_id=settings.GOOGLE_CLIENT_ID,
        google_client_secret=settings.GOOGLE_CLIENT_SECRET,
    )

    session_factory = get_session_factory()
    memory_service = MemoryService(session_factory)
    auth_service = AuthService(
        session_factory=session_factory,
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    contact_discovery_service = ContactDiscoveryService(
        hunter_api_key=settings.HUNTER_API_KEY,
        serper_service=serper_service,
    )

    # Build LangGraph agent
    agent = build_agent_graph(
        serper_service=serper_service,
        llm_service=llm_service,
        memory_service=memory_service,
        contact_discovery_service=contact_discovery_service,
    )

    logger.info("✅ All services initialized. FireReach AI ready.")
    yield
    logger.info("🔥 FireReach AI shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="🔥 FireReach AI",
    description="Agentic signal-driven B2B outreach system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────────────
class RunAgentRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200, description="Company name to analyze")
    icp: str = Field(..., min_length=10, max_length=2000, description="Ideal Customer Profile")
    send_email: bool = Field(False, description="Whether to actually send the email")
    recipient_email: Optional[str] = Field(None, description="Target email address")
    target_titles: Optional[List[str]] = Field(
        default=None,
        description="Preferred contact titles for discovery",
    )


class BatchAnalyzeRequest(BaseModel):
    companies: List[str] = Field(..., min_length=1, max_length=20)
    icp: str = Field(..., min_length=10)
    send_emails: bool = False


class SendEmailRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    to_email: EmailStr
    subject: str = Field(..., min_length=3, max_length=300)
    body: str = Field(..., min_length=10, max_length=4000)


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _run_agent_for_company(
    company: str,
    icp: str,
    send_email: bool = False,
    recipient_email: Optional[str] = None,
    target_titles: Optional[List[str]] = None,
    user_id: Optional[int] = None,
    sender_name: Optional[str] = None,
    sender_contact_email: Optional[str] = None,
    sender_google_email: Optional[str] = None,
    sender_google_refresh_token: Optional[str] = None,
) -> dict:
    """Core agent execution logic, reused by single and batch endpoints.

    When send_email is True and a valid recipient + email body exist, this will
    automatically trigger delivery via the configured EmailService. Otherwise it
    only prepares a draft for manual review/send.
    """
    initial_state = {
        "company": company.strip(),
        "icp": icp.strip(),
        "send_email_flag": send_email,
        "recipient_email": recipient_email,
        "target_titles": target_titles or ["VP Engineering", "CTO", "Engineering Manager"],
        "user_id": user_id,
        "sender_name": sender_name or "FireReach Team",
        "sender_contact_email": sender_contact_email or "",
        "sender_google_email": sender_google_email,
        "sender_google_refresh_token": sender_google_refresh_token,
        "score_threshold": settings.SCORE_THRESHOLD,
        "status": "pending",
        "error": "",
        "email_sent": False,
    }

    final_state = await agent.ainvoke(initial_state)

    # Default: no auto-send
    final_state["email_sent"] = False
    final_state["email_send_result"] = None

    # Optional auto-send: only when explicitly requested and the run succeeded.
    if send_email and final_state.get("status") not in ("failed", "stopped"):
        body = (final_state.get("email") or "").strip()
        subject = (final_state.get("email_subject") or "").strip()
        recipient = (final_state.get("recipient_email") or "").strip()

        if body and subject and recipient:
            try:
                send_result = await email_service.send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body,
                    company=final_state.get("company", "").strip(),
                    sender_profile={
                        "name": sender_name or "FireReach User",
                        "reply_to": sender_contact_email,
                        "google_email": final_state.get("sender_google_email"),
                        "google_refresh_token": final_state.get("sender_google_refresh_token"),
                    },
                )
                final_state["email_send_result"] = send_result
                final_state["email_sent"] = send_result.get("status") == "sent"
                # Mark status as sent if everything else was OK.
                if final_state.get("status") == "email_ready" and final_state["email_sent"]:
                    final_state["status"] = "sent"
            except Exception as exc:
                logger.exception("Auto-send email failed: %s", exc)
                final_state["email_send_result"] = {
                    "status": "failed",
                    "error": str(exc),
                }

        # If send_email was requested but prerequisites were missing, keep status
        # as whatever the graph produced (e.g. email_ready / complete).

    # If send_email was False, keep status from the graph but ensure email_sent flag is False.
    return dict(final_state)


def _make_response(state: dict) -> dict:
    """Sanitize state dict for JSON response."""
    return {
        "status": state.get("status", "unknown"),
        "company": state.get("company"),
        "icp": state.get("icp"),
        "score": state.get("score", 0.0),
        "score_breakdown": state.get("score_breakdown"),
        "score_threshold": state.get("score_threshold", settings.SCORE_THRESHOLD),
        "signals": state.get("cleaned_signals") or state.get("signals"),
        "contact_candidates": state.get("contact_candidates", []),
        "contacts_found": state.get("contacts_found", len(state.get("contact_candidates", []))),
        "recipient_email": state.get("recipient_email"),
        "insights": state.get("insights"),
        "strategy": state.get("strategy"),
        "email": {
            "subject": state.get("email_subject"),
            "body": state.get("email"),
            "word_count": len((state.get("email") or "").split()),
        },
        "email_sent": state.get("email_sent", False),
        "email_send_result": state.get("email_send_result"),
        "created_at": state.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "error": state.get("error"),
    }


async def _resolve_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Optional[User]:
    if not credentials:
        return None
    if credentials.scheme.lower() != "bearer":
        return None
    return await auth_service.get_user_from_token(credentials.credentials)


async def require_user(user: Optional[User] = Depends(_resolve_user)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/run-agent", summary="Run full agent pipeline for one company")
async def run_agent(payload: RunAgentRequest, user: User = Depends(require_user)):
    """
    Execute the full 8-node LangGraph agent for a single company.

    - Fetches real signals from Serper
    - Analyzes with LLM (Groq → Ollama fallback)
    - Scores deterministically (0.0–1.0)
    - If score >= 0.5: generates personalized email
    - Optionally sends via SendGrid → SMTP
    - Stores in history DB
    """
    logger.info("POST /run-agent  company=%s", payload.company)
    try:
        state = await _run_agent_for_company(
            company=payload.company,
            icp=payload.icp,
            send_email=payload.send_email,
            recipient_email=payload.recipient_email,
            target_titles=payload.target_titles,
            user_id=user.id,
            sender_name=user.name,
            sender_contact_email=user.email,
            sender_google_email=user.google_email,
            sender_google_refresh_token=user.google_refresh_token,
        )
        return JSONResponse(content=_make_response(state))
    except Exception as exc:
        logger.exception("Agent run failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/batch-analyze", summary="Analyze multiple companies, ranked by score")
async def batch_analyze(payload: BatchAnalyzeRequest, user: User = Depends(require_user)):
    """
    Run agent on up to 20 companies concurrently. Returns results sorted by score.
    """
    import asyncio

    logger.info("POST /batch-analyze  companies=%s", payload.companies)
    try:
        tasks = [
            _run_agent_for_company(
                company=c,
                icp=payload.icp,
                send_email=False,
                user_id=user.id,
                sender_name=user.name,
                sender_contact_email=user.email,
                sender_google_email=user.google_email,
                sender_google_refresh_token=user.google_refresh_token,
            )
            for c in payload.companies
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed = []
        for company, result in zip(payload.companies, results):
            if isinstance(result, Exception):
                processed.append({
                    "company": company,
                    "status": "failed",
                    "error": str(result),
                    "score": 0.0,
                })
            else:
                processed.append(_make_response(result))

        # Sort by score descending
        processed.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return JSONResponse(content={
            "total": len(processed),
            "results": processed,
        })
    except Exception as exc:
        logger.exception("Batch analyze failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/send-email", summary="Send a generated outreach email")
async def send_email(payload: SendEmailRequest, user: User = Depends(require_user)):
    try:
        logger.info("POST /send-email  company=%s to=%s", payload.company, payload.to_email)
        result = await email_service.send_email(
            to_email=payload.to_email,
            subject=payload.subject.strip(),
            body=payload.body.strip(),
            company=payload.company.strip(),
            sender_profile={
                "name": user.name,
                "reply_to": user.email,
                "google_email": user.google_email,
                "google_refresh_token": user.google_refresh_token,
            },
        )
        logger.info(
            "Send email result: status=%s method=%s error=%s",
            result.get("status"),
            result.get("method"),
            result.get("error"),
        )
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("Send email failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/history", summary="Get outreach history")
async def get_history(
    user: User = Depends(require_user),
    company: Optional[str] = Query(None, description="Filter by company name"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Retrieve past outreach records, newest first."""
    try:
        records = await memory_service.get_history(
            user_id=user.id, company=company, limit=limit, offset=offset
        )
        return JSONResponse(content={"records": records, "count": len(records)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/status/{company}", summary="Check recent outreach status for a company")
async def get_status(company: str, user: User = Depends(require_user)):
    """Return whether we've recently contacted this company (dedup check)."""
    try:
        has_recent = await memory_service.has_recent_outreach(
            company, days=settings.DEDUP_DAYS, user_id=user.id
        )
        return JSONResponse(content={
            "company": company,
            "contacted_recently": has_recent,
            "dedup_window_days": settings.DEDUP_DAYS,
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/record/{record_id}", summary="Get a single outreach record")
async def get_record(record_id: int, user: User = Depends(require_user)):
    """Fetch details of a specific outreach run."""
    record = await memory_service.get_record(record_id, user_id=user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return JSONResponse(content=record)


@app.delete("/record/{record_id}", summary="Delete an outreach record")
async def delete_record(record_id: int, user: User = Depends(require_user)):
    deleted = await memory_service.delete_record(record_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return JSONResponse(content={"deleted": True, "id": record_id})


@app.get("/stats", summary="Dashboard statistics")
async def get_stats(user: User = Depends(require_user)):
    """Return aggregate stats for the dashboard."""
    try:
        stats = await memory_service.get_stats(user_id=user.id)
        return JSONResponse(content=stats)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health", summary="Service health check")
async def health():
    """Check health of all connected services."""
    llm_status = await llm_service.health_check()
    email_status = await email_service.validate_config()

    return JSONResponse(content={
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "llm": llm_status,
            "email": email_status,
            "serper": {"configured": bool(settings.SERPER_API_KEY)},
            "database": {"url": settings.DATABASE_URL.split("///")[0]},
        },
    })


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "🔥 FireReach AI is running. Visit /docs for API reference."}


@app.post("/auth/signup", summary="Create a user account")
async def signup(payload: SignupRequest):
    try:
        user = await auth_service.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
        token = auth_service.create_access_token(user)
        return JSONResponse(content={
            "access_token": token,
            "token_type": "bearer",
            "user": user.to_public_dict(),
        })
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login", summary="Login with email and password")
async def login(payload: LoginRequest):
    user = await auth_service.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth_service.create_access_token(user)
    return JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_public_dict(),
    })


@app.get("/auth/me", summary="Get current authenticated user")
async def me(user: User = Depends(require_user)):
    return JSONResponse(content={"user": user.to_public_dict()})


@app.post("/auth/google/start", summary="Start Google OAuth connect flow")
async def google_oauth_start(user: User = Depends(require_user)):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured on server")

    state_token = auth_service.create_access_token(user)
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.send",
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token,
    })
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    return JSONResponse(content={"auth_url": auth_url})


@app.get("/auth/google/callback", summary="Google OAuth callback")
async def google_oauth_callback(code: str, state: str):
    user = await auth_service.get_user_from_token(state)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid OAuth state")

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_res.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"OAuth token exchange failed: {token_res.text}")
        token_data = token_res.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Missing Google access token")

        profile_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_res.status_code >= 400:
            raise HTTPException(status_code=400, detail=f"Failed to fetch Google profile: {profile_res.text}")
        profile = profile_res.json()

    google_email = (profile.get("email") or "").strip().lower()
    if not google_email:
        raise HTTPException(status_code=400, detail="Google account email not available")

    await auth_service.update_google_oauth(
        user_id=user.id,
        google_email=google_email,
        refresh_token=refresh_token,
    )
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings?google=connected&email={google_email}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )
