"""Idempotently seed the offline demo dataset and calculate the daily APIx."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import func, select

from app.database import Base, SessionLocal, engine
from app.config import settings
from app.models import Airline, FareQuote, IndexValue, Route, Source
from app.services.cleaning import clean_quotes
from app.services.demo import AIRLINES, ROUTES, generate_quotes
from app.services.index import calculate_index


ROUTE_WEIGHTS = {route: Decimal("1.0") for route in ROUTES}


def seed() -> None:
    if not settings.demo_mode:
        print("DEMO_MODE is false; no synthetic data was generated.")
        return
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.name == "Demo Replay Source"))
        if source and db.scalar(select(func.count(FareQuote.id)).where(FareQuote.source_id == source.id)):
            print("Demo data already exists; nothing to do.")
            return
        source = source or Source(name="Demo Replay Source", type="demo", enabled=True, is_demo=True)
        db.add(source)
        for route_code in ROUTES:
            origin, destination = route_code.split("-")
            db.merge(Route(origin=origin, destination=destination, route_code=route_code, weight=ROUTE_WEIGHTS[route_code]))
        for name, code in AIRLINES:
            db.merge(Airline(name=name, code=code, active=True))
        db.commit()
        db.refresh(source)
        routes = {route.route_code: route for route in db.scalars(select(Route))}
        airlines = {airline.code: airline for airline in db.scalars(select(Airline))}
        raw = generate_quotes(date.today() - timedelta(days=30), days=30)
        clean, stats = clean_quotes(raw)
        for quote in clean:
            db.add(FareQuote(
                source_id=source.id,
                route_id=routes[quote.route_code].id,
                airline_id=airlines[quote.airline_code].id,
                collected_at=quote.collected_at,
                travel_date=quote.travel_date,
                advance_days=quote.advance_days,
                flight_number=quote.flight_number,
                fare_class=quote.fare_class,
                base_fare=quote.base_fare,
                taxes=quote.taxes,
                airport_fee=quote.airport_fee,
                convenience_fee=quote.convenience_fee,
                other_fees=quote.other_fees,
                total_fare=quote.total_fare,
                currency="INR",
                available=quote.available,
                raw_reference="demo://replay/2026-seed",
                data_quality_score=Decimal("100.00"),
            ))
        db.commit()
        results = calculate_index(clean, {key: float(value) for key, value in ROUTE_WEIGHTS.items()})
        for position, result in enumerate(results):
            db.add(IndexValue(
                date=result["date"], frequency="daily", index_value=result["index_value"],
                base_period="first 7 days of demo data", sample_count=result["sample_count"],
                percentage_change_daily=None if position == 0 else round((result["index_value"] / results[position - 1]["index_value"] - 1) * 100, 4),
            ))
        db.commit()
        print(f"Seeded {stats.valid} fare observations ({stats.outliers} outliers excluded) across {len(ROUTES)} routes and {len(AIRLINES)} airlines.")


if __name__ == "__main__":
    seed()
