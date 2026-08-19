import datetime
from app.entities import Carrier, Route, Shipment
from app.services.scoring_service import score_shipment, tier_for_score, risk_to_dict


def test_tier_for_score_thresholds():
    assert tier_for_score(0.85) == "HIGH"
    assert tier_for_score(0.66) == "HIGH"
    assert tier_for_score(0.50) == "MEDIUM"
    assert tier_for_score(0.33) == "MEDIUM"
    assert tier_for_score(0.20) == "LOW"
    assert tier_for_score(0.01) == "LOW"


def test_score_shipment_persists_risk_score(db):
    carrier = db.query(Carrier).first()
    route = db.query(Route).first()

    shipment = Shipment(
        shipment_ref="SHP-PERSIST-TEST",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode=route.mode,
        cargo_type="Pharma",
        etd=datetime.date(2026, 9, 1),
        eta=datetime.date(2026, 9, 15),
        status="BOOKED"
    )
    db.add(shipment)
    db.commit()

    risk_record = score_shipment(db, shipment)
    assert risk_record is not None
    assert risk_record.shipment_id == shipment.shipment_id
    assert 0.0 <= risk_record.risk_score <= 1.0
    assert risk_record.risk_tier in ("LOW", "MEDIUM", "HIGH")
    assert risk_record.recommendation is not None

    # Test dictionary serialization
    risk_dict = risk_to_dict(risk_record)
    assert risk_dict["risk_score"] == risk_record.risk_score
    assert isinstance(risk_dict["top_factors"], list)
