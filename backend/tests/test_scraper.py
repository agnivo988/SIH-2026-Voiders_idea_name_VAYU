from datetime import date

import pytest

from app.services.scraper import ApprovedBrowserAdapter, DemoSourceAdapter


@pytest.mark.asyncio
async def test_demo_adapter_returns_route_quotes():
    result = await DemoSourceAdapter().collect_fares("DEL", "BOM", date(2026, 1, 1))
    assert result.status == "SUCCESS"
    assert result.quotes
    assert all(item.route_code == "DEL-BOM" for item in result.quotes)


@pytest.mark.asyncio
async def test_unconfigured_live_adapter_is_explicitly_blocked():
    result = await ApprovedBrowserAdapter().collect_fares("DEL", "BOM", date(2026, 1, 1))
    assert result.status == "SCRAPE_BLOCKED"
    assert not result.quotes
