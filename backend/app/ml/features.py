"""Feature helpers for ShipGuard ML pipeline.

All historical aggregations are careful to use only completed shipments
with outcomes available before the shipment's `etd` to avoid data leakage.
"""
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.entities import Route, Shipment


def carrier_on_time_pct_as_of(db: Session, shipment: Shipment) -> float:
    """Percent of the carrier's prior shipments that were on-time as of shipment.etd.

    On-time is defined as delay of one day or less (i.e., (actual_arrival - eta).days <= 1).
    Only shipments with `actual_arrival` before `shipment.etd` are considered.
    Returns a percentage in [0, 100].
    """
    rows = db.query(Shipment.actual_arrival, Shipment.eta).filter(
        Shipment.carrier_id == shipment.carrier_id,
        Shipment.actual_arrival.isnot(None),
        Shipment.actual_arrival < shipment.etd,
    ).all()
    if not rows:
        return float(getattr(shipment.carrier, "on_time_pct_hist", 75.0) or 75.0)
    on_time = sum(1 for (actual_arrival, eta) in rows if (actual_arrival - eta).days <= 1)
    return round((on_time / len(rows)) * 100.0, 2)


def route_avg_delay_days_as_of(db: Session, shipment: Shipment) -> float:
    """Average historical delay (in days) for the same route as of shipment.etd.

    Only completed shipments with `actual_arrival` before `shipment.etd` are used.
    Returns a non-negative float; defaults to route.avg_transit_days deviation 0.0
    if no prior records exist.
    """
    rows = db.query(Shipment.actual_arrival, Shipment.eta).filter(
        Shipment.route_id == shipment.route_id,
        Shipment.actual_arrival.isnot(None),
        Shipment.actual_arrival < shipment.etd,
    ).all()
    if not rows:
        return 0.0
    # compute average (actual_arrival - eta).days
    delays = [max(0, (actual_arrival - eta).days) for (actual_arrival, eta) in rows]
    return float(sum(delays)) / float(len(delays))


def month_of_etd(shipment: Shipment) -> int:
    return int(shipment.etd.month) if shipment.etd else 0


def transit_days_planned(shipment: Shipment) -> int:
    return max(0, (shipment.eta - shipment.etd).days) if shipment.etd and shipment.eta else 0


def transit_vs_route_avg(db: Session, shipment: Shipment) -> float:
    route = shipment.route if getattr(shipment, "route", None) else db.get(Route, shipment.route_id)
    if not route:
        return 0.0
    return transit_days_planned(shipment) - (route.avg_transit_days or 0)


def build_feature_dict(db: Session, shipment: Shipment) -> Dict[str, Any]:
    return {
        "carrier_on_time_pct_as_of": carrier_on_time_pct_as_of(db, shipment),
        "route_avg_delay_days_as_of": route_avg_delay_days_as_of(db, shipment),
        "month_of_etd": month_of_etd(shipment),
        "mode": shipment.mode,
        "cargo_type": shipment.cargo_type,
        "transit_days_planned": transit_days_planned(shipment),
        "transit_vs_route_avg": transit_vs_route_avg(db, shipment),
    }


def label_from_shipment(shipment: Shipment) -> int:
    """Return 1 if shipment was delayed more than 1 day beyond ETA, else 0."""
    if not shipment.actual_arrival or not shipment.eta:
        return 0
    return 1 if (shipment.actual_arrival - shipment.eta).days > 1 else 0
