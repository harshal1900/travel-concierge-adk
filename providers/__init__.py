from config import settings
from providers.base import PlacesProvider
from providers.mock import MockProvider


def get_provider() -> PlacesProvider:
    if settings.data_provider == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported DATA_PROVIDER: {settings.data_provider!r}")
