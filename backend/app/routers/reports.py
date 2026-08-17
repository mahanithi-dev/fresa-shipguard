import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.deps import get_current_user
from app.entities import Carrier, RiskScore, Route, Shipment

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.get("/export/csv")
def export_shipments_csv(
    status: Optional[str] = None,
    risk_tier: Optional[str] = None,
    mode: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Export filtered shipments as a structured CSV file."""
    query = db.query(Shipment).options(
        joinedload(Shipment.carrier),
        joinedload(Shipment.route),
        joinedload(Shipment.risk_score),
    )

    if status:
        query = query.filter(Shipment.status == status)
    if mode:
        query = query.filter(Shipment.mode == mode)
    if risk_tier:
        query = query.join(RiskScore, isouter=True).filter(RiskScore.risk_tier == risk_tier)

    shipments = query.order_by(Shipment.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "Shipment Ref",
        "Carrier",
        "Carrier Code",
        "Mode",
        "Origin Port",
        "Destination Port",
        "ETD",
        "ETA",
        "Actual Arrival",
        "Status",
        "Risk Tier",
        "Risk Score (%)",
        "Container No",
        "Vessel / Flight",
        "Disruption Event",
        "Consignee",
    ])

    for s in shipments:
        carrier_name = s.carrier.carrier_name if s.carrier else ""
        carrier_code = s.carrier.carrier_code if s.carrier else ""
        origin = s.route.origin_port if s.route else ""
        dest = s.route.dest_port if s.route else ""
        risk_tier_val = s.risk_score.risk_tier if s.risk_score else "UNSCORED"
        risk_score_pct = round((s.risk_score.risk_score or 0) * 100) if s.risk_score else 0

        writer.writerow([
            s.shipment_ref,
            carrier_name,
            carrier_code,
            s.mode,
            origin,
            dest,
            str(s.etd) if s.etd else "",
            str(s.eta) if s.eta else "",
            str(s.actual_arrival) if s.actual_arrival else "",
            s.status,
            risk_tier_val,
            risk_score_pct,
            getattr(s, "container_no", "") or "",
            getattr(s, "vessel_name", "") or "",
            getattr(s, "disruption_event", "") or "",
            getattr(s, "consignee", "") or "",
        ])

    csv_data = output.getvalue()
    filename = f"shipguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/summary")
def get_report_summary(db: Session = Depends(get_db)):
    """Generate executive logistics intelligence report summary."""
    shipments = db.query(Shipment).options(
        joinedload(Shipment.carrier),
        joinedload(Shipment.route),
        joinedload(Shipment.risk_score)
    ).all()

    total_count = len(shipments)
    delivered_count = sum(1 for s in shipments if s.status == "DELIVERED")
    delayed_count = sum(1 for s in shipments if s.status == "DELAYED")
    in_transit_count = sum(1 for s in shipments if s.status == "IN_TRANSIT")
    booked_count = sum(1 for s in shipments if s.status == "BOOKED")
    hold_count = sum(1 for s in shipments if s.status == "EXCEPTIONAL_HOLD")

    high_risk_count = 0
    med_risk_count = 0
    low_risk_count = 0
    total_risk_score_sum = 0
    scored_count = 0

    high_risk_exceptions = []

    for s in shipments:
        if s.risk_score:
            score = s.risk_score.risk_score or 0
            tier = s.risk_score.risk_tier or "UNSCORED"
            total_risk_score_sum += score
            scored_count += 1

            if tier == "HIGH":
                high_risk_count += 1
                high_risk_exceptions.append({
                    "id": s.shipment_id,
                    "ref": s.shipment_ref,
                    "carrier": s.carrier.carrier_name if s.carrier else "Unknown",
                    "route": f"{s.route.origin_port} -> {s.route.dest_port}" if s.route else "Unknown",
                    "mode": s.mode,
                    "eta": str(s.eta) if s.eta else "",
                    "status": s.status,
                    "score_pct": round(score * 100),
                    "disruption": getattr(s, "disruption_event", None),
                    "consignee": getattr(s, "consignee", None),
                })
            elif tier == "MEDIUM":
                med_risk_count += 1
            elif tier == "LOW":
                low_risk_count += 1

    avg_risk_pct = round((total_risk_score_sum / scored_count) * 100) if scored_count > 0 else 0

    # Carrier scorecards
    carriers = db.query(Carrier).all()
    carrier_scorecards = []
    for c in carriers:
        c_shipments = [s for s in shipments if s.carrier_id == c.carrier_id]
        if c_shipments:
            c_high = sum(1 for s in c_shipments if s.risk_score and s.risk_score.risk_tier == "HIGH")
            c_delayed = sum(1 for s in c_shipments if s.status == "DELAYED")
            carrier_scorecards.append({
                "carrier_name": c.carrier_name,
                "carrier_code": c.carrier_code,
                "on_time_pct": round((getattr(c, "on_time_pct_hist", 0) or 0) * 100, 1),
                "total_shipments": len(c_shipments),
                "delayed_count": c_delayed,
                "high_risk_count": c_high,
            })

    carrier_scorecards.sort(key=lambda x: x["total_shipments"], reverse=True)

    # Route trade lane analysis
    routes = db.query(Route).all()
    route_analytics = []
    for r in routes:
        r_shipments = [s for s in shipments if s.route_id == r.route_id]
        if r_shipments:
            r_high = sum(1 for s in r_shipments if s.risk_score and s.risk_score.risk_tier == "HIGH")
            route_analytics.append({
                "route_str": f"{r.origin_port} -> {r.dest_port}",
                "mode": r.mode,
                "avg_transit_days": r.avg_transit_days,
                "total_shipments": len(r_shipments),
                "high_risk_count": r_high,
            })

    route_analytics.sort(key=lambda x: x["high_risk_count"], reverse=True)

    return {
        "generated_at": datetime.now().isoformat(),
        "metrics": {
            "total_shipments": total_count,
            "delivered": delivered_count,
            "delayed": delayed_count,
            "in_transit": in_transit_count,
            "booked": booked_count,
            "hold": hold_count,
            "high_risk": high_risk_count,
            "medium_risk": med_risk_count,
            "low_risk": low_risk_count,
            "avg_risk_score_pct": avg_risk_pct,
        },
        "high_risk_exceptions": high_risk_exceptions[:12],
        "carrier_scorecards": carrier_scorecards,
        "route_analytics": route_analytics[:8],
    }
