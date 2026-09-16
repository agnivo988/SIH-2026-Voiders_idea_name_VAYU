"""Import the flight prediction CSV into the app's route/airline/fare schema."""
from __future__ import annotations

import csv
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Airline, FareQuote, Route, Source

CITY_CODES = {
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bangalore": "BLR",
    "Kolkata": "CCU",
    "Hyderabad": "HYD",
    "Chennai": "MAA",
}

AIRLINE_CODE_MAP = {
    "AIR INDIA": "AI",
    "AIR_INDIA": "AI",
    "AIR INDIA EXPRESS": "IX",
    "AIRINDIAEXPRESS": "IX",
    "AIRASIA": "I5",
    "GO FIRST": "G8",
    "GO_FIRST": "G8",
    "INDIGO": "6E",
    "VISTARA": "UK",
    "SPICEJET": "SG",
}

AIRLINE_NAME_BY_CODE = {
    "AI": "Air India",
    "IX": "Air India Express",
    "I5": "AirAsia",
    "G8": "Go First",
    "6E": "IndiGo",
    "UK": "Vistara",
    "SG": "SpiceJet",
}


def normalize_airline_name(value: str) -> str:
    return " ".join((value or "").strip().upper().replace("-", " ").replace("_", " ").split())


def airline_code_from_row(value: str) -> str:
    key = normalize_airline_name(value)
    if key in AIRLINE_CODE_MAP:
        return AIRLINE_CODE_MAP[key]
    for alias, code in AIRLINE_CODE_MAP.items():
        if alias in key:
            return code
    raise ValueError(f"Unsupported airline in CSV: {value!r}")


def parse_decimal(raw: str) -> Decimal:
    value = Decimal(str(raw).strip())
    if value < 0:
        raise ValueError("Values cannot be negative")
    return value.quantize(Decimal("0.01"))


def transform_prediction_row(row: dict[str, str], reference_date: date) -> dict[str, object]:
    source_city = (row.get("source_city") or "").strip().title()
    destination_city = (row.get("destination_city") or "").strip().title()
    if source_city not in CITY_CODES or destination_city not in CITY_CODES:
        raise ValueError(f"Unsupported city pair {source_city!r} -> {destination_city!r}")

    airline_code = airline_code_from_row(row.get("airline") or "")
    days_left = int((row.get("days_left") or "0").strip() or 0)
    total_fare = parse_decimal(row.get("price") or "0")
    travel_date = reference_date + timedelta(days=days_left)

    base_fare = (total_fare * Decimal("0.76")).quantize(Decimal("0.01"))
    taxes = (total_fare * Decimal("0.10")).quantize(Decimal("0.01"))
    airport_fee = (total_fare * Decimal("0.08")).quantize(Decimal("0.01"))
    convenience_fee = (total_fare * Decimal("0.04")).quantize(Decimal("0.01"))
    other_fees = (total_fare - base_fare - taxes - airport_fee - convenience_fee).quantize(Decimal("0.01"))

    return {
        "route_code": f"{CITY_CODES[source_city]}-{CITY_CODES[destination_city]}",
        "airline_code": airline_code,
        "travel_date": travel_date,
        "advance_days": days_left,
        "flight_number": (row.get("flight") or "UNKNOWN").strip() or "UNKNOWN",
        "fare_class": (row.get("class") or "Economy").strip() or "Economy",
        "base_fare": base_fare,
        "taxes": taxes,
        "airport_fee": airport_fee,
        "convenience_fee": convenience_fee,
        "other_fees": other_fees,
        "total_fare": total_fare,
        "currency": "INR",
        "available": total_fare > 0,
        "raw_reference": f"flight_prediction:{(row.get('ID') or '').strip()}",
        "collected_at": datetime.utcnow(),
    }


