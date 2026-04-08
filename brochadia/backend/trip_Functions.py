from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path
import importlib.util
import pandas as pd
import os
import requests
import geopy
from geopy.geocoders import Nominatim
from swarm import Swarm, Agent
import json




load_dotenv(Path(__file__).resolve().parent.parent / '.env')
openAI_client = Swarm()
MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
AMA_KEY = os.getenv("VITE_AMA_API_KEY")
AMA_SEC = os.getenv("VITE_AMA_API_SEC")


geoApp = Nominatim(user_agent="tutorial")

#Amadeus API Calls


def get_access_token(session: requests.Session) -> str:
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AMA_KEY,
        "client_secret": AMA_SEC,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = session.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]
    

def get_city_geocode(city: str, session: requests.Session):
    url = "https://test.api.amadeus.com/v1/reference-data/locations/cities"
    try:
        response = session.get(url, params={"keyword": city})
        if response.status_code == 200:
            data = response.json().get("data") or []
            if data:
                geo = data[0].get("geoCode") or {}
                lat = geo.get("latitude")
                lon = geo.get("longitude")
                if lat is not None and lon is not None:
                    return lat, lon
    except requests.RequestException:
        pass

    # Fallback to geopy when Amadeus fails or returns no usable coordinates.
    try:
        location = geoApp.geocode(city)
    except Exception:
        return None

    if not location:
        return None
    return location.latitude, location.longitude

# Lat Long Agent to find random latitude and longitude pairs to make more travel 
def latLong_Agent(country):
    print("Calling agent for", country)
    selector_agent = Agent(
    name="Country Location Selector",
    instructions=(
            "You are a travel curator. pick at most 3 random longitude and latitude pairs "
            "that is within the location_input variable, whether its a country, city, Lake, or Mountain Range. Return ONLY "
            "a JSON array of tuples of each pairs taken from the input string with float data type."
        ),
        output_type="json",
    )

    response = openAI_client.run(
        agent=selector_agent,
        messages=[
            {
                "role": "user",
                "content": (
                    f"location_input={country} "
                ),
            }
        ],
    )
    content = response.messages[-1].get("content").strip().removeprefix('json').removesuffix('').strip().split("```json")[-1].split("```")[0]
    print(response)
    print(type(json.loads(content)))
    return json.loads(content)