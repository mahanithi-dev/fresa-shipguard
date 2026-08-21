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


from sqlalchemy import case, func
from sqlalchemy.orm import joinedload


def _build_logistics_context(db: Session) -> str:
    """Build live summary context of active shipments, high-risk items, carriers, and routes."""
    try:
        total_shipments = db.query(func.count(Shipment.shipment_id)).scalar() or 0
        risk_counts = db.query(
            func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)),
            func.sum(case((RiskScore.risk_tier == "MEDIUM", 1), else_=0)),
            func.sum(case((RiskScore.risk_tier == "LOW", 1), else_=0)),
        ).first()

        high_risk_count = risk_counts[0] or 0
        med_risk_count = risk_counts[1] or 0
        low_risk_count = risk_counts[2] or 0

        recent_shipments_db = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.carrier),
                joinedload(Shipment.route),
                joinedload(Shipment.risk_score),
            )
            .order_by(Shipment.created_at.desc())
            .limit(10)
            .all()
        )
        carriers = db.query(Carrier).order_by(Carrier.on_time_pct_hist.desc()).limit(5).all()
        routes = db.query(Route).limit(5).all()

        recent_shipments = []
        for s in recent_shipments_db:
            tier = s.risk_score.risk_tier if s.risk_score else "UNSCORED"
            score = round((s.risk_score.risk_score or 0) * 100) if s.risk_score else 0
            carrier_name = s.carrier.carrier_name if s.carrier else "Unknown"
            route_str = f"{s.route.origin_port}->{s.route.dest_port}" if s.route else "Unknown"
            recent_shipments.append(
                f"- Ref: {s.shipment_ref} | Mode: {s.mode} | Carrier: {carrier_name} | Route: {route_str} | Status: {s.status} | Risk: {tier} ({score}%)"
            )

        carrier_summary = [
            f"{c.carrier_name} (Code: {c.carrier_code}, On-time rate: {round((getattr(c, 'on_time_pct_hist', 0) or 0) * 100)}%)"
            for c in carriers
        ]
        route_summary = [f"{r.origin_port} -> {r.dest_port} ({r.mode}, avg {r.avg_transit_days} days)" for r in routes]

        context = (
            f"Active Operations Summary:\n"
            f"- Total Active Shipments: {total_shipments}\n"
            f"- Risk Breakdown: High={high_risk_count}, Medium={med_risk_count}, Low={low_risk_count}\n"
            f"\nTop Carriers:\n" + "\n".join(f"  • {cs}" for cs in carrier_summary) +
            f"\n\nKey Routes:\n" + "\n".join(f"  • {rs}" for rs in route_summary) +
            f"\n\nRecent Active Shipments Snapshot:\n" + "\n".join(recent_shipments)
        )
        return context
    except Exception as e:
        logger.warning("Error building logistics context: %s", e)
        return "Logistics Operations Active Worklist Snapshot Available."


