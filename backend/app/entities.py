from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Carrier(Base):
    __tablename__ = "carriers"

    carrier_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    carrier_name: Mapped[str] = mapped_column(String(100), nullable=False)
    carrier_code: Mapped[str | None] = mapped_column(String(10), unique=True)
    on_time_pct_hist: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="carrier")


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (UniqueConstraint("origin_port", "dest_port", "mode", name="uq_route"),)

    route_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    origin_port: Mapped[str] = mapped_column(String(80), nullable=False)
    dest_port: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    avg_transit_days: Mapped[float] = mapped_column(Float)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="route")


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint("eta >= etd", name="chk_eta_after_etd"),
    )

    shipment_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_ref: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    carrier_id: Mapped[int] = mapped_column(ForeignKey("carriers.carrier_id"))
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.route_id"))
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    cargo_type: Mapped[str] = mapped_column(String(50))
    etd: Mapped[date] = mapped_column(Date, nullable=False)
    eta: Mapped[date] = mapped_column(Date, nullable=False)
    actual_arrival: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="BOOKED")
    container_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vessel_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disruption_event: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consignee: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    carrier: Mapped[Carrier] = relationship(back_populates="shipments")
    route: Mapped[Route] = relationship(back_populates="shipments")
    history: Mapped[list["ShipmentHistory"]] = relationship(back_populates="shipment")
    risk_score: Mapped["RiskScore | None"] = relationship(back_populates="shipment", uselist=False)


class ShipmentHistory(Base):
    __tablename__ = "shipment_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.shipment_id"))
    event_type: Mapped[str] = mapped_column(String(30))
    event_ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delay_days: Mapped[float] = mapped_column(Float, default=0)

    shipment: Mapped[Shipment] = relationship(back_populates="history")


class RiskScore(Base):
    __tablename__ = "risk_scores"

    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.shipment_id"), primary_key=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(10), nullable=False)
    top_factors: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(300), nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    shipment: Mapped[Shipment] = relationship(back_populates="risk_score")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="OPS_USER")


class ExternalWeather(Base):
    __tablename__ = "external_weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    port_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)
    wind_speed_kmh: Mapped[float] = mapped_column(Float)
    precipitation_mm: Mapped[float] = mapped_column(Float)
    weather_condition: Mapped[str] = mapped_column(String(100))
    is_severe: Mapped[bool] = mapped_column(Integer, default=0)  # 0 or 1 for SQLite compatibility
    data_source: Mapped[str] = mapped_column(String(100), default="Open-Meteo API")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExternalCurrency(Base):
    __tablename__ = "external_currencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    base_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_pct: Mapped[float] = mapped_column(Float, default=0.0)
    data_source: Mapped[str] = mapped_column(String(100), default="Frankfurter FX API")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExternalHoliday(Base):
    __tablename__ = "external_holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country_code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False)
    holiday_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_port_closure: Mapped[bool] = mapped_column(Integer, default=0)
    data_source: Mapped[str] = mapped_column(String(100), default="Nager.Date API")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExternalPortStatus(Base):
    __tablename__ = "external_port_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    port_code: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    port_name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    congestion_level: Mapped[str] = mapped_column(String(20), default="LOW")  # LOW, MEDIUM, HIGH, SEVERE
    avg_vessel_wait_hours: Mapped[float] = mapped_column(Float, default=4.0)
    data_source: Mapped[str] = mapped_column(String(100), default="Global Port Intelligence")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

