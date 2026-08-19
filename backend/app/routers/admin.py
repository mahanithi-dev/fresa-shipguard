from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin
from app.entities import RiskScore, Shipment, ShipmentHistory, User
from app.services.ai_generator import generate_ai_shipments
from app.services.security import log_security_event

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/generate-ai-data")
def generate_data(
    request: Request,
    count: int = Query(150, ge=1, le=1000),
    replace_existing: bool = True,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    log_security_event(
        "ADMIN_GENERATE_DATA_TRIGGERED",
        f"Admin initiated AI shipment generation: count={count}, replace_existing={replace_existing}",
        client_ip=client_ip,
        user_identifier=current_user.email,
    )

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

