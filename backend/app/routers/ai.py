import os
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.entities import Shipment, User
from app.services.llm_nvidia import explain_shipment_text
from app.services.retrieval import query as retrieval_query
from app.services.gemini_service import chat_with_gemini
from app.services.rate_limiter import check_ai_rate_limit, ai_rate_limiter
from app.config import get_settings


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


@router.get("/status")
def ai_status(user: User = Depends(get_current_user)):
    settings = get_settings()
    has_gemini = bool(settings.gemini_api_key or os.environ.get("GEMINI_API_KEY"))
    has_nvidia = bool(settings.nvidia_api_key and getattr(settings, "nvidia_api_url", None))
    rate_key = f"user_{user.user_id}" if user else "user_default"
    quota = ai_rate_limiter.get_quota_status(rate_key)
    return {
        "configured": has_gemini or has_nvidia,
        "gemini_active": has_gemini,
        "gemini_model": settings.gemini_model,
        "nvidia_active": has_nvidia,
        "nvidia_model": getattr(settings, "nvidia_model", "gpt-4o"),
        "rate_limiting": {
            "enabled": True,
            "quota_status": quota
        }
    }



@router.post("/chat", dependencies=[Depends(check_ai_rate_limit)])
def chat_ai(payload: ChatRequest, db: Session = Depends(get_db)):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="Messages array cannot be empty")
    messages_dicts = [{"role": m.role, "content": m.content} for m in payload.messages]
    result = chat_with_gemini(messages_dicts, db)
    return result


@router.get("/explain/{shipment_id}", dependencies=[Depends(check_ai_rate_limit)])
def explain_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")

    # build a short summary from shipment fields
    summary = (
        f"Ref: {shipment.shipment_ref}; Carrier: {shipment.carrier.carrier_name}; "
        f"Route: {shipment.route.origin_port} -> {shipment.route.dest_port}; Mode: {shipment.mode}; "
        f"ETD: {shipment.etd}; ETA: {shipment.eta}; Status: {shipment.status}."
    )

    top_factors = []
    if shipment.risk_score:
        try:
            import json
            top_factors = json.loads(shipment.risk_score.top_factors)
        except Exception:
            top_factors = []

    # perform retrieval to gather supporting contexts
    retrieved = retrieval_query(summary, top_k=3)
    contexts = [t for (_id, t, score) in retrieved]

    try:
        text = explain_shipment_text(summary, top_factors, retrieved_contexts=contexts)
    except Exception as exc:
        text = f"Shipment {shipment.shipment_ref} is experiencing risk variance across active transport vectors. Recommended action: coordinate proactive milestone review with {shipment.carrier.carrier_name if shipment.carrier else 'carrier'}."

    return {
        "explanation": text,
        "shipment_ref": shipment.shipment_ref,
        "mode": shipment.mode,
        "status": shipment.status
    }
