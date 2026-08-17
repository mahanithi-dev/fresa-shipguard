import math
import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.entities import Carrier, Route, Shipment, ShipmentHistory, User
from app.services.scoring_service import score_shipment
from app.services.security import hash_password

CARRIERS_DATA = [
    {"name": "Maersk Line", "code": "MSK", "on_time": 68.5, "prefix": "MSK"},
    {"name": "MSC Mediterranean Shipping", "code": "MSC", "on_time": 64.0, "prefix": "MED"},
    {"name": "CMA CGM Group", "code": "CMA", "on_time": 74.2, "prefix": "CMA"},
    {"name": "Hapag-Lloyd AG", "code": "HAP", "on_time": 78.0, "prefix": "HLX"},
    {"name": "Ocean Network Express (ONE)", "code": "ONE", "on_time": 71.5, "prefix": "ONE"},
    {"name": "DHL Global Forwarding", "code": "DHL", "on_time": 88.0, "prefix": "DHL"},
    {"name": "Cathay Cargo Air", "code": "CPA", "on_time": 91.2, "prefix": "CPA"},
    {"name": "Blue Dart Express", "code": "BDL", "on_time": 83.5, "prefix": "BDL"},
]

ROUTES_DATA = [
    {"origin": "Shanghai (CNSHA)", "dest": "Rotterdam (NLRTM)", "mode": "SEA", "transit": 28},
    {"origin": "Ningbo (CNNGB)", "dest": "Hamburg (DEHAM)", "mode": "SEA", "transit": 30},
    {"origin": "Chennai (INMAA)", "dest": "Jebel Ali (AEJEA)", "mode": "SEA", "transit": 9},
    {"origin": "Tuticorin (INTUT)", "dest": "Singapore (SGSIN)", "mode": "SEA", "transit": 7},
    {"origin": "Bengaluru (BLR)", "dest": "Frankfurt (FRA)", "mode": "AIR", "transit": 2},
    {"origin": "Mumbai (BOM)", "dest": "London Heathrow (LHR)", "mode": "AIR", "transit": 3},
    {"origin": "Tokyo (TYO)", "dest": "Los Angeles (LAX)", "mode": "SEA", "transit": 14},
    {"origin": "Shenzhen (CNSZX)", "dest": "Long Beach (LGB)", "mode": "SEA", "transit": 16},
    {"origin": "Chennai Port", "dest": "Delhi ICD Tughlakabad", "mode": "LAND", "transit": 4},
]

VESSELS_BY_CARRIER = {
    "MSK": ["Maersk Mc-Kinney Moller", "Maersk Madrid (Voy 2409W)", "Maersk Horizon (Voy 048E)"],
    "MSC": ["MSC GULSUN (Voy 2410E)", "MSC OSCAR (Voy 1902W)", "MSC ANNA (Voy 092S)"],
    "CMA": ["CMA CGM Antoine de St Exupery", "CMA CGM Palais Royal", "CMA CGM Jacques Saade"],
    "HAP": ["Hapag-Lloyd Berlin Express", "Hapag-Lloyd Hamburg Express", "Hapag-Lloyd Paris Express"],
    "ONE": ["ONE Apus (Voy 041E)", "ONE Innovation (Voy 012W)", "ONE Stork (Voy 098S)"],
    "DHL": ["Boeing 777F #DH-8402", "Airbus A330-300F #DH-2041"],
    "CPA": ["Boeing 747-8F #CX-8890", "Boeing 777F #CX-1042"],
    "BDL": ["Volvo FM440 Heavy Hauler #BD-409", "Tata Prima 4928 Truck #BD-102"],
}

DISRUPTION_EVENTS = [
    "Typhoon Gaemi rerouting via Lombok Strait (+3 days)",
    "Port of Rotterdam Terminal 4 Crane Maintenance Congestion",
    "Red Sea Transit Diversion via Cape of Good Hope (+9 days)",
    "Customs Inspection Clearance Audit Hold at Destination",
    "Reefer Container Cold-Chain Temperature Variance Alert",
    "Suez Canal Southbound Convoy Delay",
    "Singapore Port Transshipment Berth Waiting (+2 days)",
    "Pre-Arrival Manifest Documentation Mismatch Hold",
    "Extreme Fog Operation Slowdown at Ningbo Terminal",
    None,  # Normal flight/voyage
    None,
    None,
]

