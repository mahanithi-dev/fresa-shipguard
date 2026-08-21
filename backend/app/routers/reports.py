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


from sqlalchemy import case, func


@router.get("/export/csv")
def export_shipments_csv(
    status: Optional[str] = None,
    risk_tier: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = 5000,
    db: Session = Depends(get_db),
):
    """Export filtered shipments as a structured CSV file with a safety upper bound."""
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

    # Prevent unbounded CSV memory blowout
    max_export = min(max(1, limit), 10000)
    shipments = query.order_by(Shipment.created_at.desc()).limit(max_export).all()

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

        # Protect against CSV / Formula Injection
        from app.services.security import sanitize_csv_cell

        writer.writerow([
            sanitize_csv_cell(s.shipment_ref),
            sanitize_csv_cell(carrier_name),
            sanitize_csv_cell(carrier_code),
            sanitize_csv_cell(s.mode),
            sanitize_csv_cell(origin),
            sanitize_csv_cell(dest),
            sanitize_csv_cell(str(s.etd) if s.etd else ""),
            sanitize_csv_cell(str(s.eta) if s.eta else ""),
            sanitize_csv_cell(str(s.actual_arrival) if s.actual_arrival else ""),
            sanitize_csv_cell(s.status),
            sanitize_csv_cell(risk_tier_val),
            sanitize_csv_cell(str(risk_score_pct)),
            sanitize_csv_cell(getattr(s, "container_no", "") or ""),
            sanitize_csv_cell(getattr(s, "vessel_name", "") or ""),
            sanitize_csv_cell(getattr(s, "disruption_event", "") or ""),
            sanitize_csv_cell(getattr(s, "consignee", "") or ""),
        ])

    csv_data = output.getvalue()
    filename = f"shipguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/summary")
def get_report_summary(db: Session = Depends(get_db)):
    """Generate executive logistics intelligence report summary using direct SQL aggregations."""
    # 1. Total and Status metrics
    status_counts = dict(
        db.query(Shipment.status, func.count(Shipment.shipment_id))
        .group_by(Shipment.status)
        .all()
    )
    total_count = sum(status_counts.values())
    delivered_count = status_counts.get("DELIVERED", 0)
    delayed_count = status_counts.get("DELAYED", 0)
    in_transit_count = status_counts.get("IN_TRANSIT", 0)
    booked_count = status_counts.get("BOOKED", 0)
    hold_count = status_counts.get("EXCEPTIONAL_HOLD", 0)

    # 2. Risk breakdown metrics
    risk_stats = db.query(
        func.count(RiskScore.shipment_id),
        func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)),
        func.sum(case((RiskScore.risk_tier == "MEDIUM", 1), else_=0)),
        func.sum(case((RiskScore.risk_tier == "LOW", 1), else_=0)),
        func.avg(RiskScore.risk_score),
    ).first()

    scored_count = risk_stats[0] or 0
    high_risk_count = risk_stats[1] or 0
    med_risk_count = risk_stats[2] or 0
    low_risk_count = risk_stats[3] or 0
    avg_risk_score_raw = risk_stats[4] or 0.0
    avg_risk_pct = round(avg_risk_score_raw * 100) if scored_count > 0 else 0

    # 3. Top high risk exceptions (bounded eager query)
    high_risk_shipments = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.carrier),
            joinedload(Shipment.route),
            joinedload(Shipment.risk_score),
        )
        .join(RiskScore, Shipment.shipment_id == RiskScore.shipment_id)
        .filter(RiskScore.risk_tier == "HIGH")
        .order_by(RiskScore.risk_score.desc())
        .limit(12)
        .all()
    )

    high_risk_exceptions = [
        {
            "id": s.shipment_id,
            "ref": s.shipment_ref,
            "carrier": s.carrier.carrier_name if s.carrier else "Unknown",
            "route": f"{s.route.origin_port} -> {s.route.dest_port}" if s.route else "Unknown",
            "mode": s.mode,
            "eta": str(s.eta) if s.eta else "",
            "status": s.status,
            "score_pct": round((s.risk_score.risk_score or 0) * 100) if s.risk_score else 0,
            "disruption": getattr(s, "disruption_event", None),
            "consignee": getattr(s, "consignee", None),
        }
        for s in high_risk_shipments
    ]

    # 4. Carrier scorecards via SQL group aggregation
    carrier_rows = (
        db.query(
            Carrier.carrier_id,
            Carrier.carrier_name,
            Carrier.carrier_code,
            Carrier.on_time_pct_hist,
            func.count(Shipment.shipment_id).label("total_shipments"),
            func.sum(case((Shipment.status == "DELAYED", 1), else_=0)).label("delayed_count"),
            func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)).label("high_risk_count"),
        )
        .join(Shipment, Carrier.carrier_id == Shipment.carrier_id)
        .outerjoin(RiskScore, Shipment.shipment_id == RiskScore.shipment_id)
        .group_by(Carrier.carrier_id, Carrier.carrier_name, Carrier.carrier_code, Carrier.on_time_pct_hist)
        .order_by(func.count(Shipment.shipment_id).desc())
        .all()
    )

    carrier_scorecards = [
        {
            "carrier_name": row.carrier_name,
            "carrier_code": row.carrier_code,
            "on_time_pct": round((getattr(row, "on_time_pct_hist", 0) or 0) * 100, 1),
            "total_shipments": row.total_shipments or 0,
            "delayed_count": row.delayed_count or 0,
            "high_risk_count": row.high_risk_count or 0,
        }
        for row in carrier_rows
    ]

    # 5. Route trade lane analysis via SQL group aggregation
    route_rows = (
        db.query(
            Route.origin_port,
            Route.dest_port,
            Route.mode,
            Route.avg_transit_days,
            func.count(Shipment.shipment_id).label("total_shipments"),
            func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)).label("high_risk_count"),
        )
        .join(Shipment, Route.route_id == Shipment.route_id)
        .outerjoin(RiskScore, Shipment.shipment_id == RiskScore.shipment_id)
        .group_by(Route.route_id, Route.origin_port, Route.dest_port, Route.mode, Route.avg_transit_days)
        .order_by(func.sum(case((RiskScore.risk_tier == "HIGH", 1), else_=0)).desc())
        .limit(8)
        .all()
    )

    route_analytics = [
        {
            "route_str": f"{row.origin_port} -> {row.dest_port}",
            "mode": row.mode,
            "avg_transit_days": row.avg_transit_days,
            "total_shipments": row.total_shipments or 0,
            "high_risk_count": row.high_risk_count or 0,
        }
        for row in route_rows
    ]

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
        "high_risk_exceptions": high_risk_exceptions,
        "carrier_scorecards": carrier_scorecards,
        "route_analytics": route_analytics,
    }
