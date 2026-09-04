from collections import defaultdict
from datetime import date, timedelta
from statistics import median

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, IndexValue, Route, RouteIndexValue

router = APIRouter(prefix="/api/cpi", tags=["cpi"])


def calculate_cpi(db: Session) -> dict[str, object]:
    quotes = db.scalars(select(FareQuote).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))).all()
    if not quotes:
        raise HTTPException(404, "No usable fare observations found")
    grouped: dict[tuple[date, int], list[float]] = defaultdict(list)
    for quote in quotes:
        grouped[(quote.travel_date, quote.route_id)].append(float(quote.total_fare))
    route_days = [(day, route_id, median(fares), len(fares)) for (day, route_id), fares in grouped.items()]
    base_dates = sorted({day for day, _, _, _ in route_days})[:7]
    base_fares: dict[int, float] = {}
    for route_id in {route_id for _, route_id, _, _ in route_days}:
        values = [fare for day, current_route_id, fare, _ in route_days if current_route_id == route_id and day in base_dates]
        if values:
            base_fares[route_id] = median(values)
    routes = {route.id: route for route in db.scalars(select(Route).where(Route.active.is_(True)))}
    weight_total = sum(float(route.weight) for route in routes.values()) or 1
    weights = {route_id: float(route.weight) / weight_total for route_id, route in routes.items()}
    daily: dict[date, list[tuple[int, float, int]]] = defaultdict(list)
    for day, route_id, fare, count in route_days:
        if route_id in base_fares and route_id in weights:
            daily[day].append((route_id, fare / base_fares[route_id] * 100, count))
    if not daily:
        raise HTTPException(422, "Insufficient observations for CPI calculation")
    db.execute(delete(RouteIndexValue))
    db.execute(delete(IndexValue))
    calculated: list[tuple[date, float, int]] = []
    for day in sorted(daily):
        entries = daily[day]
        value = sum(weights[route_id] * relative for route_id, relative, _ in entries)
        sample_count = sum(count for _, _, count in entries)
        calculated.append((day, value, sample_count))
        for route_id, relative, count in entries:
            db.add(RouteIndexValue(date=day, route_id=route_id, index_value=relative, representative_fare=median(grouped[(day, route_id)]), sample_count=count))
    for position, (day, value, sample_count) in enumerate(calculated):
        def percentage_change(days: int) -> float | None:
            previous = next((item[1] for item in calculated if item[0] == day - timedelta(days=days)), None)
            return round((value / previous - 1) * 100, 4) if previous else None
        db.add(IndexValue(date=day, frequency="daily", index_value=value, base_period="first 7 days of stored fare data", percentage_change_daily=percentage_change(1), percentage_change_weekly=percentage_change(7), percentage_change_monthly=percentage_change(30), sample_count=sample_count))
    db.commit()
    current = calculated[-1]
    return {"date": current[0], "index_value": round(current[1], 4), "daily_change": round((current[1] / calculated[-2][1] - 1) * 100, 4) if len(calculated) > 1 else None, "weekly_change": percentage_change_from_series(calculated, 7), "monthly_change": percentage_change_from_series(calculated, 30), "sample_count": current[2], "base_period": "first 7 days of stored fare data", "route_count": len(daily[current[0]])}


def percentage_change_from_series(values: list[tuple[date, float, int]], days: int) -> float | None:
    current_day, current_value, _ = values[-1]
    previous = next((value for day, value, _ in values if day == current_day - timedelta(days=days)), None)
    return round((current_value / previous - 1) * 100, 4) if previous else None


@router.get("/current")
def current_cpi(db: Session = Depends(get_db)) -> dict[str, object]:
    value = db.scalar(select(IndexValue).where(IndexValue.frequency == "daily").order_by(IndexValue.date.desc()))
    if value is None:
        raise HTTPException(404, "CPI has not been calculated yet")
    return {"date": value.date, "cpi_value": float(value.index_value), "daily_change": float(value.percentage_change_daily or 0), "weekly_change": float(value.percentage_change_weekly or 0), "monthly_change": float(value.percentage_change_monthly or 0), "sample_count": value.sample_count, "base_period": value.base_period}


@router.post("/calculate")
def recalculate_cpi(db: Session = Depends(get_db)) -> dict[str, object]:
    return calculate_cpi(db)