CONSIGNEES = [
    "Siemens Energy Logistics Desk",
    "Bayer AG Healthcare Distribution",
    "Schneider Electric Supply Chain",
    "Bosch Automotive US LLC",
    "Apple Supply Chain Services",
    "Marks & Spencer International",
    "Samsung Electronics Logistics",
    "Novartis Global Pharma Operations",
    "Toyota Motor Parts Supply Desk",
]

CARGO_TYPES = ["General", "Reefer", "Hazardous", "Pharma", "Textiles", "Electronics"]


def generate_container_no(owner_prefix: str = "MSK") -> str:
    """Generates an ISO 6346 compliant shipping container number with a valid check digit."""
    equipment_identifier = "U"  # Standard freight container
    raw_prefix = (owner_prefix[:3].upper() + equipment_identifier).ljust(4, "U")
    serial = f"{random.randint(0, 999999):06d}"

    # ISO 6346 character weighting table
    char_map = {
        'A': 10, 'B': 12, 'C': 13, 'D': 14, 'E': 15, 'F': 16, 'G': 17, 'H': 18, 'I': 19,
        'J': 20, 'K': 21, 'L': 22, 'M': 23, 'N': 24, 'O': 25, 'P': 26, 'Q': 27, 'R': 28,
        'S': 29, 'T': 30, 'U': 31, 'V': 32, 'W': 33, 'X': 34, 'Y': 35, 'Z': 36
    }

    code_str = raw_prefix + serial
    total = 0
    for idx, char in enumerate(code_str):
        val = char_map[char] if char in char_map else int(char)
        total += val * (2 ** idx)

    check_digit = (total % 11) % 10
    return f"{raw_prefix}{serial}{check_digit}"


def calculate_domain_delay(mode: str, cargo_type: str, month: int, on_time_hist: float) -> int:
    """Calculates realistic logistics delay days using Log-Normal distribution and domain risk multipliers."""
    # Base risk factor derived from carrier historical reliability
    risk_factor = max(0.5, (100.0 - on_time_hist) / 30.0)

    # Cargo sensitivity multiplier
    if cargo_type in ["Reefer", "Pharma"]:
        risk_factor *= 1.35
    elif cargo_type == "Hazardous":
        risk_factor *= 1.25

    # Seasonal weather & congestion risk multiplier (Typhoon/Monsoon season)
    if mode == "SEA" and month in [7, 8, 9, 10]:
        risk_factor *= 1.4

    # Log-Normal tail distribution: mostly 0 delays, small probability of multi-day delays
    delay_raw = random.lognormvariate(0.1, 0.75) * risk_factor
    delay_days = math.floor(delay_raw) if delay_raw > 1.3 else 0
    return min(delay_days, 14)


