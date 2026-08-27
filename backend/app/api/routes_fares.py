from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, Route

router = APIRouter(prefix="/api/fares", tags=["fares"])


@router.get("")
def list_fares(route: str | None = None, advance_days: int | None = Query(None, ge=1), date_from: date | None = None, date_to: date | None = None, page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)) -> dict[str, object]:
    query = select(FareQuote).join(Route)
    if route:
        query = query.where(Route.route_code == route.upper())
    if advance_days is not None:
        query = query.where(FareQuote.advance_days == advance_days)
    if date_from:
        query = query.where(FareQuote.travel_date >= date_from)
    if date_to:
        query = query.where(FareQuote.travel_date <= date_to)
    total = len(db.scalars(query).all())
    rows = db.scalars(query.order_by(FareQuote.travel_date).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": row.id, "route": row.route.route_code, "airline": row.airline.name, "travel_date": row.travel_date, "advance_days": row.advance_days, "total_fare": float(row.total_fare), "currency": row.currency, "available": row.available, "is_outlier": row.is_outlier} for row in rows], "page": page, "page_size": page_size, "total": total}
