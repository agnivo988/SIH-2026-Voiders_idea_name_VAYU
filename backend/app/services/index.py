from collections import defaultdict
from datetime import date
from statistics import median

from app.services.demo import DemoQuote, ROUTES


def route_daily_medians(quotes: list[DemoQuote]) -> dict[tuple[date, str], float]:
    values: dict[tuple[date, str], list[float]] = defaultdict(list)
    for quote in quotes:
        values[(quote.travel_date, quote.route_code)].append(quote.total_fare)
    return {key: round(median(fares), 2) for key, fares in values.items()}


def calculate_index(quotes: list[DemoQuote], route_weights: dict[str, float], base_days: int = 7) -> list[dict[str, object]]:
    medians = route_daily_medians(quotes)
    dates = sorted({quote.travel_date for quote in quotes})
    base_dates = set(dates[:base_days])
    base_by_route: dict[str, list[float]] = defaultdict(list)
    for (day, route), value in medians.items():
        if day in base_dates:
            base_by_route[route].append(value)
    base = {route: median(values) for route, values in base_by_route.items() if values}
    total_weight = sum(route_weights.values()) or 1
    weights = {route: weight / total_weight for route, weight in route_weights.items()}
    results: list[dict[str, object]] = []
    for day in dates:
        relatives = []
        sample_count = 0
        for route, weight in weights.items():
            current = medians.get((day, route))
            if current and route in base:
                relatives.append(weight * current / base[route] * 100)
                sample_count += 1
        if relatives:
            results.append({"date": day, "index_value": round(sum(relatives), 4), "sample_count": sample_count})
    return results
