"""AttractionsSpecialist and its search_attractions tool."""

import logging

from google.adk.agents import LlmAgent

from agents.models import build_model
from config import settings
from providers import get_provider
from schemas import ATTRACTIONS_ID

logger = logging.getLogger(__name__)


async def search_attractions(city: str, category: str = "sightseeing") -> dict:
    """Find top attractions (sightseeing, museums, monuments) in a city.

    Args:
        city: City name, e.g. "Tokyo".
        category: Kind of attraction, e.g. "sightseeing" or "museum".
    """
    try:
        result = await get_provider().get_attractions(city, category)
    except Exception:
        logger.exception("search_attractions failed")
        return {"status": "error", "message": "Attractions data is currently unavailable."}
    output = {
        "status": "success",
        "data_source": result.source,
        "a2ui_surface": "main_view",
        "components": [
            {
                "id": ATTRACTIONS_ID,
                "type": "CardList",
                "title": f"Top Attractions in {city.strip().title()}",
                "items": result.items,
            }
        ],
    }
    if result.fallback_reason:
        output["demo_fallback"] = True
    return output


attractions_agent = LlmAgent(
    name="AttractionsSpecialist",
    description="Handles sightseeing, museums, monuments and other attraction requests.",
    model=build_model(settings.llm_model),
    instruction=(
        "You recommend attractions. Call search_attractions with the city (and category if given) "
        "and briefly summarise only the places the tool returned; never invent places, ratings or costs. "
        "If data_source is 'mock', say these are demo records. Mention that live data was unavailable ONLY if the tool result contains demo_fallback: true. If data_source is 'google_places', say the results come from Google Maps. If the tool returns an error, say attractions "
        "are currently unavailable. If the user's request also asks about food, restaurants or dining, "
        "transfer to DiningSpecialist after you finish; otherwise answer and stop."
    ),
    tools=[search_attractions],
)
