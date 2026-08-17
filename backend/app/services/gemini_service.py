import os
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config import get_settings
from app.entities import Shipment, Carrier, Route, RiskScore
from app.services.rate_limiter import ai_rate_limiter


logger = logging.getLogger("shipguard.gemini")

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None


def _build_logistics_context(db: Session) -> str:
    """Build live summary context of active shipments, high-risk items, carriers, and routes."""
    try:
        shipments = db.query(Shipment).all()
        carriers = db.query(Carrier).all()
        routes = db.query(Route).all()

        high_risk_count = 0
        med_risk_count = 0
        low_risk_count = 0
        recent_shipments = []

        for s in shipments[:15]:
            tier = s.risk_score.risk_tier if s.risk_score else "UNSCORED"
            score = round((s.risk_score.risk_score or 0) * 100) if s.risk_score else 0
            if tier == "HIGH":
                high_risk_count += 1
            elif tier == "MEDIUM":
                med_risk_count += 1
            elif tier == "LOW":
                low_risk_count += 1

            carrier_name = s.carrier.carrier_name if s.carrier else "Unknown"
            route_str = f"{s.route.origin_port}->{s.route.dest_port}" if s.route else "Unknown"
            recent_shipments.append(
                f"- Ref: {s.shipment_ref} | Mode: {s.mode} | Carrier: {carrier_name} | Route: {route_str} | Status: {s.status} | Risk: {tier} ({score}%)"
            )

        carrier_summary = [
            f"{c.carrier_name} (Code: {c.carrier_code}, On-time rate: {round((getattr(c, 'on_time_pct_hist', 0) or 0) * 100)}%)"
            for c in carriers[:5]
        ]
        route_summary = [f"{r.origin_port} -> {r.dest_port} ({r.mode}, avg {r.avg_transit_days} days)" for r in routes[:5]]

        context = (
            f"Active Operations Summary:\n"
            f"- Total Active Shipments: {len(shipments)}\n"
            f"- Risk Breakdown: High={high_risk_count}, Medium={med_risk_count}, Low={low_risk_count}\n"
            f"\nTop Carriers:\n" + "\n".join(f"  • {cs}" for cs in carrier_summary) +
            f"\n\nKey Routes:\n" + "\n".join(f"  • {rs}" for rs in route_summary) +
            f"\n\nRecent Active Shipments Snapshot:\n" + "\n".join(recent_shipments[:10])
        )
        return context
    except Exception as e:
        logger.warning("Error building logistics context: %s", e)
        return "Logistics Operations Active Worklist Snapshot Available."


