"""Google Places API (New) provider using Text Search.

Results are mapped to the PRD item fields. Nothing is cached: Places content must not be
stored beyond what the Google Maps Platform terms allow.
"""

import httpx

from providers.base import ProviderResult

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.displayName,places.primaryTypeDisplayName,places.rating,places.priceLevel"
MAX_ITEMS = 5
NOT_LISTED = "Not listed"
PRICE_LEVELS = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}


class PlacesError(Exception):
    """Live lookup failed; the message is safe to show (no key, no response body)."""


class GooglePlacesProvider:
    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None, timeout: float = 8.0) -> None:
        self._api_key = api_key
        self._client = client
        self._timeout = timeout

    async def _search(self, query: str) -> list[dict]:
        headers = {"X-Goog-Api-Key": self._api_key, "X-Goog-FieldMask": FIELD_MASK}
        body = {"textQuery": query, "pageSize": MAX_ITEMS}
        try:
            if self._client is not None:
                response = await self._client.post(SEARCH_URL, json=body, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(SEARCH_URL, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise PlacesError("Places request timed out") from exc
        except httpx.HTTPError as exc:
            raise PlacesError("Places request failed") from exc
        if response.status_code != 200:
            raise PlacesError(f"Places returned HTTP {response.status_code}")
        try:
            places = response.json().get("places") or []
        except ValueError as exc:
            raise PlacesError("Places returned invalid JSON") from exc
        if not places:
            raise PlacesError("Places returned no results")
        return places[:MAX_ITEMS]

    @staticmethod
    def _name(place: dict) -> str:
        return (place.get("displayName") or {}).get("text") or NOT_LISTED

    @staticmethod
    def _type(place: dict) -> str:
        return (place.get("primaryTypeDisplayName") or {}).get("text") or NOT_LISTED

    @staticmethod
    def _rating(place: dict) -> str:
        rating = place.get("rating")
        return str(rating) if rating is not None else NOT_LISTED

    async def get_attractions(self, city: str, category: str) -> ProviderResult:
        places = await self._search(f"tourist attractions in {city}")
        items = [
            {"title": self._name(p), "type": self._type(p), "rating": self._rating(p), "cost": NOT_LISTED}
            for p in places
        ]
        return ProviderResult(items, "google_places")

    async def get_restaurants(self, city: str, cuisine: str) -> ProviderResult:
        places = await self._search(f"{cuisine} restaurants in {city}")
        items = [
            {
                "title": self._name(p),
                "cuisine": self._type(p),
                "rating": self._rating(p),
                "price": PRICE_LEVELS.get(p.get("priceLevel", ""), NOT_LISTED),
            }
            for p in places
        ]
        return ProviderResult(items, "google_places")
