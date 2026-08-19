import csv
import io
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.deps import get_current_user
from app.entities import RiskScore, Shipment
from app.models.schemas import ImportResult, PaginatedShipments, ShipmentCreate, ShipmentDetail, ShipmentSummary, ShipmentUpdate
from app.services.scoring_service import risk_to_dict, score_shipment

logger = logging.getLogger("shipguard.shipments")

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_CSV_IMPORT_ROWS = 1000

router = APIRouter(prefix="/shipments", tags=["shipments"], dependencies=[Depends(get_current_user)])


def _summary(shipment: Shipment) -> ShipmentSummary:
    return ShipmentSummary(
        shipment_id=shipment.shipment_id,
        shipment_ref=shipment.shipment_ref,
        carrier_name=shipment.carrier.carrier_name if shipment.carrier else "Unknown Carrier",
        route=f"{shipment.route.origin_port} -> {shipment.route.dest_port}" if shipment.route else "Unknown Route",
        mode=shipment.mode,
        eta=shipment.eta,
        status=shipment.status,
        risk_tier=shipment.risk_score.risk_tier if shipment.risk_score else None,
        risk_score=shipment.risk_score.risk_score if shipment.risk_score else None,
        container_no=getattr(shipment, "container_no", None),
        vessel_name=getattr(shipment, "vessel_name", None),
        disruption_event=getattr(shipment, "disruption_event", None),
        consignee=getattr(shipment, "consignee", None),
    )


@router.get("", response_model=PaginatedShipments)
def list_shipments(
    status: str | None = None,
    risk_tier: str | None = None,
    mode: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Shipment).options(
        joinedload(Shipment.carrier),
        joinedload(Shipment.route),
        joinedload(Shipment.risk_score)
    )
    if status:
        query = query.filter(Shipment.status == status.strip().upper())
    if mode:
        query = query.filter(Shipment.mode == mode.strip().upper())
    if risk_tier:
        query = query.join(RiskScore, isouter=True).filter(RiskScore.risk_tier == risk_tier.strip().upper())

    total = query.count()
    offset = (page - 1) * page_size
    shipments = query.order_by(Shipment.created_at.desc()).offset(offset).limit(page_size).all()

    items = [_summary(shipment) for shipment in shipments]
    return PaginatedShipments(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ShipmentSummary)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    # Check for duplicate shipment_ref
    existing = db.query(Shipment).filter(Shipment.shipment_ref == payload.shipment_ref).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Shipment reference '{payload.shipment_ref}' already exists."
        )

    shipment = Shipment(**payload.model_dump())
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    score_shipment(db, shipment)
    return _summary(shipment)


@router.get("/{shipment_id}", response_model=ShipmentDetail)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = (
        db.query(Shipment)
        .options(
            joinedload(Shipment.carrier),
            joinedload(Shipment.route),
            joinedload(Shipment.risk_score),
            joinedload(Shipment.history)
        )
        .filter(Shipment.shipment_id == shipment_id)
        .first()
    )
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    summary = _summary(shipment).model_dump()
    return ShipmentDetail(
        **summary,
        carrier_id=shipment.carrier_id,
        route_id=shipment.route_id,
        cargo_type=shipment.cargo_type,
        etd=shipment.etd,
        actual_arrival=shipment.actual_arrival,
        risk=risk_to_dict(shipment.risk_score) if shipment.risk_score else None,
        history=sorted(shipment.history, key=lambda item: item.event_ts),
    )


@router.patch("/{shipment_id}", response_model=ShipmentSummary)
def update_shipment(shipment_id: int, payload: ShipmentUpdate, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(shipment, key, value)
    if shipment.eta < shipment.etd:
        raise HTTPException(status_code=422, detail="eta must be greater than or equal to etd")
    db.commit()
    db.refresh(shipment)
    score_shipment(db, shipment)
    return _summary(shipment)


@router.post("/import", response_model=ImportResult)
async def import_shipments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. Validate file format / extension
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only CSV files (.csv) are accepted for shipment import."
        )

    # 2. Enforce file size limit
    raw_content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(raw_content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum allowed size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    try:
        decoded_content = raw_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            decoded_content = raw_content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode file encoding. Please provide a valid UTF-8 CSV.")

    reader = csv.DictReader(io.StringIO(decoded_content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing header row.")

    imported = 0
    errors = []

    for index, row in enumerate(reader, start=2):
        if index > MAX_CSV_IMPORT_ROWS + 2:
            errors.append(f"Reached maximum limit of {MAX_CSV_IMPORT_ROWS} rows per import.")
            break

        try:
            # Clean string values in row
            cleaned_row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k}
            payload = ShipmentCreate(**cleaned_row)
            shipment = Shipment(**payload.model_dump())
            db.add(shipment)
            db.flush()
            score_shipment(db, shipment)
            db.commit()
            imported += 1
        except Exception as exc:
            db.rollback()
            # Sanitize error detail to prevent database schema/driver leakage
            logger.info("CSV import row %d validation error: %s", index, exc)
            errors.append(f"Line {index}: Invalid shipment data format or missing required fields.")

    return ImportResult(imported=imported, errors=errors)


