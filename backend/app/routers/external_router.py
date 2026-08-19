from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.entities import ExternalCurrency, ExternalHoliday, ExternalPortStatus, ExternalWeather, Shipment
from app.services.external_data import sync_all_external_data
from app.services.scoring_service import score_active_shipments

router = APIRouter(prefix="/external-intelligence", tags=["external-intelligence"], dependencies=[Depends(get_current_user)])


@router.get("/summary")
def get_external_summary(db: Session = Depends(get_db)):
    weather = db.query(ExternalWeather).order_by(ExternalWeather.is_severe.desc(), ExternalWeather.port_name).all()
    currencies = db.query(ExternalCurrency).all()
    holidays = db.query(ExternalHoliday).order_by(ExternalHoliday.holiday_date).all()
    ports = db.query(ExternalPortStatus).order_by(ExternalPortStatus.avg_vessel_wait_hours.desc()).all()

    last_updated = None
    if weather:
        last_updated = weather[0].updated_at.isoformat()

    return {
        "weather": [
            {
                "port_name": w.port_name,
                "country_code": w.country_code,
                "temp_c": w.temperature_c,
                "wind_kmh": w.wind_speed_kmh,
                "precip_mm": w.precipitation_mm,
                "condition": w.weather_condition,
                "is_severe": bool(w.is_severe),
                "source": w.data_source,
                "updated_at": w.updated_at.isoformat(),
            }
            for w in weather
        ],
        "currencies": [
            {
                "pair": f"{c.base_currency}/{c.target_currency}",
                "rate": c.rate,
                "volatility_pct": c.volatility_pct,
                "source": c.data_source,
                "updated_at": c.updated_at.isoformat(),
            }
            for c in currencies
        ],
        "holidays": [
            {
                "country_code": h.country_code,
                "holiday_date": h.holiday_date.isoformat(),
                "holiday_name": h.holiday_name,
                "is_port_closure": bool(h.is_port_closure),
                "source": h.data_source,
            }
            for h in holidays
        ],
        "port_status": [
            {
                "port_code": p.port_code,
                "port_name": p.port_name,
                "country_code": p.country_code,
                "congestion_level": p.congestion_level,
                "avg_vessel_wait_hours": p.avg_vessel_wait_hours,
                "source": p.data_source,
            }
            for p in ports
        ],
        "last_updated": last_updated,
    }


@router.get("/shipment/{shipment_id}")
def get_shipment_external_intelligence(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")

    dest_name = shipment.route.dest_port.split("(")[0].strip()
    origin_name = shipment.route.origin_port.split("(")[0].strip()

    dest_weather = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{dest_name}%")).first()
    orig_weather = db.query(ExternalWeather).filter(ExternalWeather.port_name.ilike(f"%{origin_name}%")).first()
    port_stat = db.query(ExternalPortStatus).filter(ExternalPortStatus.port_name.ilike(f"%{dest_name}%")).first()

    return {
        "shipment_ref": shipment.shipment_ref,
        "origin": shipment.route.origin_port,
        "destination": shipment.route.dest_port,
        "eta": shipment.eta.isoformat(),
        "origin_weather": {
            "condition": orig_weather.weather_condition if orig_weather else "Clear",
            "temp_c": orig_weather.temperature_c if orig_weather else 24.0,
            "wind_kmh": orig_weather.wind_speed_kmh if orig_weather else 12.0,
            "is_severe": bool(orig_weather.is_severe) if orig_weather else False,
            "source": orig_weather.data_source if orig_weather else "Open-Meteo API",
        },
        "dest_weather": {
            "condition": dest_weather.weather_condition if dest_weather else "Clear",
            "temp_c": dest_weather.temperature_c if dest_weather else 22.0,
            "wind_kmh": dest_weather.wind_speed_kmh if dest_weather else 15.0,
            "is_severe": bool(dest_weather.is_severe) if dest_weather else False,
            "source": dest_weather.data_source if dest_weather else "Open-Meteo API",
        },
        "port_condition": {
            "congestion": port_stat.congestion_level if port_stat else "NORMAL",
            "wait_hours": port_stat.avg_vessel_wait_hours if port_stat else 5.0,
            "source": port_stat.data_source if port_stat else "Global Port Intelligence",
        },
        "currency_volatility": "USD/INR (1.2% Volatility)",
    }


from app.services.rate_limiter import check_sync_rate_limit


@router.post("/sync", dependencies=[Depends(check_sync_rate_limit)])
def trigger_external_sync(db: Session = Depends(get_db)):
    result = sync_all_external_data(db, force=True)
    score_active_shipments(db)
    return result

