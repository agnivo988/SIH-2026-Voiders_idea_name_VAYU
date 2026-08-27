from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
import asyncio
import logging
from urllib.parse import urljoin

import httpx
from cachetools import TTLCache

from app.config import settings
from app.services.demo import DemoQuote, generate_quotes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionResult:
    status: str
    quotes: list[DemoQuote]
    error: str | None = None


class SourceAdapter(ABC):
    def __init__(self, request_delay: float = 5.0) -> None:
        self.request_delay = request_delay

    @abstractmethod
    async def collect_fares(self, origin: str, destination: str, travel_date: date) -> CollectionResult:
        raise NotImplementedError


class DemoSourceAdapter(SourceAdapter):
    async def collect_fares(self, origin: str, destination: str, travel_date: date) -> CollectionResult:
        await asyncio.sleep(0)
        route = f"{origin.upper()}-{destination.upper()}"
        quotes = [quote for quote in generate_quotes(travel_date, days=1) if quote.route_code == route]
        return CollectionResult(status="SUCCESS", quotes=quotes)


class ApprovedBrowserAdapter(SourceAdapter):
    """Extension point for approved public pages; it never bypasses access controls."""

    async def collect_fares(self, origin: str, destination: str, travel_date: date) -> CollectionResult:
        logger.warning("Live collection is disabled until an approved source configuration exists")
        return CollectionResult(status="SCRAPE_BLOCKED", quotes=[], error="No approved live source configured")


class ApprovedJsonApiAdapter(SourceAdapter):
    """Collects only from an explicitly approved JSON API contract.

    Expected response: {"quotes": [{...FareQuote fields...}]}.
    The API owner must authorize this client and provide the endpoint.
    """

    def __init__(self, api_url: str | None = None, request_delay: float | None = None) -> None:
        super().__init__(request_delay if request_delay is not None else settings.scrape_request_delay)
        self.api_url = api_url or settings.live_api_url
        self.cache: TTLCache[str, dict] = TTLCache(maxsize=256, ttl=300)

    async def collect_fares(self, origin: str, destination: str, travel_date: date) -> CollectionResult:
        if not settings.enable_live_scraping or not self.api_url:
            return CollectionResult(status="SCRAPE_BLOCKED", quotes=[], error="Live scraping is disabled or API URL is not configured")
        cache_key = f"{origin.upper()}-{destination.upper()}:{travel_date.isoformat()}"
        payload = self.cache.get(cache_key)
        if payload is None:
            robots_url = urljoin(self.api_url, "/robots.txt")
            try:
                async with httpx.AsyncClient(timeout=settings.live_request_timeout, follow_redirects=False, headers={"User-Agent": settings.live_user_agent}) as client:
                    robots = await client.get(robots_url)
                    if robots.status_code == 403 or robots.status_code >= 500:
                        return CollectionResult(status="SCRAPE_BLOCKED", quotes=[], error=f"robots.txt denied or unavailable ({robots.status_code})")
                    await asyncio.sleep(self.request_delay)
                    for attempt in range(settings.live_max_retries + 1):
                        response = await client.get(self.api_url, params={"origin": origin.upper(), "destination": destination.upper(), "travel_date": travel_date.isoformat()})
                        if response.status_code in {401, 403, 429}:
                            return CollectionResult(status="SCRAPE_BLOCKED", quotes=[], error=f"source denied request ({response.status_code})")
                        if response.status_code < 500:
                            response.raise_for_status()
                            payload = response.json()
                            self.cache[cache_key] = payload
                            break
                        if attempt < settings.live_max_retries:
                            await asyncio.sleep(2 ** attempt)
                    else:
                        return CollectionResult(status="FAILED", quotes=[], error="source remained unavailable after retries")
            except (httpx.HTTPError, ValueError) as error:
                logger.warning("Approved live source failed: %s", error)
                return CollectionResult(status="FAILED", quotes=[], error=str(error))
        if not isinstance(payload, dict) or not isinstance(payload.get("quotes"), list):
            return CollectionResult(status="FAILED", quotes=[], error="approved API returned an invalid quote payload")
        normalized: list[DemoQuote] = []
        for item in payload["quotes"]:
            try:
                if not isinstance(item, dict):
                    raise ValueError("quote is not an object")
                base_fare = float(item["base_fare"])
                taxes = float(item.get("taxes", 0))
                airport_fee = float(item.get("airport_fee", 0))
                convenience_fee = float(item.get("convenience_fee", 0))
                other_fees = float(item.get("other_fees", 0))
                if base_fare <= 0 or any(value < 0 for value in (taxes, airport_fee, convenience_fee, other_fees)):
                    raise ValueError("invalid fare components")
                normalized.append(DemoQuote(
                    route_code=f"{origin.upper()}-{destination.upper()}",
                    airline_code=str(item["airline_code"]).upper(),
                    collected_at=datetime.fromisoformat(str(item.get("collected_at", datetime.utcnow().isoformat()))),
                    travel_date=travel_date,
                    advance_days=int(item["advance_days"]),
                    flight_number=str(item.get("flight_number", "UNKNOWN")),
                    fare_class=str(item.get("fare_class", "Economy")),
                    base_fare=base_fare,
                    taxes=taxes,
                    airport_fee=airport_fee,
                    convenience_fee=convenience_fee,
                    other_fees=other_fees,
                    available=bool(item.get("available", True)),
                ))
            except (KeyError, TypeError, ValueError) as error:
                logger.warning("Rejected malformed live quote: %s", error)
        return CollectionResult(status="SUCCESS", quotes=normalized)
