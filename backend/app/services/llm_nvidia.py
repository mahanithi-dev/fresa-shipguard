import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from app.config import get_settings
from app.services.rate_limiter import ai_rate_limiter

logger = logging.getLogger("shipguard.ai")


def call_llm(prompt: str, system: str | None = None, max_tokens: int = 400) -> str:
    settings = get_settings()
    api_key = settings.nvidia_api_key
    api_url = getattr(settings, "nvidia_api_url", None)
    if not api_key or not api_url:
        raise RuntimeError("External LLM API key or URL not configured")

    if not ai_rate_limiter.check_and_record_provider_quota("nvidia"):
        logger.warning("NVIDIA daily API key quota reached. Falling back to local intelligence generator.")
        raise RuntimeError("NVIDIA API key daily quota reached")


    payload = {
        "model": getattr(settings, "nvidia_model", "gpt-4o") or "meta/llama-3.1-70b-instruct",
        "messages": [
            {"role": "system", "content": system or "You are ShipGuard AI, an expert logistics and freight forwarding risk intelligence assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ShipGuard-AI/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
        if "text" in choice:
            return choice["text"]

    return json.dumps(data)


def generate_fallback_explanation(shipment_summary: str, top_factors: Optional[list[dict]] = None) -> str:
    """Intelligent fallback explanation generator based on domain rules and risk factors."""
    factors = top_factors or []
    factor_names = [str(f.get("factor", "")).lower() for f in factors]
    
    analysis_points = []
    actions = []
    
    if any("carrier" in f for f in factor_names):
        analysis_points.append("Carrier historical on-time performance indicates potential operational variance on this lane.")
        actions.append("Request prioritized container handling and milestone confirmations from carrier dispatch.")
        
    if any("route" in f or "congestion" in f or "transit" in f for f in factor_names):
        analysis_points.append("Route transit characteristics or transshipment bottlenecks present a moderate-to-high delay probability.")
        actions.append("Establish active GPS/AIS transshipment checkpoint alerts and prepare alternate feeder routing.")
        
    if any("cargo" in f or "reefer" in f or "pharma" in f or "hazard" in f for f in factor_names):
        analysis_points.append("Specialized cargo requirements require expedited customs clearance to avoid dwell time penalties.")
        actions.append("Pre-clear customs documentation and coordinate pre-arrival inspection with terminal handling.")

    if not analysis_points:
        analysis_points.append("Shipment parameters indicate elevated transit variance based on historical freight forwarding risk vectors.")
        actions.append("Monitor milestone scan updates at origin port and confirm scheduled vessel/flight departure.")

    if len(actions) < 2:
        actions.append("Notify consignee ops desk with proactive ETA buffer tracking and exception escalations.")

    explanation = (
        f"**Risk Analysis:** {shipment_summary}\n\n"
        f"**Key Risk Drivers:**\n"
        + "\n".join(f"• {p}" for p in analysis_points)
        + "\n\n"
        f"**Recommended Operations Actions:**\n"
        + "\n".join(f"1. {a}" if i == 0 else f"2. {a}" for i, a in enumerate(actions[:2]))
    )
    return explanation


def explain_shipment_text(shipment_summary: str, top_factors: Optional[list[dict]] = None, retrieved_contexts: Optional[list[str]] = None) -> str:
    # 1. Try Google Gemini API first if configured
    try:
        from app.services.gemini_service import explain_shipment_with_gemini
        gemini_explanation = explain_shipment_with_gemini(shipment_summary, top_factors, retrieved_contexts)
        if gemini_explanation and gemini_explanation.strip():
            return gemini_explanation.strip()
    except Exception as e:
        logger.debug("Gemini explanation skipped: %s", e)

    # 2. Try external OpenAI/NVIDIA LLM if configured
    factors_text = ""
    if top_factors:
        factors_text = "\nTop factors:\n" + "\n".join([f"- {f.get('factor','')}: {f.get('value') or f.get('impact')}" for f in top_factors])

    context_text = ""
    if retrieved_contexts:
        context_text = "\nRetrieved context:\n" + "\n---\n".join(retrieved_contexts)

    prompt = (
        f"Here is a shipment summary:\n{shipment_summary}\n{factors_text}\n{context_text}\n\n"
        "Please provide a concise (3-5 sentence) plain-language explanation of why this shipment is at risk and suggest 2 practical mitigation actions for operations."
    )

    try:
        return call_llm(prompt)
    except Exception as e:
        logger.info("External LLM not available (%s), using ShipGuard AI Engine fallback", e)
        return generate_fallback_explanation(shipment_summary, top_factors)


