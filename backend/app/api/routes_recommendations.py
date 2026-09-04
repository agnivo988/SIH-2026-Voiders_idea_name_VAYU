from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FareQuote, Route

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("")
def recommend_flights(
    route: str = Query(..., min_length=7, max_length=7),
    travel_date: date | None = None,
    advance_days: int = Query(7, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = select(FareQuote).join(Route).where(
        Route.route_code == route.upper(),
        FareQuote.advance_days == advance_days,
        FareQuote.available.is_(True),
        FareQuote.is_outlier.is_(False),
    )
    if travel_date:
        query = query.where(FareQuote.travel_date == travel_date)
    rows = db.scalars(query.order_by(FareQuote.total_fare).limit(limit)).all()
    if not rows:
        raise HTTPException(404, "No available fare observations match these filters")
    return {
        "route": route.upper(),
        "travel_date": travel_date,
        "advance_days": advance_days,
        "recommendation": "Lowest observed total fare; verify availability with the provider before booking.",
        "items": [
            {
                "id": row.id,
                "airline": row.airline.name,
                "airline_code": row.airline.code,
                "flight_number": row.flight_number,
                "fare_class": row.fare_class,
                "base_fare": float(row.base_fare),
                "taxes": float(row.taxes),
                "fees": round(float(row.airport_fee + row.convenience_fee + row.other_fees), 2),
                "total_fare": float(row.total_fare),
                "currency": row.currency,
                "collected_at": row.collected_at,
                "available": row.available,
            }
            for row in rows
        ],
    }
