from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.entities import Carrier, Route
from app.models.schemas import CarrierOut, RouteOut


router = APIRouter(tags=["reference"], dependencies=[Depends(get_current_user)])


@router.get("/carriers", response_model=list[CarrierOut])
def list_carriers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Carrier).order_by(Carrier.carrier_name)
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size).all()


@router.get("/routes", response_model=list[RouteOut])
def list_routes(
    mode: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Route)
    if mode:
        query = query.filter(Route.mode == mode.strip().upper())
    offset = (page - 1) * page_size
    return query.order_by(Route.origin_port, Route.dest_port).offset(offset).limit(page_size).all()

