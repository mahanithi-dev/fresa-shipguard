from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.entities import RiskScore, Shipment
from app.models.schemas import ModelMetrics, RiskScoreOut, RiskSummary, ScoreBatchResult
from app.seed import MODEL_METRICS
from app.services.scoring_service import risk_to_dict, score_active_shipments, score_shipment


router = APIRouter(prefix="/risk", tags=["risk"], dependencies=[Depends(get_current_user)])


@router.post("/score/{shipment_id}", response_model=RiskScoreOut)
def score_one(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return risk_to_dict(score_shipment(db, shipment))


@router.post("/score-batch", response_model=ScoreBatchResult)
def score_batch(db: Session = Depends(get_db)):
    return ScoreBatchResult(scored=score_active_shipments(db))


@router.get("/summary", response_model=RiskSummary)
def risk_summary(db: Session = Depends(get_db)):
    risks = db.query(RiskScore).all()
    return RiskSummary(
        high=sum(1 for risk in risks if risk.risk_tier == "HIGH"),
        medium=sum(1 for risk in risks if risk.risk_tier == "MEDIUM"),
        low=sum(1 for risk in risks if risk.risk_tier == "LOW"),
        total=len(risks),
    )


@router.get("/metrics", response_model=ModelMetrics)
def model_metrics():
    return MODEL_METRICS
