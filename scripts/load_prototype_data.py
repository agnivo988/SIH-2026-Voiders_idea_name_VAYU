"""Create and bulk-load the labelled prototype dataset into the configured database."""
from __future__ import annotations

import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Airline, Route
from app.services.demo import AIRLINES, ROUTES
from create_prototype_csv import OUTPUT, main as create_csv
from import_fares import import_file


def ensure_reference_data() -> None:
    with SessionLocal() as db:
        for route_code in ROUTES:
            origin, destination = route_code.split("-")
            if db.scalar(select(Route).where(Route.route_code == route_code)) is None:
                db.add(Route(origin=origin, destination=destination, route_code=route_code, weight=Decimal("1.0")))
        for name, code in AIRLINES:
            if db.scalar(select(Airline).where(Airline.code == code)) is None:
                db.add(Airline(name=name, code=code, active=True))
        db.commit()


def main() -> None:
    create_csv()
    ensure_reference_data()
    inserted, skipped, rejected = import_file(OUTPUT, "Synthetic Prototype CSV", 5000, is_demo=True)
    print(f"Loaded prototype data into database: inserted={inserted}, skipped_existing={skipped}, rejected={rejected}")


if __name__ == "__main__":
    main()