def chat_with_gemini(messages: List[Dict[str, str]], db: Session) -> Dict[str, Any]:
    """Execute chat turn using Google Gemini API (gemini-3.6-flash)."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return {
            "reply": "⚠️ **Google Gemini API Key is missing.** Please ensure `GEMINI_API_KEY` is configured in `backend/.env`.",
            "status": "config_error"
        }

    logistics_context = _build_logistics_context(db)
    user_query = messages[-1]["content"] if messages else "Hello"

    # Enforce Gemini daily API key quota cap
    if not ai_rate_limiter.check_and_record_provider_quota("gemini"):
        logger.warning("Gemini daily API key quota reached. Seamlessly switching to ShipGuard Intelligence Engine.")
        return {
            "reply": generate_logistics_chat_fallback(user_query, db),
            "status": "fallback_quota_limit",
            "model": "ShipGuard Intelligence Engine (Quota Saver)"
        }

    system_instruction = (

        "You are ShipGuard AI Assistant, an expert logistics and freight forwarding operations co-pilot. "
        "Your task is to help operations managers analyze shipment risk, carrier reliability, route bottlenecks, "
        "and draft clear exception emails or mitigation recommendations.\n\n"
        f"Live System Context:\n{logistics_context}"
    )

    # Use google-genai Client if installed
    if HAS_GENAI and genai:
        try:
            client = genai.Client(api_key=api_key)

            # Build prompt with conversation history context
            prompt_parts = []
            for msg in messages[:-1]:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}")
            prompt_parts.append(f"User: {user_query}")
            
            full_prompt = "\n".join(prompt_parts)

            try:
                interaction = client.interactions.create(
                    model=settings.gemini_model,
                    input=full_prompt,
                    system_instruction=system_instruction,
                )
                output_text = interaction.output_text
            except Exception:
                # Fallback to models.generate_content if interactions endpoint is not active
                response = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=full_prompt,
                    config={"system_instruction": system_instruction}
                )
                output_text = response.text

            return {
                "reply": output_text,
                "status": "success",
                "model": settings.gemini_model
            }
        except Exception as e:
            logger.info("Gemini SDK call error/timeout (%s), using ShipGuard Intelligence Engine", e)
            return {
                "reply": generate_logistics_chat_fallback(user_query, db),
                "status": "fallback",
                "model": "ShipGuard Intelligence Engine"
            }
    else:
        # Fallback HTTP call if SDK is missing
        import urllib.request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\nUser Question: {user_query}"}]}]
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return {"reply": text, "status": "success", "model": settings.gemini_model}
        except Exception as e:
            logger.info("Gemini HTTP call error (%s), using ShipGuard Intelligence Engine", e)
            return {
                "reply": generate_logistics_chat_fallback(user_query, db),
                "status": "fallback",
                "model": "ShipGuard Intelligence Engine"
            }


def generate_logistics_chat_fallback(query: str, db: Session) -> str:
    """Intelligent fallback chat responses using database entities and operations rules."""
    q_lower = query.lower()
    if "high risk" in q_lower or "risk" in q_lower or "alert" in q_lower or "summarize" in q_lower:
        high_shipments = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").limit(5).all()
        if high_shipments:
            lines = [f"• **{s.shipment_ref}** ({s.carrier.carrier_name if s.carrier else 'Carrier'}) — {s.route.origin_port} -> {s.route.dest_port} (ETA: {s.eta})" for s in high_shipments]
            return "🚨 **High-Risk Exception Overview:**\n\nCurrently, the following critical shipments require immediate attention:\n\n" + "\n".join(lines) + "\n\n**Recommended Action:** Contact carriers to verify container milestone timestamps and prepare alternate feeder connections."
        return "✅ **Good News:** There are currently no critical high-risk shipments detected in the active work queue."

    if "carrier" in q_lower or "reliability" in q_lower or "delay" in q_lower:
        carriers = db.query(Carrier).order_by(Carrier.on_time_pct_hist.desc()).limit(5).all()
        lines = [f"• **{c.carrier_name}** ({c.carrier_code}): {c.on_time_pct_hist:.1f}% on-time rate" for c in carriers]
        return "🚢 **Carrier Reliability Summary:**\n\n" + "\n".join(lines) + "\n\n**Insight:** Prioritize high-value bookings with carriers meeting SLA thresholds above 75%."

    if "email" in q_lower or "draft" in q_lower:
        return "✉️ **Draft Delay Notification Email:**\n\n**Subject:** Delay Notification - Shipment Update for Ref #[Shipment Ref]\n\nDear Consignee Operations Team,\n\nPlease be advised that due to unforeseen port congestion and transit variance on the scheduled trade lane, the estimated arrival for shipment **[Shipment Ref]** has been adjusted to **[New ETA]**.\n\nOur logistics desk is actively tracking milestone checkpoint scans with carrier dispatch to minimize dwell time.\n\nBest regards,\n**ShipGuard Operations Desk**"

    return "👋 **ShipGuard Logistics Co-Pilot:**\n\nI am monitoring live trade lane status, carrier performance, and port congestion across your freight network.\n\nYou can ask me to:\n- 🚨 *'Summarize high risk shipments'*\n- 🚢 *'Analyze carrier on-time performance'*\n- ✉️ *'Draft a delay notification email'*\n- 💡 *'Suggest route mitigations'*"



def explain_shipment_with_gemini(shipment_summary: str, top_factors: Optional[List[Dict[str, Any]]] = None, retrieved_contexts: Optional[List[str]] = None) -> Optional[str]:
    """Generate plain-language risk explanation for a specific shipment using Google Gemini."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    if not ai_rate_limiter.check_and_record_provider_quota("gemini"):
        logger.warning("Gemini daily API key quota reached in explain_shipment. Falling back to local engine.")
        return None


    factors_text = ""
    if top_factors:
        factors_text = "\nContributing Risk Factors:\n" + "\n".join([f"- {f.get('factor','')}: {f.get('value') or f.get('impact')}" for f in top_factors])

    context_text = ""
    if retrieved_contexts:
        context_text = "\nRetrieved Live Intelligence Context:\n" + "\n---\n".join(retrieved_contexts)

    prompt = (
        f"You are ShipGuard AI, an expert freight forwarding risk intelligence assistant.\n"
        f"Analyze this shipment and provide a concise, professional risk summary (3-4 sentences) highlighting the primary drivers "
        f"and 2 clear, actionable mitigation steps for freight forwarders.\n\n"
        f"Shipment Summary:\n{shipment_summary}\n"
        f"{factors_text}\n"
        f"{context_text}"
    )

    if HAS_GENAI and genai:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            logger.warning("Gemini SDK error in explain_shipment: %s", e)

    # Fallback HTTP
    import urllib.request
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.warning("Gemini HTTP error in explain_shipment: %s", e)
        return None

