from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from app.services.demo import DemoQuote


@dataclass
class CleaningStats:
    raw: int = 0
    valid: int = 0
    invalid: int = 0
    duplicates: int = 0
    sold_out: int = 0
    outliers: int = 0


def clean_quotes(quotes: list[DemoQuote], use_outliers: bool = True) -> tuple[list[DemoQuote], CleaningStats]:
    stats = CleaningStats(raw=len(quotes))
    valid: list[DemoQuote] = []
    seen: set[tuple[object, ...]] = set()
    for quote in quotes:
        key = (quote.route_code, quote.airline_code, quote.travel_date, quote.advance_days, quote.fare_class, quote.flight_number, quote.collected_at)
        if key in seen:
            stats.duplicates += 1
            continue
        seen.add(key)
        if quote.base_fare <= 0 or quote.total_fare <= 0:
            stats.invalid += 1
            if not quote.available:
                stats.sold_out += 1
            continue
        valid.append(quote)
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for quote in valid:
        grouped[(quote.route_code, quote.advance_days)].append(quote.total_fare)
    bounds: dict[tuple[str, int], tuple[float, float]] = {}
    for key, values in grouped.items():
        ordered = sorted(values)
        q1 = ordered[len(ordered) // 4]
        q3 = ordered[(len(ordered) * 3) // 4]
        spread = q3 - q1
        bounds[key] = (q1 - 1.5 * spread, q3 + 1.5 * spread)
    clean: list[DemoQuote] = []
    for quote in valid:
        lower, upper = bounds[(quote.route_code, quote.advance_days)]
        if quote.total_fare < lower or quote.total_fare > upper:
            stats.outliers += 1
            if use_outliers:
                continue
        clean.append(quote)
    stats.valid = len(clean)
    return clean, stats
