import os
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case, func

from app.config import get_settings
from app.entities import Shipment, Carrier, Route, RiskScore, ExternalPortStatus, ExternalWeather
from app.services.rate_limiter import ai_rate_limiter

logger = logging.getLogger("shipguard.gemini")

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    genai = None
    types = None


def _build_logistics_context(db: Session) -> str:
    """Build live summary context of active shipments, high-risk items, carriers, and routes."""
    try:
        total_shipments = db.query(func.count(Shipment.shipment_id)).scalar() or 0
        risk_counts = db.query(
            func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)),
            func.sum(case((RiskScore.risk_tier == "MEDIUM", 1), else_=0)),
            func.sum(case((RiskScore.risk_tier == "LOW", 1), else_=0)),
        ).first()

        high_risk_count = risk_counts[0] or 0 if risk_counts else 0
        med_risk_count = risk_counts[1] or 0 if risk_counts else 0
        low_risk_count = risk_counts[2] or 0 if risk_counts else 0
        delayed_count = db.query(Shipment).filter(Shipment.status == "DELAYED").count()

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
        carriers = db.query(Carrier).order_by(Carrier.on_time_pct_hist.desc()).limit(6).all()
        routes = db.query(Route).limit(6).all()

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
            f"{c.carrier_name} ({c.carrier_code}): {round((getattr(c, 'on_time_pct_hist', 0) or 0) * 100)}% on-time"
            for c in carriers
        ]
        route_summary = [
            f"{r.origin_port} -> {r.dest_port} ({r.mode}, avg {r.avg_transit_days}d)"
            for r in routes
        ]

        context = (
            f"Active Operations Summary:\n"
            f"- Total Active Shipments: {total_shipments} | Delayed: {delayed_count}\n"
            f"- Risk Breakdown: High={high_risk_count}, Medium={med_risk_count}, Low={low_risk_count}\n"
            f"\nCarrier SLAs:\n" + "\n".join(f"  • {cs}" for cs in carrier_summary) +
            f"\n\nKey Routes:\n" + "\n".join(f"  • {rs}" for rs in route_summary) +
            f"\n\nActive Shipments Snapshot:\n" + "\n".join(recent_shipments)
        )
        return context
    except Exception as e:
        logger.warning("Error building logistics context: %s", e)
        return "Logistics Operations Active Worklist Snapshot Available."


