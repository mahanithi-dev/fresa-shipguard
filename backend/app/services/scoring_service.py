import json
import math
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.entities import (
    Carrier,
    ExternalCurrency,
    ExternalHoliday,
    ExternalPortStatus,
    ExternalWeather,
    RiskScore,
    Route,
    Shipment,
    ShipmentHistory,
)


RECOMMENDATIONS = {
    "HIGH": "Contact the carrier, request a fresh ETA, and review alternate routing or escalation options.",
    "MEDIUM": "Monitor closely and request proactive status updates before customer communication windows.",
    "LOW": "No immediate intervention required; continue normal milestone monitoring.",
}


def tier_for_score(score: float) -> str:
    if score >= 0.66:
        return "HIGH"
    if score >= 0.33:
        return "MEDIUM"
    return "LOW"


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _route_delay_as_of(db: Session, shipment: Shipment) -> float:
    # Uses SHIPMENT_HISTORY -> SHIPMENTS -> ROUTES and only outcomes before this shipment ETD.
    # Calculate average historical delay for the route using only history
    # records that occurred before the current shipment's ETD to avoid leakage.
    etd_dt = datetime.combine(shipment.etd, datetime.min.time()) if isinstance(shipment.etd, date) and not isinstance(shipment.etd, datetime) else shipment.etd
    avg_delay = (
        db.query(func.avg(ShipmentHistory.delay_days))
        .join(Shipment, Shipment.shipment_id == ShipmentHistory.shipment_id)
        .filter(Shipment.route_id == shipment.route_id)
        .filter(ShipmentHistory.event_ts.isnot(None))
        .filter(ShipmentHistory.event_ts < etd_dt)
        .scalar()
    )
    return float(avg_delay or 0)


def _carrier_reliability_as_of(db: Session, shipment: Shipment) -> float:
    # Compute carrier reliability based only on prior shipments that completed
    # before this shipment's ETD. Use actual_arrival when present; fall back to
    # the carrier's stored historical percentage if no prior data exists.
    rows = (
        db.query(Shipment)
        .filter(Shipment.carrier_id == shipment.carrier_id)
        .filter(Shipment.actual_arrival.isnot(None))
        .filter(Shipment.actual_arrival < shipment.etd)
        .all()
    )
    if not rows:
        return float(shipment.carrier.on_time_pct_hist or 70)
    on_time = sum(1 for row in rows if (row.actual_arrival - row.eta).days <= 1)
    return round((on_time / len(rows)) * 100, 2)


