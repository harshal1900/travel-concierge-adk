"""Mock provider: reads demo records from JSON files in MOCK_DATA_DIR."""

import json
from pathlib import Path

from config import settings
from providers.base import ProviderResult

DEFAULT_KEY = "_default"


class MockProvider:
    def __init__(self, data_dir: str | None = None) -> None:
        self._dir = Path(data_dir or settings.mock_data_dir)

    def _load(self, filename: str, city: str) -> list[dict[str, str]]:
        with (self._dir / filename).open(encoding="utf-8") as f:
            records = json.load(f)
        return list(records.get(city.strip().lower()) or records[DEFAULT_KEY])

    async def get_attractions(self, city: str, category: str) -> ProviderResult:
        return ProviderResult(self._load("attractions.json", city), "mock")

    async def get_restaurants(self, city: str, cuisine: str) -> ProviderResult:
        return ProviderResult(self._load("restaurants.json", city), "mock")