def generate_ai_shipments(db: Session, count: int = 160) -> int:
    """Generates dynamic AI-synthesized shipment records with realistic freight details."""
    # Step 1: Ensure Admin & Ops users exist
    admin_user = db.query(User).filter_by(email="fresa_admin").first()
    if not admin_user:
        admin_user = User(name="Fresa Admin", email="fresa_admin", password_hash=hash_password("123"), role="ADMIN")
        db.add(admin_user)
    else:
        admin_user.password_hash = hash_password("123")
        admin_user.role = "ADMIN"
    
    user = db.query(User).filter_by(email="ops@shipguard.local").first()
    if not user:
        user = User(name="Ops User", email="ops@shipguard.local", password_hash=hash_password("shipguard123"))
        db.add(user)
    db.commit()

    # Step 2: Ensure Carriers exist
    carrier_map = {}
    for cdata in CARRIERS_DATA:
        c = db.query(Carrier).filter_by(carrier_code=cdata["code"]).first()
        if not c:
            c = Carrier(carrier_name=cdata["name"], carrier_code=cdata["code"], on_time_pct_hist=cdata["on_time"])
            db.add(c)
            db.commit()
            db.refresh(c)
        carrier_map[cdata["code"]] = c

    # Step 3: Ensure Routes exist
    route_list = []
    for rdata in ROUTES_DATA:
        r = db.query(Route).filter_by(origin_port=rdata["origin"], dest_port=rdata["dest"], mode=rdata["mode"]).first()
        if not r:
            r = Route(origin_port=rdata["origin"], dest_port=rdata["dest"], mode=rdata["mode"], avg_transit_days=rdata["transit"])
            db.add(r)
            db.commit()
            db.refresh(r)
        route_list.append(r)

    random.seed(date.today().timetuple().tm_yday + 100)
    today = date.today()
    created_count = 0

    # Generate shipments
    for i in range(1, count + 1):
        code = random.choice(list(carrier_map.keys()))
        carrier = carrier_map[code]
        route = random.choice(route_list)
        cargo = random.choice(CARGO_TYPES)
        consignee = random.choice(CONSIGNEES)
        vessels = VESSELS_BY_CARRIER.get(code, ["Generic Express Vessel"])
        vessel = random.choice(vessels)
        c_prefix = next((cd["prefix"] for cd in CARRIERS_DATA if cd["code"] == code), "MSK")
        container_no = generate_container_no(c_prefix)

        is_completed = i <= (count * 0.8)
        if is_completed:
            etd = today - timedelta(days=random.randint(20, 360))
            delay_days = calculate_domain_delay(route.mode, cargo, etd.month, carrier.on_time_pct_hist)
            planned = max(1, int(route.avg_transit_days))
            eta = etd + timedelta(days=planned)
            disruption = random.choice([d for d in DISRUPTION_EVENTS if d]) if delay_days > 2 else None
            actual = eta + timedelta(days=delay_days)
            status = "DELAYED" if delay_days > 1 else "DELIVERED"
            ref = f"SHP-2026-H{i:04d}"
        else:
            etd = today + timedelta(days=random.randint(-4, 10))
            planned = max(1, int(route.avg_transit_days))
            eta = etd + timedelta(days=planned)
            actual = None
            disruption = random.choice(DISRUPTION_EVENTS)
            status = random.choice(["BOOKED", "IN_TRANSIT", "IN_TRANSIT", "EXCEPTIONAL_HOLD"])
            ref = f"SHP-2026-A{(i - int(count * 0.8)):04d}"

        # Check if shipment ref exists
        existing = db.query(Shipment).filter_by(shipment_ref=ref).first()
        if existing:
            continue

        shipment = Shipment(
            shipment_ref=ref,
            carrier_id=carrier.carrier_id,
            route_id=route.route_id,
            mode=route.mode,
            cargo_type=cargo,
            etd=etd,
            eta=eta,
            actual_arrival=actual,
            status=status,
            container_no=container_no,
            vessel_name=vessel,
            disruption_event=disruption,
            consignee=consignee,
        )
        db.add(shipment)
        db.flush()

        # Add milestone history
        db.add(ShipmentHistory(
            shipment_id=shipment.shipment_id,
            event_type="BOOKING_CONFIRMED",
            event_ts=datetime.combine(etd - timedelta(days=3), datetime.min.time()),
            delay_days=0
        ))
        db.add(ShipmentHistory(
            shipment_id=shipment.shipment_id,
            event_type="DEPARTED_ORIGIN",
            event_ts=datetime.combine(etd, datetime.min.time()),
            delay_days=0
        ))
        if disruption:
            db.add(ShipmentHistory(
                shipment_id=shipment.shipment_id,
                event_type="DISRUPTION_ALERT",
                event_ts=datetime.combine(etd + timedelta(days=max(1, int(route.avg_transit_days // 2))), datetime.min.time()),
                delay_days=2.5
            ))
        if actual:
            db.add(ShipmentHistory(
                shipment_id=shipment.shipment_id,
                event_type="PORT_ARRIVED",
                event_ts=datetime.combine(actual, datetime.min.time()),
                delay_days=max(0, (actual - eta).days)
            ))

        # Calculate ML Risk Score
        score_shipment(db, shipment)
        created_count += 1

    db.commit()
    return created_count

