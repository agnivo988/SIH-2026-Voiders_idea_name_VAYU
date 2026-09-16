from collections import defaultdict
from statistics import median
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Airline, FareQuote, Route

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/lead-time")
def lead_time(route: str | None = None, db: Session = Depends(get_db)) -> dict[str, float | None]:
    query = select(FareQuote.advance_days, func.avg(FareQuote.total_fare)).join(Route).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))
    if route:
        query = query.where(Route.route_code == route.upper())
    query = query.where(FareQuote.advance_days.in_([1, 7, 15, 30, 45])).group_by(FareQuote.advance_days)
    values = {days: average for days, average in db.execute(query).all()}
    return {f"T+{days}": round(float(values[days]), 2) if values.get(days) is not None else None for days in [1, 7, 15, 30, 45]}


@router.get("/airlines")
def airline_comparison(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = (
        select(
            FareQuote.airline_id,
            func.avg(FareQuote.total_fare),
            func.percentile_cont(0.5).within_group(FareQuote.total_fare),
            func.count(FareQuote.id),
        )
        .join(FareQuote.airline)
        .where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))
        .group_by(FareQuote.airline_id)
    )
    names = dict(db.execute(select(Airline.id, Airline.name)).all())
    return [
        {
            "airline": names[airline_id],
            "median_fare": round(float(median_value), 2),
            "average_fare": round(float(average_value), 2),
            "observations": observations,
        }
        for airline_id, average_value, median_value, observations in sorted(db.execute(query).all(), key=lambda item: names[item[0]])
    ]


@router.get("/volatility")
def volatility(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    query = (
        select(Route.route_code, func.avg(FareQuote.total_fare), func.avg(FareQuote.total_fare * FareQuote.total_fare))
        .join(FareQuote, FareQuote.route_id == Route.id)
        .where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))
        .group_by(Route.route_code)
    )
    result = []
    for route, average_value, squared_average_value in db.execute(query):
        average = float(average_value)
        variance = max(float(squared_average_value) - average**2, 0)
        deviation = variance**0.5
        result.append({"route": route, "standard_deviation": round(deviation, 2), "coefficient_of_variation": round(deviation / average * 100, 2)})
    return sorted(result, key=lambda item: item["coefficient_of_variation"], reverse=True)


@router.get("/price-surge")
def price_surge(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    grouped: dict[str, dict[object, list[float]]] = defaultdict(lambda: defaultdict(list))
    for quote in db.scalars(select(FareQuote).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))):
        grouped[quote.route.route_code][quote.travel_date].append(float(quote.total_fare))
    result = []
    for route, days in grouped.items():
        ordered = sorted((day, median(values)) for day, values in days.items())
        if len(ordered) >= 2:
            change = (ordered[-1][1] / ordered[-2][1] - 1) * 100
            result.append({"route": route, "percentage_change": round(change, 2), "flagged": change >= 5})
    return sorted(result, key=lambda item: item["percentage_change"], reverse=True)
