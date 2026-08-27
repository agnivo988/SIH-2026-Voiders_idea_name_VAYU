from collections import defaultdict
from statistics import median
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, Route

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/lead-time")
def lead_time(route: str | None = None, db: Session = Depends(get_db)) -> dict[str, float | None]:
    query = select(FareQuote).join(Route).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))
    if route:
        query = query.where(Route.route_code == route.upper())
    values: dict[int, list[float]] = defaultdict(list)
    for quote in db.scalars(query):
        values[quote.advance_days].append(float(quote.total_fare))
    return {f"T+{days}": round(sum(fares) / len(fares), 2) if fares else None for days, fares in [(1, values[1]), (7, values[7]), (15, values[15]), (30, values[30]), (45, values[45])]}


@router.get("/airlines")
def airline_comparison(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for quote in db.scalars(select(FareQuote).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))):
        grouped[quote.airline.name].append(float(quote.total_fare))
    return [{"airline": name, "median_fare": round(median(fares), 2), "average_fare": round(sum(fares) / len(fares), 2), "observations": len(fares)} for name, fares in sorted(grouped.items())]


@router.get("/volatility")
def volatility(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for quote in db.scalars(select(FareQuote).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))):
        grouped[quote.route.route_code].append(float(quote.total_fare))
    result = []
    for route, fares in grouped.items():
        average = sum(fares) / len(fares)
        deviation = (sum((fare - average) ** 2 for fare in fares) / len(fares)) ** 0.5
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
