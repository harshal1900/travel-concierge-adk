"""AttractionsSpecialist and its search_attractions tool."""

import logging

from google.adk.agents import LlmAgent

from config import settings
from providers import get_provider
from schemas import ATTRACTIONS_ID

logger = logging.getLogger(__name__)


def search_attractions(city: str, category: str = "sightseeing") -> dict:
    """Find top attractions (sightseeing, museums, monuments) in a city.

    Args:
        city: City name, e.g. "Tokyo".
        category: Kind of attraction, e.g. "sightseeing" or "museum".
    """
    try:
        items = get_provider().get_attractions(city, category)
    except Exception:
        logger.exception("search_attractions failed")
        return {"status": "error", "message": "Attractions data is currently unavailable."}
    return {
        "status": "success",
        "data_source": settings.data_provider,
        "a2ui_surface": "main_view",
        "components": [
            {
                "id": ATTRACTIONS_ID,
                "type": "CardList",
                "title": f"Top Attractions in {city.strip().title()}",
                "items": items,
            }
        ],
    }


attractions_agent = LlmAgent(
    name="AttractionsSpecialist",
    description="Handles sightseeing, museums, monuments and other attraction requests.",
    model=settings.llm_model,
    instruction=(
        "You recommend attractions. Call search_attractions with the city (and category if given) "
        "and briefly summarise only the places the tool returned; never invent places, ratings or costs. "
        "If data_source is 'mock', say these are demo records. If the tool returns an error, say attractions "
        "are currently unavailable. If the user's request also asks about food, restaurants or dining, "
        "transfer to DiningSpecialist after you finish; otherwise answer and stop."
    ),
    tools=[search_attractions],
)
