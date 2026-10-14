"""TravelCoordinator: single owner of intent routing across both specialists."""

from google.adk.agents import LlmAgent

from agents.attractions_agent import attractions_agent
from agents.dining_agent import dining_agent
from agents.models import build_model
from config import settings

travel_coordinator = LlmAgent(
    name="TravelCoordinator",
    description="Routes travel requests to the right specialist.",
    model=build_model(settings.llm_model),
    instruction=(
        "You coordinate travel recommendations. Route sightseeing, museum and monument requests to "
        "AttractionsSpecialist and food, restaurant and dining requests to DiningSpecialist. When a "
        "request asks for both, use both specialists, one after the other. Never invent places; "
        "recommendations come only from the specialists. If one specialist is unavailable, say which "
        "part is unavailable and still share the other's results."
    ),
    sub_agents=[attractions_agent, dining_agent],
)
