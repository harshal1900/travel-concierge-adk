"""Data-provider interface shared by the mock and (later) Google Places providers."""

from typing import Protocol


class PlacesProvider(Protocol):
    def get_attractions(self, city: str, category: str) -> list[dict[str, str]]: ...

    def get_restaurants(self, city: str, cuisine: str) -> list[dict[str, str]]: ...