def score_shipment(db: Session, shipment: Shipment) -> RiskScore:
    route_delay = _route_delay_as_of(db, shipment)
    carrier_on_time = _carrier_reliability_as_of(db, shipment)
    planned_days = max((shipment.eta - shipment.etd).days, 1)
    route_avg = float(shipment.route.avg_transit_days or planned_days)
    transit_vs_avg = planned_days - route_avg
    month = shipment.etd.month

    score_input = 0.0
    score_input += (70 - carrier_on_time) / 18
    score_input += route_delay / 3.5
    score_input += 0.7 if month in {8, 9, 12} else 0
    score_input += 0.55 if shipment.cargo_type.lower() in {"reefer", "hazardous", "pharma"} else 0
    score_input += 0.35 if shipment.mode == "SEA" else 0.1 if shipment.mode == "LAND" else -0.15
    score_input += max(0, -transit_vs_avg) / 4
    base_score = round(_sigmoid(score_input - 1.2), 4)

    factors = [
        {
            "factor": "Carrier on-time rate",
            "value": f"{carrier_on_time:.0f}%",
            "impact": "high" if carrier_on_time < 65 else "medium" if carrier_on_time < 78 else "low",
            "source": "Historical Operational Data",
        },
        {
            "factor": "Route historical delay",
            "value": f"{route_delay:.1f} days",
            "impact": "high" if route_delay > 2 else "medium" if route_delay > 0.75 else "low",
            "source": "Historical Lane Telemetry",
        },
        {
            "factor": "Planned transit vs route average",
            "value": f"{transit_vs_avg:+.1f} days",
            "impact": "medium" if transit_vs_avg < 0 else "low",
            "source": "Route Baseline Schedule",
        },
    ]
    if month in {8, 9, 12}:
        factors.append({
            "factor": "Seasonality",
            "value": date(2026, month, 1).strftime("%B"),
            "impact": "medium",
            "source": "Seasonal Congestion Model"
        })

    # Integrate External Real-World Intelligence Factors
    external_risk_delta = 0.0

    # 1. Weather Factor (Origin / Destination)
    dest_name = shipment.route.dest_port.split("(")[0].strip()
    origin_name = shipment.route.origin_port.split("(")[0].strip()
    w_dest = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{dest_name}%")).first()
    w_orig = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{origin_name}%")).first()
    target_w = w_dest or w_orig

    if target_w:
        if target_w.is_severe or target_w.wind_speed_kmh > 40.0:
            external_risk_delta += 0.12
            factors.append({
                "factor": "Severe Weather Alert",
                "value": f"{target_w.weather_condition} ({target_w.wind_speed_kmh} km/h wind)",
                "impact": "high (+12%)",
                "source": target_w.data_source
            })
        elif target_w.precipitation_mm > 5.0:
            external_risk_delta += 0.04
            factors.append({
                "factor": "Weather Rainfall Impact",
                "value": f"{target_w.weather_condition} ({target_w.precipitation_mm}mm rain)",
                "impact": "low (+4%)",
                "source": target_w.data_source
            })

    # 2. Port Congestion Factor
    port_stat = db.query(ExternalPortStatus).filter(ExternalPortStatus.port_name.ilike(f"%{dest_name}%")).first()
    if port_stat:
        if port_stat.congestion_level in ["HIGH", "ELEVATED"]:
            external_risk_delta += 0.15
            factors.append({
                "factor": "Port Terminal Congestion",
                "value": f"{port_stat.congestion_level} ({port_stat.avg_vessel_wait_hours} hrs wait)",
                "impact": "high (+15%)",
                "source": port_stat.data_source
            })

    # 3. Destination Public Holiday Impact
    h_win_start = shipment.eta - timedelta(days=2)
    h_win_end = shipment.eta + timedelta(days=2)
    holiday = db.query(ExternalHoliday).filter(
        ExternalHoliday.holiday_date >= h_win_start,
        ExternalHoliday.holiday_date <= h_win_end
    ).first()
    if holiday:
        external_risk_delta += 0.05
        factors.append({
            "factor": "Public Holiday / Port Closure",
            "value": f"{holiday.holiday_name} ({holiday.holiday_date.strftime('%b %d')})",
            "impact": "medium (+5%)",
            "source": holiday.data_source
        })

    # 4. Currency Volatility Impact
    curr = db.query(ExternalCurrency).filter_by(base_currency="USD", target_currency="INR").first()
    if curr and curr.volatility_pct > 1.0:
        external_risk_delta += 0.02
        factors.append({
            "factor": "Currency Exchange Volatility",
            "value": f"USD/INR volatility {curr.volatility_pct}%",
            "impact": "low (+2%)",
            "source": curr.data_source
        })

    # Combine Base Score with External Data Additions
    final_score = round(min(0.99, max(0.01, base_score + external_risk_delta)), 4)
    tier = tier_for_score(final_score)

    existing = db.get(RiskScore, shipment.shipment_id)
    if existing is None:
        existing = RiskScore(shipment_id=shipment.shipment_id)
        db.add(existing)
    existing.risk_score = final_score
    existing.risk_tier = tier
    existing.top_factors = json.dumps(factors)
    existing.recommendation = RECOMMENDATIONS[tier]
    existing.scored_at = datetime.utcnow()
    db.commit()
    db.refresh(existing)
    return existing


def score_active_shipments(db: Session) -> int:
    shipments = db.query(Shipment).filter(Shipment.status.in_(["BOOKED", "IN_TRANSIT", "DELAYED"])).all()
    for shipment in shipments:
        score_shipment(db, shipment)
    return len(shipments)


def risk_to_dict(risk: RiskScore) -> dict:
    return {
        "shipment_id": risk.shipment_id,
        "risk_score": risk.risk_score,
        "risk_tier": risk.risk_tier,
        "top_factors": json.loads(risk.top_factors),
        "recommendation": risk.recommendation,
        "scored_at": risk.scored_at,
    }
