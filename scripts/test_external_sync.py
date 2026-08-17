import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from app.db import Base, engine, SessionLocal
from app.entities import ExternalCurrency, ExternalHoliday, ExternalPortStatus, ExternalWeather, Shipment
from app.services.external_data import sync_all_external_data
from app.services.scoring_service import score_active_shipments


def main():
    print("=== Testing Real-World External Data Integration ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Step 1: Sync external data from live public APIs
        print("\n1. Syncing live API data...")
        result = sync_all_external_data(db, force=True)
        print("Sync result:", result)

        # Step 2: Query DB cache
        w_count = db.query(ExternalWeather).count()
        c_count = db.query(ExternalCurrency).count()
        h_count = db.query(ExternalHoliday).count()
        p_count = db.query(ExternalPortStatus).count()

        print(f"\n2. DB Cached Records:")
        print(f" - Weather Ports: {w_count}")
        print(f" - Currency Pairs: {c_count}")
        print(f" - Public Holidays: {h_count}")
        print(f" - Port Statuses: {p_count}")

        # Print samples
        sample_w = db.query(ExternalWeather).filter_by(port_name="Rotterdam").first()
        if sample_w:
            print(f"   [Sample Weather] Rotterdam: {sample_w.weather_condition}, {sample_w.temperature_c}°C, {sample_w.wind_speed_kmh} km/h wind (Source: {sample_w.data_source})")

        sample_c = db.query(ExternalCurrency).filter_by(base_currency="USD", target_currency="INR").first()
        if sample_c:
            print(f"   [Sample FX] USD/INR: {sample_c.rate} (Source: {sample_c.data_source})")

        sample_h = db.query(ExternalHoliday).first()
        if sample_h:
            print(f"   [Sample Holiday] {sample_h.country_code}: {sample_h.holiday_name} on {sample_h.holiday_date} (Source: {sample_h.data_source})")

        # Step 3: Rescore shipments with external factors
        print("\n3. Rescoring active shipments with external risk factors...")
        scored = score_active_shipments(db)
        print(f"Successfully scored {scored} shipments with real-world factors!")

        # Print top risk shipment breakdown
        sample_shipment = db.query(Shipment).first()
        if sample_shipment and sample_shipment.risk_score:
            print(f"\n[Shipment {sample_shipment.shipment_ref}] Risk Score: {sample_shipment.risk_score.risk_score*100:.1f}% ({sample_shipment.risk_score.risk_tier})")
            print("Factors Breakdown:")
            import json
            for f in json.loads(sample_shipment.risk_score.top_factors):
                print(f" - {f['factor']}: {f['value']} (Source: {f.get('source', 'System')})")

    finally:
        db.close()

if __name__ == '__main__':
    main()
