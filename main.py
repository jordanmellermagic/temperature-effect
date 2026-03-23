from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import anthropic
import os
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store — same pattern as Double Date
latest_result: dict = {}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


class QueryPayload(BaseModel):
    query: str  # Raw string from Goo, e.g. "What is the temperature in Tokyo"


def celsius_to_fahrenheit(c: float) -> float:
    return round((c * 9 / 5) + 32, 1)


async def extract_place_with_ai(raw_query: str) -> str:
    """Use Claude to extract a clean place name from whatever Goo sends."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Extract only the place name from this query. "
                    f"Return ONLY the place name, nothing else. No punctuation, no explanation.\n\n"
                    f"Query: {raw_query}"
                ),
            }
        ],
    )
    return message.content[0].text.strip()


async def get_weather(place: str) -> dict:
    """Geocode the place name then fetch current temperature from Open-Meteo."""
    async with httpx.AsyncClient() as client:
        # Step 1: Geocode
        geo_resp = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": place, "count": 1, "language": "en", "format": "json"},
        )
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            raise HTTPException(status_code=404, detail=f"Could not find place: {place}")

        result = geo_data["results"][0]
        lat = result["latitude"]
        lon = result["longitude"]
        display_name = result.get("name", place)
        country = result.get("country", "")

        # Step 2: Get current temperature
        weather_resp = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "temperature_unit": "celsius",
            },
        )
        weather_data = weather_resp.json()
        temp_c = weather_data["current_weather"]["temperature"]
        temp_f = celsius_to_fahrenheit(temp_c)

        return {
            "place": display_name,
            "country": country,
            "temperature_f": temp_f,
            "temperature_c": temp_c,
        }


@app.post("/submit")
async def submit_query(payload: QueryPayload):
    """
    Goo hits this endpoint with the raw spectator query.
    We extract the place, fetch weather, and store the result.
    """
    global latest_result

    raw = payload.query.strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty query")

    # Extract place name via AI
    place = await extract_place_with_ai(raw)

    # Fetch weather
    weather = await get_weather(place)

    latest_result = {
        "raw_query": raw,
        "place": weather["place"],
        "country": weather["country"],
        "temperature_f": weather["temperature_f"],
        "temperature_c": weather["temperature_c"],
        "ready": True,
    }

    return latest_result


@app.get("/poll")
async def poll():
    """Performer dashboard polls this to get the latest result."""
    return latest_result


@app.delete("/reset")
async def reset():
    """Clear the result between performances."""
    global latest_result
    latest_result = {}
    return {"status": "cleared"}


@app.get("/health")
async def health():
    return {"status": "ok"}
