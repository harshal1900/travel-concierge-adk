"""DiningSpecialist and its find_restaurants tool."""

import logging

from google.adk.agents import LlmAgent

from agents.models import build_model
from config import settings
from providers import get_provider
from schemas import DINING_ID

logger = logging.getLogger(__name__)


async def find_restaurants(city: str, cuisine: str = "local") -> dict:
    """Find recommended restaurants in a city.

    Args:
        city: City name, e.g. "Tokyo".
        cuisine: Cuisine type, e.g. "sushi" or "local".
    """
    try:
        result = await get_provider().get_restaurants(city, cuisine)
    except Exception:
        logger.exception("find_restaurants failed")
        return {"status": "error", "message": "Dining data is currently unavailable."}
    output = {
        "status": "success",
        "data_source": result.source,
        "a2ui_surface": "main_view",
        "components": [
            {
                "id": DINING_ID,
                "type": "CardList",
                "title": f"Recommended Dining in {city.strip().title()}",
                "items": result.items,
            }
        ],
    }
    if result.fallback_reason:
        output["demo_fallback"] = True
    return output


dining_agent = LlmAgent(
    name="DiningSpecialist",
    description="Handles food, restaurant and dining requests.",
    model=build_model(settings.llm_model),
    instruction=(
        "You recommend restaurants. Call find_restaurants with the city (and cuisine if given) "
        "and briefly summarise only the places the tool returned; never invent places, ratings or prices. "
        "If data_source is 'mock', say these are demo records. Mention that live data was unavailable ONLY if the tool result contains demo_fallback: true. If data_source is 'google_places', say the results come from Google Maps. If the tool returns an error, say dining "
        "is currently unavailable. If the user's request also asks about sightseeing, museums or monuments "
        "and attractions were not yet provided in this conversation turn, transfer to AttractionsSpecialist "
        "after you finish; otherwise answer and stop."
    ),
    tools=[find_restaurants],
)
