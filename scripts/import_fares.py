"""Bulk-import real fare observations from CSV into PostgreSQL/Supabase.

Expected columns:
route_code, airline_code, travel_date, advance_days, flight_number,
fare_class, base_fare, taxes, airport_fee, convenience_fee, other_fees,
currency, available, collected_at, raw_reference
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Airline, FareQuote, Route, Source

REQUIRED_COLUMNS = {"route_code", "airline_code", "travel_date", "advance_days", "base_fare", "taxes", "airport_fee", "convenience_fee", "other_fees", "total_fare", "raw_reference"}


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value) if value else datetime.utcnow()


def money(value: str) -> Decimal:
    parsed = Decimal(value)
    if parsed < 0:
        raise ValueError("money values cannot be negative")
    return parsed.quantize(Decimal("0.01"))


def import_file(path: Path, source_name: str, batch_size: int, is_demo: bool = False) -> tuple[int, int, int]:
    inserted = skipped = rejected = 0
    with SessionLocal() as db, path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        source = db.scalar(select(Source).where(Source.name == source_name))
        if source is None:
            source = Source(name=source_name, type="demo" if is_demo else "import", enabled=True, is_demo=is_demo)
            db.add(source)
            db.commit()
            db.refresh(source)
        routes = {item.route_code: item for item in db.scalars(select(Route))}
        airlines = {item.code: item for item in db.scalars(select(Airline))}
        known_references = set(db.scalars(select(FareQuote.raw_reference).where(FareQuote.source_id == source.id)).all())
        batch: list[FareQuote] = []
        for line_number, row in enumerate(reader, start=2):
            reference = (row.get("raw_reference") or "").strip()
            try:
                route_code = row["route_code"].strip().upper()
                airline_code = row["airline_code"].strip().upper()
                if not reference or route_code not in routes or airline_code not in airlines:
                    raise ValueError("unknown route/airline or empty raw_reference")
                if reference in known_references:
                    skipped += 1
                    continue
                base_fare = money(row["base_fare"])
                taxes = money(row["taxes"])
                airport_fee = money(row["airport_fee"])
                convenience_fee = money(row["convenience_fee"])
                other_fees = money(row["other_fees"])
                total_fare = money(row["total_fare"])
                if total_fare <= 0 or base_fare <= 0:
                    raise ValueError("fares must be greater than zero")
                expected_total = base_fare + taxes + airport_fee + convenience_fee + other_fees
                if abs(total_fare - expected_total) > Decimal("0.02"):
                    raise ValueError("total_fare does not match fare components")
                batch.append(FareQuote(
                    source_id=source.id, route_id=routes[route_code].id, airline_id=airlines[airline_code].id,
                    collected_at=parse_datetime(row.get("collected_at", "")), travel_date=parse_date(row["travel_date"]),
                    advance_days=int(row["advance_days"]), flight_number=row.get("flight_number", "UNKNOWN"),
                    fare_class=row.get("fare_class", "Economy"), base_fare=base_fare, taxes=taxes,
                    airport_fee=airport_fee, convenience_fee=convenience_fee, other_fees=other_fees,
                    total_fare=total_fare, currency=row.get("currency", "INR").upper(),
                    available=(row.get("available", "true").strip().lower() not in {"false", "0", "no"}),
                    raw_reference=reference, data_quality_score=Decimal("100.00"), is_outlier=False,
                ))
                known_references.add(reference)
                if len(batch) >= batch_size:
                    db.add_all(batch)
                    db.commit()
                    inserted += len(batch)
                    batch.clear()
            except (KeyError, ValueError, InvalidOperation) as error:
                rejected += 1
                print(f"Rejected line {line_number}: {error}", file=sys.stderr)
        if batch:
            db.add_all(batch)
            db.commit()
            inserted += len(batch)
    return inserted, skipped, rejected


def main() -> None:
    parser = argparse.ArgumentParser(description="Import real fare observations into PostgreSQL/Supabase")
    parser.add_argument("file", type=Path, help="CSV file to import")
    parser.add_argument("--source", default="Approved Data Import", help="Source label stored in the database")
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--demo", action="store_true", help="Mark imported rows as synthetic demo data")
    args = parser.parse_args()
    inserted, skipped, rejected = import_file(args.file, args.source, args.batch_size, args.demo)
    print(f"Imported={inserted} skipped_existing={skipped} rejected={rejected}")


if __name__ == "__main__":
    main()
