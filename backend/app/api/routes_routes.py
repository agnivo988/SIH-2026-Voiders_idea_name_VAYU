from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, Route

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("")
def list_routes(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [{"route_code": route.route_code, "origin": route.origin, "destination": route.destination, "weight": float(route.weight), "active": route.active} for route in db.scalars(select(Route).where(Route.active.is_(True)).order_by(Route.route_code))]


@router.get("/{route_code}")
def route_detail(route_code: str, db: Session = Depends(get_db)) -> dict[str, object]:
    route = db.scalar(select(Route).where(Route.route_code == route_code.upper()))
    if route is None:
        raise HTTPException(404, "Route not found")
    fares = db.scalars(select(FareQuote).where(FareQuote.route_id == route.id, FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))).all()
    ordered = sorted(float(fare.total_fare) for fare in fares)
    representative = ordered[len(ordered) // 2] if ordered else None
    average = sum(ordered) / len(ordered) if ordered else None
    deviation = (sum((value - average) ** 2 for value in ordered) / len(ordered)) ** 0.5 if ordered and average else None
    return {"route_code": route.route_code, "current_median_fare": representative, "average_fare": round(average, 2) if average else None, "volatility": round(deviation / average * 100, 2) if deviation and average else 0, "observations": len(ordered)}