def chat_with_gemini(messages: List[Dict[str, str]], db: Session) -> Dict[str, Any]:
    """Execute chat turn using Google Gemini API or intelligent ShipGuard Logistics Engine."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY")
    user_query = messages[-1]["content"] if messages else "Hello"

    # If Gemini API Key is missing or placeholder, seamlessly use the ShipGuard Intelligence Engine
    if not api_key or api_key.startswith("AQ.") or "your-" in api_key.lower():
        return {
            "reply": generate_logistics_chat_fallback(user_query, db),
            "status": "success",
            "model": "ShipGuard Intelligence Engine"
        }

    logistics_context = _build_logistics_context(db)


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
    """Intelligent, multi-intent fallback chat engine that dynamically answers queries using live database context."""
    from app.entities import ExternalPortStatus, ExternalWeather

    q_lower = query.lower().strip()

    # 1. Check for specific shipment reference lookup (e.g., SHP-2026-A0001 or any ref match)
    import re
    ref_match = re.search(r"(shp[-\w\d]+)", q_lower)
    if ref_match:
        target_ref = ref_match.group(1).upper()
        s = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.carrier),
                joinedload(Shipment.route),
                joinedload(Shipment.risk_score),
            )
            .filter(Shipment.shipment_ref.ilike(f"%{target_ref}%"))
            .first()
        )
        if s:
            tier = s.risk_score.risk_tier if s.risk_score else "UNSCORED"
            score = round((s.risk_score.risk_score or 0) * 100) if s.risk_score else 0
            carrier_name = s.carrier.carrier_name if s.carrier else "Unknown Carrier"
            route_str = f"{s.route.origin_port} -> {s.route.dest_port}" if s.route else "Unknown Route"
            disruption = getattr(s, "disruption_event", None) or "None reported"

            factors_summary = "Standard route variance"
            if s.risk_score and s.risk_score.top_factors:
                try:
                    f_list = json.loads(s.risk_score.top_factors)
                    factors_summary = ", ".join([f"{f.get('factor')}: {f.get('value', '')}" for f in f_list[:3]])
                except Exception:
                    pass

            return (
                f"📦 **Shipment Analysis: {s.shipment_ref}**\n\n"
                f"• **Status:** {s.status} | **Risk Level:** {tier} ({score}%)\n"
                f"• **Carrier:** {carrier_name} ({s.carrier.carrier_code if s.carrier else 'N/A'})\n"
                f"• **Trade Lane:** {route_str} ({s.mode})\n"
                f"• **Schedule:** ETD {s.etd} → ETA {s.eta}\n"
                f"• **Disruption Alert:** {disruption}\n"
                f"• **Contributing Factors:** {factors_summary}\n\n"
                f"**Recommended Next Action:** {s.risk_score.recommendation if s.risk_score else 'Monitor milestone tracking updates.'}"
            )

    # 2. Check for port / weather / congestion queries
    ports = ["rotterdam", "shanghai", "hamburg", "singapore", "jebel ali", "los angeles", "chennai", "tuticorin", "bengaluru", "mumbai", "frankfurt", "london", "ningbo", "shenzhen", "delhi"]
    matched_port = next((p for p in ports if p in q_lower), None)
    if matched_port:
        w = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{matched_port}%")).first()
        p = db.query(ExternalPortStatus).filter(ExternalPortStatus.port_name.ilike(f"%{matched_port}%")).first()
        port_title = matched_port.capitalize()
        details = []
        if w:
            details.append(f"• **Weather:** {w.weather_condition} ({w.temperature_c}°C, {w.wind_speed_kmh} km/h wind, {w.precipitation_mm}mm rain)")
        if p:
            details.append(f"• **Terminal Congestion:** {p.congestion_level} (Avg Vessel Wait: {p.avg_vessel_wait_hours} hrs)")

        active_in_port = db.query(Shipment).join(Route).filter(Route.dest_port.ilike(f"%{matched_port}%") | Route.origin_port.ilike(f"%{matched_port}%")).count()
        details.append(f"• **Active Shipments on Lane:** {active_in_port} shipment(s) currently routed through this hub.")

        return f"⚓ **Live Port & Weather Intelligence for {port_title}:**\n\n" + "\n".join(details) + "\n\n**Operational Advisory:** Factor berth waiting times into estimated delivery dates for consignee communications."

    # 3. Check for high risk or risk summary queries
    if "high risk" in q_lower or "risk" in q_lower or "alert" in q_lower or "summarize" in q_lower or "exception" in q_lower:
        high_shipments = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.carrier),
                joinedload(Shipment.route),
                joinedload(Shipment.risk_score),
            )
            .join(RiskScore)
            .filter(RiskScore.risk_tier == "HIGH")
            .limit(5)
            .all()
        )
        if high_shipments:
            lines = [f"• **{s.shipment_ref}** ({s.carrier.carrier_name if s.carrier else 'Carrier'}) — {s.route.origin_port} -> {s.route.dest_port} (ETA: {s.eta}, Score: {round((s.risk_score.risk_score or 0)*100)}%)" for s in high_shipments]
            return "🚨 **High-Risk Exception Overview:**\n\nCurrently, the following critical shipments require proactive intervention:\n\n" + "\n".join(lines) + "\n\n**Recommended Action:** Contact carriers to verify container milestone timestamps and prepare alternate feeder connections."
        return "✅ **Good News:** There are currently no critical high-risk shipments detected in the active work queue."

    # 4. Check for carrier performance / reliability queries
    carriers_names = ["maersk", "msc", "cma", "hapag", "one", "dhl", "cathay", "blue dart"]
    matched_carrier = next((c for c in carriers_names if c in q_lower), None)
    if matched_carrier:
        c = db.query(Carrier).filter(Carrier.carrier_name.ilike(f"%{matched_carrier}%") | Carrier.carrier_code.ilike(f"%{matched_carrier}%")).first()
        if c:
            shipments_count = db.query(Shipment).filter(Shipment.carrier_id == c.carrier_id).count()
            delayed_count = db.query(Shipment).filter(Shipment.carrier_id == c.carrier_id, Shipment.status == "DELAYED").count()
            return (
                f"🚢 **Carrier Scorecard: {c.carrier_name} ({c.carrier_code})**\n\n"
                f"• **Historical On-Time Rate:** {c.on_time_pct_hist:.1f}%\n"
                f"• **Active Network Shipments:** {shipments_count}\n"
                f"• **Delayed Volume:** {delayed_count} shipment(s)\n"
                f"• **SLA Reliability Tier:** {'Tier 1 (High Reliability)' if c.on_time_pct_hist >= 80 else 'Tier 2 (Moderate Variance)' if c.on_time_pct_hist >= 70 else 'Tier 3 (Elevated Delay Risk)'}\n\n"
                f"**Recommendation:** Use for priority trade lanes when historical SLA exceeds 75%."
            )

    if "carrier" in q_lower or "reliability" in q_lower:
        carriers = db.query(Carrier).order_by(Carrier.on_time_pct_hist.desc()).limit(6).all()
        lines = [f"• **{c.carrier_name}** ({c.carrier_code}): {c.on_time_pct_hist:.1f}% on-time rate" for c in carriers]
        return "🚢 **Carrier Reliability Leaderboard:**\n\n" + "\n".join(lines) + "\n\n**Operational Insight:** Prioritize high-value bookings with carriers meeting SLA thresholds above 75%."

    # 5. Check for email draft / notification queries
    if "email" in q_lower or "draft" in q_lower or "notify" in q_lower or "template" in q_lower:
        sample_shipment = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").first()
        ref = sample_shipment.shipment_ref if sample_shipment else "SHP-2026-A0001"
        carrier = sample_shipment.carrier.carrier_name if sample_shipment and sample_shipment.carrier else "Ocean Network Express"
        eta = str(sample_shipment.eta) if sample_shipment else "Tomorrow"
        return (
            f"✉️ **Draft Delay Exception Notification Email:**\n\n"
            f"**Subject:** Shipment Delay Update — Ref #{ref}\n\n"
            f"Dear Customer Operations Team,\n\n"
            f"Please be advised that due to unforeseen transshipment congestion on the scheduled trade lane, the estimated arrival for shipment **{ref}** with **{carrier}** has been updated to **{eta}**.\n\n"
            f"Our operations desk is actively tracking milestone checkpoint scans with carrier dispatch to minimize port dwell time and expedite destination customs clearance.\n\n"
            f"We will provide our next scheduled checkpoint update within 12 hours.\n\n"
            f"Best regards,\n"
            f"**ShipGuard Operations Desk**"
        )

    # 6. Check for mitigation / recommendation queries
    if "mitigat" in q_lower or "action" in q_lower or "suggest" in q_lower or "recommend" in q_lower or "solution" in q_lower:
        return (
            "💡 **Logistics Risk Mitigation Playbook:**\n\n"
            "1. **High Congestion Trade Lanes:** Pre-book customs clearance manifests 48 hours prior to vessel arrival to avoid demurrage penalties.\n"
            "2. **Reefer & Cold-Chain Cargo:** Enable automated IoT container temperature telemetry alerts and prioritize dedicated drayage transport.\n"
            "3. **Carrier Escalations:** For delays exceeding 48 hours, trigger alternate feeder routing or request prioritized terminal discharge."
        )

    # 7. Default smart greeting & operational overview
    total_count = db.query(Shipment).count()
    high_count = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").count()
    delayed_count = db.query(Shipment).filter(Shipment.status == "DELAYED").count()

    return (
        f"👋 **ShipGuard Logistics Co-Pilot Active**\n\n"
        f"I am actively monitoring **{total_count} shipments** across your global forwarding network. Currently tracking **{high_count} high-risk exceptions** and **{delayed_count} delayed shipments**.\n\n"
        f"**What would you like to do?**\n"
        f"• 🚨 *'Summarize high risk shipments'*\n"
        f"• 🚢 *'Analyze carrier reliability'*\n"
        f"• ⚓ *'Check Rotterdam port weather and congestion'*\n"
        f"• 📦 *'Inspect shipment SHP-2026-A0001'*\n"
        f"• ✉️ *'Draft a delay notification email'*\n"
        f"• 💡 *'Suggest route mitigations'*"
    )



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

