from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CarrierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    carrier_id: int
    carrier_name: str
    carrier_code: str | None
    on_time_pct_hist: float


class RouteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    route_id: int
    origin_port: str
    dest_port: str
    mode: str
    avg_transit_days: float


class ShipmentBase(BaseModel):
    shipment_ref: str
    carrier_id: int
    route_id: int
    mode: str
    cargo_type: str
    etd: date
    eta: date
    actual_arrival: date | None = None
    status: str = "BOOKED"

    @model_validator(mode="after")
    def check_dates(self):
        if self.eta < self.etd:
            raise ValueError("eta must be greater than or equal to etd")
        return self


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    carrier_id: int | None = None
    route_id: int | None = None
    mode: str | None = None
    cargo_type: str | None = None
    etd: date | None = None
    eta: date | None = None
    actual_arrival: date | None = None
    status: str | None = None


class Factor(BaseModel):
    factor: str
    value: str | None = None
    impact: str


class RiskScoreOut(BaseModel):
    shipment_id: int
    risk_score: float = Field(ge=0, le=1)
    risk_tier: str
    top_factors: list[Factor]
    recommendation: str
    scored_at: datetime


class ShipmentSummary(BaseModel):
    shipment_id: int
    shipment_ref: str
    carrier_name: str
    route: str
    mode: str
    eta: date
    status: str
    risk_tier: str | None
    risk_score: float | None
    container_no: str | None = None
    vessel_name: str | None = None
    disruption_event: str | None = None
    consignee: str | None = None


class PaginatedShipments(BaseModel):
    items: list[ShipmentSummary]
    total: int
    page: int
    page_size: int


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    event_type: str
    event_ts: datetime
    delay_days: float


class ShipmentDetail(ShipmentSummary):
    carrier_id: int
    route_id: int
    cargo_type: str
    etd: date
    actual_arrival: date | None
    risk: RiskScoreOut | None
    history: list[HistoryOut]


class ImportResult(BaseModel):
    imported: int
    errors: list[str]


class ScoreBatchResult(BaseModel):
    scored: int


class RiskSummary(BaseModel):
    high: int
    medium: int
    low: int
    total: int


class ModelMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    target_definition: str
    leakage_guardrail: str
