from dataclasses import dataclass
from datetime import date, datetime, timedelta
import hashlib
import math
import random


ROUTES = ["DEL-BOM", "DEL-BLR", "BOM-BLR", "DEL-CCU", "BLR-HYD", "MAA-DEL", "DEL-HYD", "BOM-DEL", "BLR-DEL", "CCU-DEL"]
AIRLINES = [("IndiGo", "6E"), ("Air India", "AI"), ("Air India Express", "IX"), ("Akasa Air", "QP"), ("SpiceJet", "SG")]
ADVANCE_WINDOWS = [1, 7, 15, 30, 45]
ROUTE_BASES = {route: 3500 + index * 270 for index, route in enumerate(ROUTES)}
AIRLINE_FACTOR = {"6E": 0.94, "AI": 1.08, "IX": 0.91, "QP": 0.98, "SG": 0.88}


@dataclass(frozen=True)
class DemoQuote:
    route_code: str
    airline_code: str
    collected_at: datetime
    travel_date: date
    advance_days: int
    flight_number: str
    fare_class: str
    base_fare: float
    taxes: float
    airport_fee: float
    convenience_fee: float
    other_fees: float
    available: bool

    @property
    def total_fare(self) -> float:
        return round(self.base_fare + self.taxes + self.airport_fee + self.convenience_fee + self.other_fees, 2)


def _seed(*parts: object) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest[:16], 16)


def generate_quotes(start_date: date, days: int = 30, seed: int = 2026) -> list[DemoQuote]:
    quotes: list[DemoQuote] = []
    for day_offset in range(days):
        travel_date = start_date + timedelta(days=day_offset)
        day_demand = 0.08 * math.sin(day_offset / 3.7) + (0.14 if travel_date.weekday() in (4, 6) else 0)
        season = 0.10 * math.sin((travel_date.timetuple().tm_yday + 30) / 35)
        for route in ROUTES:
            for airline_name, airline_code in AIRLINES:
                for advance_days in ADVANCE_WINDOWS:
                    rng = random.Random(_seed(seed, route, airline_code, travel_date, advance_days))
                    observations = 2 + (rng.random() > 0.35)
                    for observation in range(observations):
                        route_factor = ROUTE_BASES[route] / 3500
                        lead_time = 0.62 + 0.72 * math.exp(-advance_days / 9)
                        airline_factor = AIRLINE_FACTOR[airline_code]
                        noise = rng.gauss(0, 0.045)
                        demand = day_demand + season + 0.08 * math.sin(day_offset / 2.4 + ROUTES.index(route))
                        base = ROUTE_BASES[route] * route_factor * lead_time * airline_factor * (1 + demand + noise)
                        base = round(max(1800, base), 2)
                        available = rng.random() > 0.035
                        if not available:
                            base = 0
                        taxes = round(base * 0.05, 2)
                        airport_fee = round(250 + rng.uniform(-15, 25), 2)
                        convenience_fee = round(rng.uniform(0, 180), 2)
                        other_fees = round(rng.uniform(0, 80), 2)
                        quotes.append(DemoQuote(
                            route_code=route,
                            airline_code=airline_code,
                            collected_at=datetime.combine(travel_date - timedelta(days=advance_days), datetime.min.time()),
                            travel_date=travel_date,
                            advance_days=advance_days,
                            flight_number=f"{airline_code}{100 + observation + ROUTES.index(route)}",
                            fare_class="Economy",
                            base_fare=base,
                            taxes=taxes,
                            airport_fee=airport_fee,
                            convenience_fee=convenience_fee,
                            other_fees=other_fees,
                            available=available,
                        ))
    return quotes
