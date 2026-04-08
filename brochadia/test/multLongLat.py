import json
import os
from pathlib import Path
import osmnx as ox
import random
from shapely.geometry import Point
from swarm import Swarm, Agent
import geopy
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import matplotlib.pyplot as plt

import spacy
nlp = spacy.load("en_core_web_sm")


load_dotenv(Path(__file__).resolve().parent.parent / ".env")
openAI_client = Swarm()
geoApp = Nominatim(user_agent="tutorial")
MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
MONGO_URI = (
    f"mongodb+srv://azad:{MONGO_PASSWORD}@dwcluster.2zyrq7o.mongodb.net/"
    "?appName=DWCluster"
)


# Lat Long Agent to find random latitude and longitude pairs to make more travel 
def latLong_Agent(country):
    print("Calling agent for", country)
    selector_agent = Agent(
    name="Country Location Selector",
    instructions=(
            "You are a travel curator. pick at most 3 random longitude and latitude pairs "
            "that is within the location_input variable, whether its a country, city, Lake, or Mountain Range. Return ONLY "
            "a JSON array of tuples of each pairs taken from the input string."
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
    print(content)
    return json.loads(content)


def get_city_coords_from_geoapp(city_name):
    try:
        location = geoApp.geocode(city_name)
    except Exception:
        return []

    if not location:
        return []

    return [[location.latitude, location.longitude]]


def get_all_user_travel_preferences():
    if not MONGO_PASSWORD:
        raise RuntimeError("VITE_MONGO_PASSWORD is not set in the project .env file.")

    client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

    try:
        users_collection = client["Brochadia"]["users"]
        users = users_collection.find(
            {},
            {
                "email": 1,
                "full_name": 1,
                "travel_preference": 1,
                "location_preference": 1
            },
        )

        return [
            {
                "location_preference": user.get("location_preference"),
            }
            for user in users
        ]
    finally:
        client.close()


if __name__ == "__main__":
    data = get_all_user_travel_preferences()
    points = []
    #print(data)
    for user in data:
        #print(user)
        places = [
            (place ,user['location_preference'][place]) for place in user['location_preference'] if any(ent.label_ in ["LOC", "GPE"] for ent in nlp(place).ents)
        ]
        #If the user likes a certain city or location, get up to 3 random longitude and latitude for
        for city in places:
            if (city[-1] == 1):
                points = latLong_Agent(city[0])
                print(latLong_Agent("Italy"))
                # Country or location might be too small
                if len(points) == 0:
                    points = get_city_coords_from_geoapp(city[0])
            print(points)
                    #print(f"Random coordinates: Latitude={latitude}, Longitude={longitude}")
        
