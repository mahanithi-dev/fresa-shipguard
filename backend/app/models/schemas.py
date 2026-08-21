from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=150)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="OPS_USER", max_length=20)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=10, description="Google ID Token from Google Identity Services")


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
    shipment_ref: str = Field(..., min_length=1, max_length=30)
    carrier_id: int = Field(..., ge=1)
    route_id: int = Field(..., ge=1)
    mode: str = Field(..., min_length=2, max_length=10)
    cargo_type: str = Field(..., min_length=1, max_length=50)
    etd: date
    eta: date
    actual_arrival: date | None = None
    status: str = Field(default="BOOKED", max_length=20)

    @model_validator(mode="after")
    def check_dates(self):
        if self.eta < self.etd:
            raise ValueError("eta must be greater than or equal to etd")
        return self


class ShipmentCreate(ShipmentBase):
    container_no: str | None = Field(default=None, max_length=50)
    vessel_name: str | None = Field(default=None, max_length=100)
    disruption_event: str | None = Field(default=None, max_length=255)
    consignee: str | None = Field(default=None, max_length=100)


class ShipmentUpdate(BaseModel):
    carrier_id: int | None = Field(default=None, ge=1)
    route_id: int | None = Field(default=None, ge=1)
    mode: str | None = Field(default=None, max_length=10)
    cargo_type: str | None = Field(default=None, max_length=50)
    etd: date | None = None
    eta: date | None = None
    actual_arrival: date | None = None
    status: str | None = Field(default=None, max_length=20)
    container_no: str | None = Field(default=None, max_length=50)
    vessel_name: str | None = Field(default=None, max_length=100)
    disruption_event: str | None = Field(default=None, max_length=255)
    consignee: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def check_dates(self):
        if self.eta is not None and self.etd is not None and self.eta < self.etd:
            raise ValueError("eta must be greater than or equal to etd")
        return self


class Factor(BaseModel):
    factor: str = Field(..., max_length=100)
    value: str | None = Field(default=None, max_length=255)
    impact: str = Field(..., max_length=50)
    source: str | None = Field(default=None, max_length=100)


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

