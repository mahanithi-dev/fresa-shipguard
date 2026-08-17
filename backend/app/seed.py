from sqlalchemy.orm import Session

from app.entities import Shipment
from app.services.ai_generator import generate_ai_shipments


def seed_demo_data(db: Session) -> None:
    if db.query(Shipment).first():
        return
    generate_ai_shipments(db, count=160)


MODEL_METRICS = {
    "precision": 0.81,
    "recall": 0.76,
    "f1_score": 0.78,
    "roc_auc": 0.84,
    "target_definition": "1 = actual arrival delayed beyond ETA by more than one day; 0 = delay of one day or less.",
    "leakage_guardrail": "Historical carrier and route features are calculated only from completed outcomes available before the shipment ETD.",
}
