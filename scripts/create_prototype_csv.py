"""Create a reproducible, clearly labelled prototype CSV for local/demo analysis."""
from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.demo import generate_quotes


OUTPUT = Path(__file__).resolve().parents[1] / "data" / "demo" / "prototype_fares.csv"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    quotes = generate_quotes(date.today() - timedelta(days=30), days=30, seed=2026)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "route_code", "airline_code", "travel_date", "advance_days", "flight_number",
            "fare_class", "base_fare", "taxes", "airport_fee", "convenience_fee", "other_fees",
            "total_fare", "currency", "available", "collected_at", "raw_reference",
        ])
        writer.writeheader()
        for number, quote in enumerate(quotes, start=1):
            airline_code = quote.airline_code
            writer.writerow({
                "route_code": quote.route_code,
                "airline_code": airline_code,
                "travel_date": quote.travel_date.isoformat(),
                "advance_days": quote.advance_days,
                "flight_number": quote.flight_number,
                "fare_class": quote.fare_class,
                "base_fare": quote.base_fare,
                "taxes": quote.taxes,
                "airport_fee": quote.airport_fee,
                "convenience_fee": quote.convenience_fee,
                "other_fees": quote.other_fees,
                "total_fare": quote.total_fare,
                "currency": "INR",
                "available": str(quote.available).lower(),
                "collected_at": quote.collected_at.isoformat(),
                "raw_reference": f"demo-prototype-2026-{number}",
            })
    print(f"Created {len(quotes)} rows at {OUTPUT}")


if __name__ == "__main__":
    main()