def chat_with_gemini(messages: List[Dict[str, str]], db: Session) -> Dict[str, Any]:
    """Execute conversational turn using Google Gemini API or the built-in Logistics Intelligence Engine."""
    settings = get_settings()
    api_key = (settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or "").strip()
    user_query = messages[-1]["content"] if messages else "Hello"

    # If Gemini API Key is missing or placeholder, seamlessly use the ShipGuard Intelligence Engine
    if not api_key or api_key.startswith("AQ.") or "your-" in api_key.lower() or len(api_key) < 15:
        return {
            "reply": generate_logistics_chat_fallback(user_query, db),
            "status": "success",
            "model": "ShipGuard Logistics Intelligence Engine"
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
        "You are ShipGuard AI Co-Pilot, an intelligent, conversational, and highly capable assistant with full general intelligence as well as deep freight forwarding and logistics domain expertise. "
        "You must answer ANY request the user makes directly and helpfully — whether it is a general task (like picking a random number, doing math, answering questions, writing text) or deep logistics operations analysis (analyzing shipment delays, evaluating carriers, checking ports and weather, recommending mitigations).\n\n"
        f"Live System Operations Context:\n{logistics_context}\n\n"
        "Guidelines:\n"
        "- Respond directly and accurately to whatever the user asks.\n"
        "- If the user asks general or conversational questions (e.g. 'pick 1 to 10 number', 'tell me a joke', 'what is 25 * 4'), fulfill their request immediately.\n"
        "- If the user asks about shipments, format references like **SHP-2026-A0001** so they are bold and interactive.\n"
        "- Keep answers direct, friendly, and well-structured."
    )

    # 1. Try official google-genai SDK if available
    if HAS_GENAI and genai:
        try:
            client = genai.Client(api_key=api_key)
            formatted_contents = []
            for msg in messages[:-1]:
                role = "user" if msg.get("role") == "user" else "model"
                formatted_contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.get("content", ""))]
                    )
                )
            formatted_contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_query)]
                )
            )

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1024,
            )

            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=formatted_contents,
                config=config,
            )

            if response.text:
                return {
                    "reply": response.text.strip(),
                    "status": "success",
                    "model": settings.gemini_model
                }
        except Exception as e:
            logger.info("Google GenAI SDK call failed (%s), falling back to REST/Local Engine", e)

    # 2. Try Direct HTTP REST call with httpx (30-second timeout)
    try:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={api_key}"

        contents_payload = []
        for msg in messages[:-1]:
            role = "user" if msg.get("role") == "user" else "model"
            contents_payload.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })
        contents_payload.append({
            "role": "user",
            "parts": [{"text": user_query}]
        })

        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents_payload,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1024
            }
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return {
                            "reply": parts[0]["text"].strip(),
                            "status": "success",
                            "model": settings.gemini_model
                        }
            else:
                logger.warning("Gemini REST API returned status %s: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("Gemini REST API HTTP error (%s), using ShipGuard Intelligence Engine", e)

    # 3. Intelligent fallback using live database intelligence
    return {
        "reply": generate_logistics_chat_fallback(user_query, db),
        "status": "fallback",
        "model": "ShipGuard Logistics Intelligence Engine"
    }


def generate_logistics_chat_fallback(query: str, db: Session) -> str:
    """Intelligent, dynamic fallback chat engine that accurately answers general & logistics queries using live database context."""
    import re
    import random
    q_lower = query.lower().strip()

    # 1. Random number / range picking (e.g. "pick 1 to 10 number", "pick a number between 1 and 100")
    picker_match = re.search(r"(?:pick|choose|select|give me|random|roll).*?(\d+)\s*(?:to|and|-|thru|through)\s*(\d+)", q_lower)
    if picker_match:
        n1 = int(picker_match.group(1))
        n2 = int(picker_match.group(2))
        low, high = min(n1, n2), max(n1, n2)
        picked = random.randint(low, high)
        return f"🎲 I picked **{picked}** (from range {low} to {high})!"

    # Single number request (e.g. "pick a number", "random number")
    if "pick" in q_lower and ("number" in q_lower or "digit" in q_lower):
        picked = random.randint(1, 10)
        return f"🎲 I picked **{picked}** (from 1 to 10)!"

    # Coin flip & dice roll
    if "flip a coin" in q_lower or "coin flip" in q_lower or "toss a coin" in q_lower:
        side = random.choice(["Heads", "Tails"])
        return f"🪙 **{side}**!"

    if "roll a dice" in q_lower or "roll a die" in q_lower or "roll dice" in q_lower:
        dice = random.randint(1, 6)
        return f"🎲 You rolled a **{dice}**!"

    # Simple arithmetic (e.g. "what is 25 * 4", "calculate 120 + 35")
    math_match = re.search(r"(?:what is|calculate|compute|solve)?\s*(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)", q_lower)
    if math_match and ("what is" in q_lower or "calculate" in q_lower or any(op in q_lower for op in ["*", "+", "/", "-"])):
        try:
            val1 = float(math_match.group(1))
            op = math_match.group(2)
            val2 = float(math_match.group(3))
            if op == "+":
                res = val1 + val2
            elif op == "-":
                res = val1 - val2
            elif op == "*":
                res = val1 * val2
            elif op == "/":
                res = val1 / val2 if val2 != 0 else "undefined (division by zero)"
            
            res_str = int(res) if isinstance(res, float) and res.is_integer() else res
            return f"🧮 **{math_match.group(1)} {op} {math_match.group(2)} = {res_str}**"
        except Exception:
            pass

    # Jokes & fun
    if "joke" in q_lower or "funny" in q_lower:
        jokes = [
            "😄 *Why did the shipping container go to school?* Because it wanted to be a smart-box! 📦",
            "🚢 *Why do cargo ships make great comedians?* Because their delivery is always on point! ⚓",
            "✈️ *Why was the air freight pilot so good at customer service?* Because they always went above and beyond! 🛫",
        ]
        return random.choice(jokes)

    # 2. Greetings & capabilities inquiry
    if any(q_lower.startswith(w) for w in ["hi", "hello", "hey", "hola", "good morning", "good evening", "how are you", "who are you", "what can you do"]):
        total_count = db.query(Shipment).count()
        high_count = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").count()
        delayed_count = db.query(Shipment).filter(Shipment.status == "DELAYED").count()
        return (
            f"👋 **Hello! I am ShipGuard AI Co-Pilot.**\n\n"
            f"I am actively monitoring your freight operations across **{total_count} active shipments**.\n\n"
            f"**Current Operations Snapshot:**\n"
            f"• 🚨 **High-Risk Exceptions:** {high_count} shipment(s)\n"
            f"• ⏱️ **Delayed Shipments:** {delayed_count} shipment(s)\n\n"
            f"**You can ask me anything:**\n"
            f"• General queries (e.g. *'Pick 1 to 10 number'*, *'What is 15 * 8'*, *'Tell me a joke'*)\n"
            f"• Risk analysis: *'Summarize high risk shipments'*\n"
            f"• Shipment details: *'Inspect SHP-2026-A0001'*\n"
            f"• Carrier performance: *'Compare carrier reliability'*\n"
            f"• Port intelligence: *'Rotterdam weather and berth congestion'*\n"
            f"• Actions: *'Suggest route mitigations'* or *'Draft delay email'*"
        )

    # 2. Specific shipment reference lookup (e.g. SHP-2026-A0001, SHP-xxxx, or numeric ID)
    ref_match = re.search(r"(shp[-\w\d]+)", q_lower)
    target_ref = ref_match.group(1).upper() if ref_match else None

    if not target_ref and ("shipment" in q_lower or "track" in q_lower or "inspect" in q_lower):
        num_match = re.search(r"(?:shipment|id|ref|#)\s*([0-9]+)", q_lower)
        if num_match:
            ship_id = int(num_match.group(1))
            found_s = db.get(Shipment, ship_id)
            if found_s:
                target_ref = found_s.shipment_ref

    if target_ref:
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
            route_str = f"{s.route.origin_port} ➔ {s.route.dest_port}" if s.route else "Unknown Route"
            disruption = getattr(s, "disruption_event", None) or "None reported"

            factors_summary = "Standard route and carrier operational variance"
            if s.risk_score and s.risk_score.top_factors:
                try:
                    f_list = json.loads(s.risk_score.top_factors)
                    if isinstance(f_list, list) and f_list:
                        factors_summary = ", ".join([f"{f.get('factor')}: {f.get('value', f.get('impact', ''))}" for f in f_list[:3]])
                except Exception:
                    pass

            recommendation = (
                s.risk_score.recommendation
                if (s.risk_score and s.risk_score.recommendation)
                else "Confirm milestone checkpoint timestamp with carrier dispatch and alert receiving consignee."
            )

            return (
                f"📦 **Shipment Intelligence: {s.shipment_ref}**\n\n"
                f"• **Status:** `{s.status}` | **Risk Level:** **{tier}** ({score}% delay probability)\n"
                f"• **Carrier:** {carrier_name} ({s.carrier.carrier_code if s.carrier else 'N/A'})\n"
                f"• **Trade Lane:** {route_str} ({s.mode})\n"
                f"• **Schedule:** ETD {s.etd} ➔ ETA {s.eta}\n"
                f"• **Disruption Event:** {disruption}\n"
                f"• **Contributing Factors:** {factors_summary}\n\n"
                f"💡 **Recommended Action:** {recommendation}"
            )
        else:
            return f"🔍 I searched the active operations ledger but could not find a shipment matching reference **{target_ref}**. Please verify the reference number or try another query."

    # 3. Port / Weather / Congestion queries
    ports = ["rotterdam", "shanghai", "hamburg", "singapore", "jebel ali", "los angeles", "chennai", "tuticorin", "bengaluru", "mumbai", "frankfurt", "london", "ningbo", "shenzhen", "delhi", "colombo", "antwerp"]
    matched_port = next((p for p in ports if p in q_lower), None)
    if matched_port or ("weather" in q_lower or "port" in q_lower or "congestion" in q_lower or "berth" in q_lower):
        port_query_name = matched_port or "rotterdam"
        w = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{port_query_name}%")).first()
        p = db.query(ExternalPortStatus).filter(ExternalPortStatus.port_name.ilike(f"%{port_query_name}%")).first()
        port_title = port_query_name.capitalize()
        details = []
        if w:
            details.append(f"• 🌤️ **Weather:** {w.weather_condition} ({w.temperature_c}°C, {w.wind_speed_kmh} km/h wind, {w.precipitation_mm}mm precipitation)")
        if p:
            details.append(f"• ⚓ **Terminal Congestion:** {p.congestion_level} (Avg Vessel Berth Waiting: {p.avg_vessel_wait_hours} hrs)")

        active_in_port = db.query(Shipment).join(Route).filter(Route.dest_port.ilike(f"%{port_query_name}%") | Route.origin_port.ilike(f"%{port_query_name}%")).count()
        details.append(f"• 📦 **Active Worklist:** {active_in_port} shipment(s) currently traversing this gateway.")

        if not details:
            details.append("• ⚓ Standard terminal dwell times reported (normal operating parameters).")

        return (
            f"⚓ **Live Port & Weather Intelligence for {port_title}:**\n\n"
            + "\n".join(details)
            + "\n\n**Operational Advisory:** Factor berth waiting times into estimated delivery dates for consignee communications."
        )

    # 4. High-risk exceptions / delay queries
    if any(k in q_lower for k in ["high risk", "risk", "critical", "danger", "exception", "alert", "delayed", "late", "behind schedule"]):
        high_shipments = (
            db.query(Shipment)
            .options(
                joinedload(Shipment.carrier),
                joinedload(Shipment.route),
                joinedload(Shipment.risk_score),
            )
            .join(RiskScore)
            .filter(RiskScore.risk_tier == "HIGH")
            .order_by(RiskScore.risk_score.desc())
            .limit(5)
            .all()
        )
        if high_shipments:
            lines = [
                f"• **{s.shipment_ref}** ({s.carrier.carrier_name if s.carrier else 'Carrier'}) — {s.route.origin_port} ➔ {s.route.dest_port} (ETA: {s.eta}, Risk: **{round((s.risk_score.risk_score or 0)*100)}%**)"
                for s in high_shipments
            ]
            return (
                "🚨 **Critical High-Risk Exception Overview:**\n\n"
                "The following priority shipments have elevated risk scores and require operational intervention:\n\n"
                + "\n".join(lines)
                + "\n\n**Recommended Next Steps:**\n"
                "1. Contact carrier dispatch desks for urgent milestone updates.\n"
                "2. Send proactive delay advisories to consignees to manage delivery expectations."
            )
        return "✅ **Good News:** There are currently no critical high-risk shipments flagged in the active work queue."

    # 5. Carrier performance & SLA reliability
    carriers_names = ["maersk", "msc", "cma", "hapag", "one", "dhl", "cathay", "blue dart", "fedex", "kuehne"]
    matched_carrier = next((c for c in carriers_names if c in q_lower), None)
    if matched_carrier:
        c = db.query(Carrier).filter(Carrier.carrier_name.ilike(f"%{matched_carrier}%") | Carrier.carrier_code.ilike(f"%{matched_carrier}%")).first()
        if c:
            shipments_count = db.query(Shipment).filter(Shipment.carrier_id == c.carrier_id).count()
            delayed_count = db.query(Shipment).filter(Shipment.carrier_id == c.carrier_id, Shipment.status == "DELAYED").count()
            tier_desc = "Tier 1 (High Reliability)" if c.on_time_pct_hist >= 80 else "Tier 2 (Moderate Variance)" if c.on_time_pct_hist >= 70 else "Tier 3 (Elevated Delay Risk)"
            return (
                f"🚢 **Carrier Scorecard: {c.carrier_name} ({c.carrier_code})**\n\n"
                f"• **Historical On-Time Rate:** {c.on_time_pct_hist:.1f}%\n"
                f"• **Active Network Shipments:** {shipments_count}\n"
                f"• **Delayed Volume:** {delayed_count} shipment(s)\n"
                f"• **SLA Reliability Tier:** {tier_desc}\n\n"
                f"**Recommendation:** Prioritize for time-sensitive cargo when historical SLA exceeds 75%."
            )

    if any(k in q_lower for k in ["carrier", "carriers", "reliability", "leaderboard", "sla", "performance", "best carrier"]):
        carriers = db.query(Carrier).order_by(Carrier.on_time_pct_hist.desc()).limit(6).all()
        lines = [f"• **{c.carrier_name}** ({c.carrier_code}): **{c.on_time_pct_hist:.1f}%** historical on-time SLA" for c in carriers]
        return (
            "🚢 **Carrier Reliability & SLA Leaderboard:**\n\n"
            + "\n".join(lines)
            + "\n\n**Operational Insight:** Book priority air/ocean freight with carriers maintaining >75% on-time consistency to minimize demurrage and buffer time."
        )

    # 6. Email draft / customer notification templates
    if any(k in q_lower for k in ["email", "draft", "notify", "template", "message", "letter"]):
        sample_shipment = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").first()
        ref = sample_shipment.shipment_ref if sample_shipment else "SHP-2026-A0001"
        carrier = sample_shipment.carrier.carrier_name if sample_shipment and sample_shipment.carrier else "Ocean Network Express"
        eta = str(sample_shipment.eta) if sample_shipment else "Tomorrow"
        return (
            f"✉️ **Draft Delay Exception Notification Email:**\n\n"
            f"**Subject:** Shipment Delay Update — Ref #{ref}\n\n"
            f"Dear Customer Operations Team,\n\n"
            f"Please be advised that due to transshipment congestion along the scheduled trade lane, the estimated arrival for shipment **{ref}** with **{carrier}** has been updated to **{eta}**.\n\n"
            f"Our operations desk is actively tracking milestone checkpoint scans with carrier dispatch to minimize port dwell time and expedite destination customs clearance.\n\n"
            f"We will provide our next scheduled checkpoint update within 12 hours.\n\n"
            f"Best regards,\n"
            f"**ShipGuard Operations Desk**"
        )

    # 7. Mitigation playbooks & solutions
    if any(k in q_lower for k in ["mitigat", "action", "suggest", "recommend", "solution", "playbook", "sop", "fix"]):
        return (
            "💡 **ShipGuard Logistics Risk Mitigation Playbook:**\n\n"
            "1. **High Congestion Trade Lanes:** Pre-file customs entry manifests 48 hours prior to vessel/flight arrival to avert demurrage penalties.\n"
            "2. **Cold-Chain & Pharma Cargo:** Verify IoT temperature logger telemetry at origin handover and schedule priority bonded drayage.\n"
            "3. **Transshipment Delays (>48h):** Escalate to carrier regional port captain for priority container restow or coordinate secondary feeder connections."
        )

    # 8. General overview & status snapshot
    total_count = db.query(Shipment).count()
    high_count = db.query(Shipment).join(RiskScore).filter(RiskScore.risk_tier == "HIGH").count()
    delayed_count = db.query(Shipment).filter(Shipment.status == "DELAYED").count()
    in_transit_count = db.query(Shipment).filter(Shipment.status == "IN_TRANSIT").count()

    return (
        f"📊 **ShipGuard Operational Status Summary**\n\n"
        f"• **Total Active Cargo:** {total_count} shipments\n"
        f"• **In-Transit:** {in_transit_count} | **Delayed:** {delayed_count}\n"
        f"• **High-Risk Items Requiring Attention:** {high_count}\n\n"
        f"💡 **Suggested Prompts:**\n"
        f"• *'Summarize high risk shipments'*\n"
        f"• *'Compare carrier reliability'*\n"
        f"• *'Check Rotterdam port weather and congestion'*\n"
        f"• *'Draft a delay notification email'*"
    )


def explain_shipment_with_gemini(shipment_summary: str, top_factors: Optional[List[Dict[str, Any]]] = None, retrieved_contexts: Optional[List[str]] = None) -> Optional[str]:
    """Generate plain-language risk explanation for a specific shipment using Google Gemini."""
    settings = get_settings()
    api_key = (settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key or len(api_key) < 15:
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

    # Try SDK
    if HAS_GENAI and genai:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning("Gemini SDK error in explain_shipment: %s", e)

    # Try HTTP REST
    try:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
    except Exception as e:
        logger.warning("Gemini HTTP error in explain_shipment: %s", e)

    return None
