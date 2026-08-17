from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.entities import Shipment, ShipmentHistory, RiskScore
from app.services.ai_generator import generate_ai_shipments

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_user)])


@router.post("/generate-ai-data")
def generate_data(count: int = 150, replace_existing: bool = True, db: Session = Depends(get_db)):
    if replace_existing:
        db.query(RiskScore).delete()
        db.query(ShipmentHistory).delete()
        db.query(Shipment).delete()
        db.commit()

    created = generate_ai_shipments(db, count=count)
    return {
        "status": "success",
        "message": f"Successfully generated {created} realistic AI shipment records.",
        "count": created
    }
