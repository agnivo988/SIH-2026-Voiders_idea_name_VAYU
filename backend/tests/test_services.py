from datetime import date

from app.services.cleaning import clean_quotes
from app.services.demo import generate_quotes
from app.services.index import calculate_index, route_daily_medians


def test_demo_generation_is_reproducible_and_correlated():
    first = generate_quotes(date(2026, 1, 1), days=2)
    second = generate_quotes(date(2026, 1, 1), days=2)
    assert first == second
    assert len(first) > 200
    assert len({quote.total_fare for quote in first if quote.available}) > 20


def test_cleaning_removes_invalid_and_returns_stats():
    quotes = generate_quotes(date(2026, 1, 1), days=1)
    clean, stats = clean_quotes(quotes)
    assert stats.raw == len(quotes)
    assert stats.invalid > 0
    assert stats.valid == len(clean)
    assert all(quote.total_fare > 0 for quote in clean)


def test_index_uses_route_weights_and_medians():
    quotes = generate_quotes(date(2026, 1, 1), days=8)
    clean, _ = clean_quotes(quotes)
    medians = route_daily_medians(clean)
    results = calculate_index(clean, {"DEL-BOM": 2, "DEL-BLR": 1})
    assert medians
    assert results
    assert 80 < float(results[0]["index_value"]) < 120
