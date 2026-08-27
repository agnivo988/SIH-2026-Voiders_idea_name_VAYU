"""Recalculate route and composite APIx values from stored database fares."""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models import FareQuote, IndexValue, Route, RouteIndexValue


def recalculate() -> int:
    with SessionLocal() as db:
        quotes = db.scalars(select(FareQuote).where(FareQuote.available.is_(True), FareQuote.is_outlier.is_(False))).all()
        grouped: dict[tuple[date, int], list[float]] = defaultdict(list)
        for quote in quotes:
            grouped[(quote.travel_date, quote.route_id)].append(float(quote.total_fare))
        route_rows: list[tuple[date, int, float, int]] = []
        for (day, route_id), fares in grouped.items():
            route_rows.append((day, route_id, median(fares), len(fares)))
        if not route_rows:
            print("No usable fare observations found; index was not recalculated.")
            return 0
        base_dates = sorted({row[0] for row in route_rows})[:7]
        base_by_route: dict[int, list[float]] = defaultdict(list)
        for day, route_id, fare, _ in route_rows:
            if day in base_dates:
                base_by_route[route_id].append(fare)
        base_fares = {route_id: median(fares) for route_id, fares in base_by_route.items()}
        routes = {route.id: route for route in db.scalars(select(Route).where(Route.active.is_(True)))}
        total_weight = sum(float(route.weight) for route in routes.values()) or 1
        weights = {route_id: float(route.weight) / total_weight for route_id, route in routes.items()}
        by_day: dict[date, list[tuple[int, float, int]]] = defaultdict(list)
        for day, route_id, fare, count in route_rows:
            if route_id in base_fares:
                route_index = fare / base_fares[route_id] * 100
                by_day[day].append((route_id, route_index, count))
        db.execute(delete(RouteIndexValue))
        db.execute(delete(IndexValue))
        daily_values: list[tuple[date, float, int]] = []
        for day in sorted(by_day):
            entries = by_day[day]
            composite = sum(weights.get(route_id, 0) * value for route_id, value, _ in entries)
            daily_values.append((day, composite, sum(count for _, _, count in entries)))
            for route_id, value, count in entries:
                db.add(RouteIndexValue(date=day, route_id=route_id, index_value=round(value, 4), representative_fare=round(grouped[(day, route_id)] and median(grouped[(day, route_id)]) or 0, 2), sample_count=count))
        for position, (day, value, count) in enumerate(daily_values):
            def change(days: int) -> Decimal | None:
                target = day - timedelta(days=days)
                prior = next((item[1] for item in daily_values if item[0] == target), None)
                return Decimal(str(round((value / prior - 1) * 100, 4))) if prior else None
            db.add(IndexValue(date=day, frequency="daily", index_value=round(value, 4), base_period="first 7 days of imported data", percentage_change_daily=change(1), percentage_change_weekly=change(7), percentage_change_monthly=change(30), sample_count=count))
        db.commit()
        print(f"Recalculated {len(daily_values)} composite daily values and {len(route_rows)} route-day values from {len(quotes)} fare observations.")
        return len(daily_values)


if __name__ == "__main__":
    recalculate()
