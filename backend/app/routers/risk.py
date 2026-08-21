from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from joblib import load
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.entities import RiskScore, Shipment
from app.models.schemas import ModelMetrics, RiskScoreOut, RiskSummary, ScoreBatchResult
from app.seed import MODEL_METRICS
from app.services.scoring_service import risk_to_dict, score_active_shipments, score_shipment


from sqlalchemy import func


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
    tier_counts = dict(
        db.query(RiskScore.risk_tier, func.count(RiskScore.shipment_id))
        .group_by(RiskScore.risk_tier)
        .all()
    )
    high = tier_counts.get("HIGH", 0)
    medium = tier_counts.get("MEDIUM", 0)
    low = tier_counts.get("LOW", 0)
    total = sum(tier_counts.values())
    return RiskSummary(
        high=high,
        medium=medium,
        low=low,
        total=total,
    )


@router.get("/metrics", response_model=ModelMetrics)
def model_metrics():
    settings = get_settings()
    model_path = Path(settings.model_path)
    if not model_path.is_absolute():
        # resolve relative to backend package directory
        model_path = Path(__file__).resolve().parents[1] / "ml" / "model.joblib"

    if model_path.exists():
        try:
            artifact = load(model_path)
            if isinstance(artifact, dict) and "metrics" in artifact:
                m = artifact["metrics"]
                return ModelMetrics(
                    precision=float(m.get("precision", MODEL_METRICS["precision"])),
                    recall=float(m.get("recall", MODEL_METRICS["recall"])),
                    f1_score=float(m.get("f1_score", MODEL_METRICS["f1_score"])),
                    roc_auc=float(m.get("roc_auc") if m.get("roc_auc") is not None else MODEL_METRICS["roc_auc"]),
                    target_definition=MODEL_METRICS["target_definition"],
                    leakage_guardrail=MODEL_METRICS["leakage_guardrail"],
                )
        except Exception:
            pass
    return MODEL_METRICS
