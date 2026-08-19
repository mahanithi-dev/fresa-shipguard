import datetime
from app.entities import Carrier, Route, Shipment, ShipmentHistory
from app.ml.features import carrier_on_time_pct_as_of, route_avg_delay_days_as_of


def test_route_avg_delay_zero_leakage(db):
    """
    Verifies that historical route delay calculations strictly ignore
    any history events timestamped AFTER the target shipment's ETD.
    """
    carrier = db.query(Carrier).first()
    route = db.query(Route).filter(Route.mode == "SEA").first()

    # Shipment 1: historical event occurred before test shipment ETD (delay = 2 days)
    s1 = Shipment(
        shipment_ref="SHP-PAST-1",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="SEA",
        cargo_type="General",
        etd=datetime.date(2026, 1, 1),
        eta=datetime.date(2026, 1, 26),
        status="DELIVERED",
        actual_arrival=datetime.date(2026, 1, 28)
    )
    db.add(s1)
    db.commit()

    h1 = ShipmentHistory(
        shipment_id=s1.shipment_id,
        event_type="ARRIVED",
        event_ts=datetime.datetime(2026, 1, 28, 12, 0),
        delay_days=2.0
    )
    db.add(h1)

    # Shipment 2: historical event occurred AFTER test shipment ETD (delay = 10 days)
    s2 = Shipment(
        shipment_ref="SHP-FUTURE-2",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="SEA",
        cargo_type="General",
        etd=datetime.date(2026, 6, 1),
        eta=datetime.date(2026, 6, 26),
        status="DELIVERED",
        actual_arrival=datetime.date(2026, 7, 6)
    )
    db.add(s2)
    db.commit()

    h2 = ShipmentHistory(
        shipment_id=s2.shipment_id,
        event_type="ARRIVED",
        event_ts=datetime.datetime(2026, 7, 6, 12, 0),
        delay_days=10.0
    )
    db.add(h2)
    db.commit()

    # Test shipment with ETD in March 2026 (after h1, but before h2)
    test_shipment = Shipment(
        shipment_ref="SHP-TEST-EVAL",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="SEA",
        cargo_type="General",
        etd=datetime.date(2026, 3, 1),
        eta=datetime.date(2026, 3, 26),
        status="BOOKED"
    )
    db.add(test_shipment)
    db.commit()

    calculated_delay = route_avg_delay_days_as_of(db, test_shipment)
    
    # h1 (2.0 days) must be included, h2 (10.0 days) must be excluded!
    assert calculated_delay == 2.0


def test_carrier_on_time_pct_zero_leakage(db):
    """
    Verifies that carrier reliability only considers completed past shipments
    whose actual arrivals were recorded prior to the target shipment's ETD.
    """
    carrier = db.query(Carrier).first()
    route = db.query(Route).first()

    # Past on-time delivery
    s_past_on_time = Shipment(
        shipment_ref="SHP-PAST-ONTIME",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="AIR",
        cargo_type="General",
        etd=datetime.date(2026, 1, 1),
        eta=datetime.date(2026, 1, 4),
        actual_arrival=datetime.date(2026, 1, 4),
        status="DELIVERED"
    )
    # Past late delivery
    s_past_late = Shipment(
        shipment_ref="SHP-PAST-LATE",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="AIR",
        cargo_type="General",
        etd=datetime.date(2026, 1, 5),
        eta=datetime.date(2026, 1, 8),
        actual_arrival=datetime.date(2026, 1, 12),
        status="DELIVERED"
    )
    # Future delivery (arrived in November 2026)
    s_future = Shipment(
        shipment_ref="SHP-FUTURE-LATE",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="AIR",
        cargo_type="General",
        etd=datetime.date(2026, 11, 1),
        eta=datetime.date(2026, 11, 4),
        actual_arrival=datetime.date(2026, 11, 10),
        status="DELIVERED"
    )
    db.add_all([s_past_on_time, s_past_late, s_future])
    db.commit()

    # Target shipment in May 2026
    target_shipment = Shipment(
        shipment_ref="SHP-TARGET-MAY",
        carrier_id=carrier.carrier_id,
        route_id=route.route_id,
        mode="AIR",
        cargo_type="General",
        etd=datetime.date(2026, 5, 1),
        eta=datetime.date(2026, 5, 4),
        status="BOOKED"
    )
    db.add(target_shipment)
    db.commit()

    pct = carrier_on_time_pct_as_of(db, target_shipment)

    # 1 on-time out of 2 past shipments = 50.0% (future shipment excluded)
    assert pct == 50.0