def ensure_route_and_airline(db, route_code: str, airline_code: str) -> tuple[Route, Airline]:
    route = db.scalar(select(Route).where(Route.route_code == route_code))
    if route is None:
        origin, destination = route_code.split("-")
        route = Route(origin=origin, destination=destination, route_code=route_code, weight=Decimal("1.0"))
        db.add(route)
        db.flush()

    airline = db.scalar(select(Airline).where(Airline.code == airline_code))
    if airline is None:
        name = AIRLINE_NAME_BY_CODE.get(airline_code, airline_code)
        airline = Airline(name=name, code=airline_code, active=True)
        db.add(airline)
        db.flush()

    return route, airline


def import_prediction_csv(path: Path, source_name: str = "Flight Predictions CSV", reference_date: date | None = None, batch_size: int = 5000) -> tuple[int, int, int]:
    Base.metadata.create_all(bind=engine)
    inserted = skipped = rejected = 0
    ref_date = reference_date or date.today()
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.name == source_name))
        if source is None:
            source = Source(name=source_name, type="import", enabled=True, is_demo=False)
            db.add(source)
            db.commit()
            db.refresh(source)
        routes = {route.route_code: route for route in db.scalars(select(Route))}
        airlines = {airline.code: airline for airline in db.scalars(select(Airline))}
        known_references = set(db.scalars(select(FareQuote.raw_reference).where(FareQuote.source_id == source.id)).all())
        batch: list[FareQuote] = []
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"CSV is empty or missing a header: {path}")
            for line_number, row in enumerate(reader, start=2):
                reference = (row.get("ID") or "").strip()
                if not reference:
                    rejected += 1
                    print(f"Rejected line {line_number}: missing ID", file=sys.stderr)
                    continue
                raw_reference = f"flight_prediction:{reference}"
                try:
                    transformed = transform_prediction_row(row, ref_date)
                    route_code = str(transformed["route_code"])
                    airline_code = str(transformed["airline_code"])
                    if route_code not in routes:
                        route, airline = ensure_route_and_airline(db, route_code, airline_code)
                        routes[route_code] = route
                        airlines[airline_code] = airline
                    elif airline_code not in airlines:
                        route = routes[route_code]
                        airline = ensure_route_and_airline(db, route_code, airline_code)[1]
                        airlines[airline_code] = airline
                    route = routes[route_code]
                    airline = airlines[airline_code]
                    if raw_reference in known_references:
                        skipped += 1
                        continue
                    batch.append(FareQuote(
                        source_id=source.id,
                        airline_id=airline.id,
                        route_id=route.id,
                        collected_at=transformed["collected_at"],
                        travel_date=transformed["travel_date"],
                        advance_days=transformed["advance_days"],
                        flight_number=transformed["flight_number"],
                        fare_class=transformed["fare_class"],
                        base_fare=transformed["base_fare"],
                        taxes=transformed["taxes"],
                        airport_fee=transformed["airport_fee"],
                        convenience_fee=transformed["convenience_fee"],
                        other_fees=transformed["other_fees"],
                        total_fare=transformed["total_fare"],
                        currency=transformed["currency"],
                        available=transformed["available"],
                        raw_reference=raw_reference,
                        data_quality_score=Decimal("100.00"),
                        is_outlier=False,
                    ))
                    known_references.add(raw_reference)
                    if len(batch) >= batch_size:
                        db.add_all(batch)
                        db.commit()
                        inserted += len(batch)
                        batch.clear()
                except (KeyError, ValueError, InvalidOperation) as exc:
                    rejected += 1
                    print(f"Rejected line {line_number}: {exc}", file=sys.stderr)
        if batch:
            db.add_all(batch)
            db.commit()
            inserted += len(batch)
    return inserted, skipped, rejected


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Import the flight prediction dataset into the project database")
    parser.add_argument("file", type=Path, help="Path to the CSV file")
    parser.add_argument("--reference-date", type=date.fromisoformat, default=date.today(), help="Base date for travel_date calculation")
    parser.add_argument("--source", default="Flight Predictions CSV", help="Label for the imported source")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()

    inserted, skipped, rejected = import_prediction_csv(args.file, args.source, args.reference_date, args.batch_size)
    print(f"Imported={inserted} skipped_existing={skipped} rejected={rejected}")


if __name__ == "__main__":
    main()
