from google.adk.agents import Agent
from google.adk.tools.retrieval
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import json

def get_recipes(query: str) -> dict:
    """Get recipe information for a specific query."""
    
    return 

root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent suggest recipes based on the user query."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about recipes."
    ),
    tools=[get_recipes],
)