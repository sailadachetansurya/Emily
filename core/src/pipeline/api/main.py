"""
Emily FastAPI Server
"""

from __future__ import annotations

from datetime import datetime
import os
import sqlite3
from typing import Any, Optional
import uuid

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline.api.persistence import (
    authenticate_user,
    consume_rate_limit,
    consume_password_reset_token,
    create_password_reset_token,
    create_session,
    create_user,
    delete_draft,
    delete_entry,
    get_user_by_token,
    init_db,
    list_drafts,
    list_entries,
    revoke_session,
    revoke_user_sessions,
    save_draft,
    save_entry,
    update_entry,
)
from pipeline.contracts.models import RequestEnvelope
from pipeline.orchestrator.pipeline import EmotivePipeline

app = FastAPI(
    title="Emily API",
    description="Emotive AI Pipeline for ECHO - Emotional Chronicle",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("ECHO_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

_pipeline: Optional[EmotivePipeline] = None


def get_pipeline() -> EmotivePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = EmotivePipeline()
    return _pipeline


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return value


def _require_user(authorization: Optional[str]) -> dict[str, Any]:
    token = _extract_bearer_token(authorization)
    user = get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def _rate_key(prefix: str, request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{prefix}:{host}"


def _enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    ok = consume_rate_limit(key, limit, window_seconds)
    if not ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


class AnalyzeRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}")
    user_id: str = Field(default="default-user")
    user_input: str
    trace_id: str = Field(default_factory=lambda: f"trace-{uuid.uuid4().hex[:12]}")
    metadata: Optional[dict[str, Any]] = None


class EmotionStateResponse(BaseModel):
    emotional_valence: float
    activation_level: str
    social_orientation: str
    stability: str
    signals: dict[str, float]


class TraceResponse(BaseModel):
    stage_name: str
    status: str
    metadata: Optional[dict[str, Any]] = None


class SafeResponseData(BaseModel):
    text: str
    was_regenerated: bool
    safety_notes: list[str]


class AnalyzeResponse(BaseModel):
    request_id: str
    response: SafeResponseData
    traces: list[TraceResponse]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    status: str
    pipeline_loaded: bool
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=256)


class LoginRequest(BaseModel):
    username: str
    password: str


class ResetRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class ResetConfirmRequest(BaseModel):
    token: str = Field(min_length=8)
    new_password: str = Field(min_length=6, max_length=256)


class AuthResponse(BaseModel):
    token: str
    user_id: str
    username: str


class DraftRequest(BaseModel):
    text: str = Field(min_length=1)
    mood: Optional[str] = None


class DraftResponse(BaseModel):
    id: str
    text: str
    mood: Optional[str] = None
    createdAt: str


class EntryResponse(BaseModel):
    id: str
    text: str
    mood: Optional[str] = None
    responseText: str
    emotionState: Optional[dict[str, Any]] = None
    createdAt: str


class EntryUpdateRequest(BaseModel):
    text: str = Field(min_length=1)
    mood: Optional[str] = None


@app.get("/")
async def root():
    return {"name": "Emily API", "version": "0.2.0", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", pipeline_loaded=_pipeline is not None)


@app.post("/api/pipeline/analyze", response_model=AnalyzeResponse)
async def analyze_journal(
    request: AnalyzeRequest,
    raw_request: Request,
    authorization: Optional[str] = Header(default=None),
):
    _enforce_rate_limit(_rate_key("analyze", raw_request), 30, 60)
    try:
        pipeline = get_pipeline()
        user = None
        if authorization:
            token = _extract_bearer_token(authorization)
            user = get_user_by_token(token)

        effective_user_id = request.user_id if user is None else user["username"]
        envelope = RequestEnvelope(
            request_id=request.request_id,
            user_id=effective_user_id,
            user_input=request.user_input,
            trace_id=request.trace_id,
            metadata=request.metadata or {},
        )
        result = pipeline.run(envelope)

        payload = AnalyzeResponse(
            request_id=result.request_id,
            response=SafeResponseData(
                text=result.response.text,
                was_regenerated=result.response.was_regenerated,
                safety_notes=result.response.safety_notes,
            ),
            traces=[
                TraceResponse(stage_name=trace.stage_name, status=trace.status, metadata=trace.metadata)
                for trace in result.traces
            ],
        )

        if user is not None:
            emotion_state: Optional[dict[str, Any]] = None
            for trace in result.traces:
                if trace.stage_name == "emotion_perception":
                    emotion_state = trace.metadata.get("emotion") if isinstance(trace.metadata, dict) else None
                    break
            save_entry(
                entry_id=f"entry-{uuid.uuid4().hex[:16]}",
                user_id=user["id"],
                text=request.user_input,
                mood=(request.metadata or {}).get("mood"),
                response_text=result.response.text,
                emotion_state=emotion_state,
            )
        return payload
    except Exception as e:
        return AnalyzeResponse(
            request_id=request.request_id,
            response=SafeResponseData(
                text="I am here with you. Want to unpack this one step at a time?",
                was_regenerated=True,
                safety_notes=["Pipeline error - fallback response"],
            ),
            traces=[TraceResponse(stage_name="error", status="error", metadata={"error": str(e)})],
        )


@app.post("/api/emotion", response_model=EmotionStateResponse)
async def get_emotion_state(text: str):
    try:
        pipeline = get_pipeline()
        envelope = RequestEnvelope(
            request_id=f"emotion-{uuid.uuid4().hex[:8]}",
            user_id="emotion-only",
            user_input=text,
            trace_id=f"trace-{uuid.uuid4().hex[:8]}",
        )
        emotion = pipeline.emotion_engine.infer(envelope)
        return EmotionStateResponse(
            emotional_valence=emotion.emotional_valence,
            activation_level=emotion.activation_level,
            social_orientation=emotion.social_orientation,
            stability=emotion.stability,
            signals=emotion.signals,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest, raw_request: Request):
    _enforce_rate_limit(_rate_key("auth-register", raw_request), 8, 60)
    try:
        user = create_user(request.username.strip().lower(), request.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already exists")
    revoke_user_sessions(user["id"])
    token = create_session(user["id"])
    return AuthResponse(token=token, user_id=str(user["id"]), username=user["username"])


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest, raw_request: Request):
    _enforce_rate_limit(_rate_key("auth-login", raw_request), 12, 60)
    user = authenticate_user(request.username.strip().lower(), request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    revoke_user_sessions(user["id"])
    token = create_session(user["id"])
    return AuthResponse(token=token, user_id=str(user["id"]), username=user["username"])


@app.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(default=None)):
    token = _extract_bearer_token(authorization)
    revoke_session(token)
    return {"ok": True}


@app.get("/api/auth/me")
async def me(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    return {"user_id": str(user["id"]), "username": user["username"]}


@app.post("/api/auth/password-reset/request")
async def request_password_reset(request: ResetRequest, raw_request: Request):
    _enforce_rate_limit(_rate_key("auth-reset-request", raw_request), 6, 60)
    token = create_password_reset_token(request.username.strip().lower())
    return {"ok": True, "reset_token": token}


@app.post("/api/auth/password-reset/confirm")
async def confirm_password_reset(request: ResetConfirmRequest, raw_request: Request):
    _enforce_rate_limit(_rate_key("auth-reset-confirm", raw_request), 10, 60)
    ok = consume_password_reset_token(request.token, request.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"ok": True}


@app.get("/api/data/entries", response_model=list[EntryResponse])
async def get_entries(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    return list_entries(user["id"], limit=200)


@app.put("/api/data/entries/{entry_id}", response_model=EntryResponse)
async def modify_entry(entry_id: str, request: EntryUpdateRequest, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    updated = update_entry(user_id=user["id"], entry_id=entry_id, text=request.text, mood=request.mood)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry not found")
    for entry in list_entries(user["id"], limit=200):
        if entry["id"] == entry_id:
            return entry
    raise HTTPException(status_code=404, detail="Entry not found")


@app.delete("/api/data/entries/{entry_id}")
async def remove_entry(entry_id: str, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    deleted = delete_entry(user_id=user["id"], entry_id=entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"ok": True}


@app.get("/api/data/drafts", response_model=list[DraftResponse])
async def get_drafts(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    return list_drafts(user["id"], limit=200)


@app.post("/api/data/drafts", response_model=DraftResponse)
async def create_draft(request: DraftRequest, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    draft_id = f"draft-{uuid.uuid4().hex[:16]}"
    save_draft(draft_id=draft_id, user_id=user["id"], text=request.text, mood=request.mood)
    return DraftResponse(id=draft_id, text=request.text, mood=request.mood, createdAt=datetime.utcnow().isoformat())


@app.delete("/api/data/drafts/{draft_id}")
async def remove_draft(draft_id: str, authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    deleted = delete_draft(user_id=user["id"], draft_id=draft_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"ok": True}


@app.get("/api/data/insights")
async def get_user_insights(authorization: Optional[str] = Header(default=None)):
    user = _require_user(authorization)
    entries = list_entries(user["id"], limit=200)
    if not entries:
        return {"insights": ["No insights yet. Add journal entries first."]}

    avg_valence = 0.0
    seen_valence = 0
    trigger_counts: dict[str, int] = {}
    for entry in entries:
        emotion = entry.get("emotionState") or {}
        if isinstance(emotion, dict) and isinstance(emotion.get("emotional_valence"), (float, int)):
            avg_valence += float(emotion["emotional_valence"])
            seen_valence += 1
        for trigger in ["work", "social", "night", "money", "family", "friend"]:
            if trigger in entry["text"].lower():
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

    if seen_valence > 0:
        avg_valence /= seen_valence
    top_trigger = max(trigger_counts, key=trigger_counts.get) if trigger_counts else None
    insights = [
        "Recent trend looks emotionally low." if avg_valence < -0.2 else "Recent trend looks stable or improving.",
        f"Total entries analyzed: {len(entries)}.",
    ]
    if top_trigger:
        insights.append(f"Most frequent theme: {top_trigger}.")
    return {"insights": insights}


@app.on_event("startup")
async def startup_event():
    global _pipeline
    print("🚀 Starting Emily API server...")
    init_db()
    if os.getenv("ECHO_SKIP_PIPELINE_PRELOAD", "0") == "1":
        print("⚠️ Pipeline preload skipped by env")
        return
    _pipeline = EmotivePipeline()
    print("✅ Pipeline loaded successfully")


@app.on_event("shutdown")
async def shutdown_event():
    global _pipeline
    print("👋 Shutting down Emily API server...")
    _pipeline = None
