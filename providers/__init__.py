import logging

from config import settings
from providers.base import PlacesProvider, ProviderResult
from providers.google_places import GooglePlacesProvider, PlacesError
from providers.mock import MockProvider

logger = logging.getLogger(__name__)


class FallbackProvider:
    """Live provider that falls back to labelled mock records on any failure."""

    def __init__(self, live: PlacesProvider, mock: PlacesProvider) -> None:
        self._live = live
        self._mock = mock

    async def get_attractions(self, city: str, category: str) -> ProviderResult:
        try:
            return await self._live.get_attractions(city, category)
        except PlacesError as exc:
            return await self._fallback(self._mock.get_attractions(city, category), exc)

    async def get_restaurants(self, city: str, cuisine: str) -> ProviderResult:
        try:
            return await self._live.get_restaurants(city, cuisine)
        except PlacesError as exc:
            return await self._fallback(self._mock.get_restaurants(city, cuisine), exc)

    @staticmethod
    async def _fallback(mock_call, exc: Exception) -> ProviderResult:
        logger.warning("Places lookup failed, using demo records: %s", exc)
        result = await mock_call
        return ProviderResult(result.items, "mock", fallback_reason=str(exc))


def get_provider() -> PlacesProvider:
    if settings.data_provider == "mock":
        return MockProvider()
    if settings.data_provider == "google_places":
        if not settings.places_api_key:
            logger.warning("DATA_PROVIDER=google_places but PLACES_API_KEY is empty; using demo records")
            return MockProvider()
        return FallbackProvider(GooglePlacesProvider(settings.places_api_key), MockProvider())
    raise ValueError(f"Unsupported DATA_PROVIDER: {settings.data_provider!r}")
