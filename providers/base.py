"""Data-provider interface shared by the mock and Google Places providers."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResult:
    items: list[dict[str, str]]
    source: str  # "mock" or "google_places"
    fallback_reason: str | None = None  # set when mock records replaced a failed live lookup


class PlacesProvider(Protocol):
    async def get_attractions(self, city: str, category: str) -> ProviderResult: ...

    async def get_restaurants(self, city: str, cuisine: str) -> ProviderResult: ...
