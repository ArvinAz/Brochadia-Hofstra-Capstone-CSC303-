from calendar import c
from math import fabs
from dotenv import load_dotenv
from pathlib import Path
import os
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import UpdateOne
from swarm import Swarm, Agent
from typing import List
import ast

import asyncio
import geopy
from geopy.geocoders import Nominatim




# Load .env from project root (brochadia/.env)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
AMA_KEY = os.getenv("VITE_AMA_API_KEY")
AMA_SEC = os.getenv("VITE_AMA_API_SEC")

client = Swarm()

uri = f"mongodb+srv://azad:{MONGO_PASSWORD}@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster"
clientdb = MongoClient(uri, server_api=ServerApi('1'))
db = clientdb["Brochadia"]
trips_collection = db["Trips"]
experiences_collection = db["Experiences"]

session = requests.Session()
sugg_activities = None
app = Nominatim(user_agent="tutorial")




#Agent for looking at Lists


def get_access_token() -> str:
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


# This will be used later on for
def get_city_geocode(city: str):
    url = "https://test.api.amadeus.com/v1/reference-data/locations/cities"
    response = session.get(url, params={"keyword": city})
    if response.status_code != 200:
        return None
    data = response.json().get("data") or []
    if not data:
        return None
    geo = data[0].get("geoCode") or {}
    lat = geo.get("latitude")
    lon = geo.get("longitude")
    if lat is None or lon is None:
        return None
    return lat, lon


def get_city_geocode(city: str):
    try:
        location = app.geocode(city)
    except Exception:
        return None

    if not location:
        return None

    return location.latitude, location.longitude


def get_activities(lat: float, lon: float):
    url = "https://test.api.amadeus.com/v1/shopping/activities"
    response = session.get(url, params={"latitude": lat, "longitude": lon, "radius": 1})
    if response.status_code == 429:
        return {"data":[
            {
                "id": "dummy-activity-1",
                "name": "Dummy Activity 1",
                "shortDescription": "Leisure, Cultural, Honeymoon",
                "price": {"currencyCode": "USD", "amount": "1000"},
                "price_USD": 1000,
            },
            {
                "id": "dummy-activity-2",
                "name": "Dummy Activity 2",
                "shortDescription": " Backpacking, Business, Honeymoon",
                "price": {"currencyCode": "USD", "amount": "1000"},
                "price_USD": 1000,
            },
            {
                "id": "dummy-activity-3",
                "name": "Dummy Activity 3",
                "shortDescription": "Leisure, Backpacking, Culture",
                "price": {"currencyCode": "USD", "amount": "1000"},
                "price_USD": 1000,
            },
                        {
                "id": "dummy-activity-4",
                "name": "Dummy Activity 4",
                "shortDescription": "Leisure, Cultural, Honeymoon, Business, Backpacking",
                "price": {"currencyCode": "USD", "amount": "1000"},
                "price_USD": 100,
            },
        ]}
    if response.status_code != 200:
        return []
    return response.json().get("data") or []


'''
def check_budget(activities, budget):
                if estimated_cost > budget:
                del_price = min(price_activities)
                # TODO: Remove the activity in posts['data'] that has the lowest USD value in side of the price feature.
                if not on_budget:
                    price_removed = min(posts["data"], key=lambda x:x['price']['USD'])
                else:
                    price_removed = max(posts["data"], key=lambda x:x['price']['USD'])
                posts["data"].remove(price_removed)
'''



def fill_missing_experiences():
    access_token = get_access_token()
    session.headers.update({"Authorization": f"Bearer {access_token}"})

    missing_query = {
        "$or": [
            {"experiences": {"$exists": False}},
            {"experiences": {}},
            {"experiences": {"$size": 0}},
        ]
    }

    trips_by_group = {}
    cursor = trips_collection.find(
        missing_query,
        {"location": 1, "trip_type": 1, "season": 1, "budget_usd": 1},
    )
    for trip in cursor:
        location = trip.get("location")
        if not location:
            continue
        trip_type = trip.get("trip_type")
        season = trip.get("season")
        group_key = (location, trip_type, season)
        trips_by_group.setdefault(group_key, []).append(
            {"_id": trip["_id"], "budget_usd": trip.get("budget_usd")}
        )
    
    # Sort Each trip by Most to least budget
    for trips in trips_by_group.values():
        # Sort the list in place
        trips.sort(
            # Use budget_usd for sorting; if it's None, treat it as negative infinity
            key=lambda x: x.get("budget_usd") if x.get("budget_usd") is not None else float('-inf'), 
            reverse=True # Descending order
        )

    trip_ops = []
    


    try:
        for (location, _trip_type, _season), trip_docs in trips_by_group.items():
            coords = get_city_geocode(location)
            on_budget = False
            if _trip_type == "Backpacking":
                on_budget = True
            
            if not coords:
                continue
            lat, lon = coords

            trip_docs.sort(
                key=lambda t: (t.get("budget_usd") is None, -(t.get("budget_usd") or 0))
            )
            if not trip_docs:
                continue

            global sugg_activities
            sugg_activities = get_activities(lat, lon)
            print(sugg_activities)
            if (
                not sugg_activities
                or (
                    isinstance(sugg_activities, dict)
                    and not (sugg_activities.get("data") or [])
                )
            ):
                print("no activities")
                continue

            #TODO: Have Swarm read each Activities short Description for the most expensive Trip
            response = client.run(
                agent=classifier_agent,
                messages=[{
                    "role": "user", 
                    "content": f"Here is the raw data: {sugg_activities}. Please filter for a {_season} {_trip_type} trip on a {trip_docs[0]['budget_usd']} budget."
                }]
            )
            #TODO: Get rid of all cheap Trips if the trip type isn't Backpacking

            activities = ast.literal_eval(response.messages[1]['content'])
            print(type(activities),activities)

            # Insert Activities found in Experiences Collection
            activity_ids = []
            for activity in activities:
                print(activity)
                print(type(activity))
                activity_id = activity.get("id")
                if not activity_id:
                    continue
                activity_ids.append(activity_id)
                print("First",activity_id)
                experiences_collection.update_one(
                    {"id": activity_id},
                    {"$setOnInsert": activity},
                    upsert=True,
                )

            if not activity_ids:
                continue

            for i, trip_doc in enumerate(trip_docs):
                activity_ids = cutActivities(activities, _trip_type, trip_doc['budget_usd'])
                print(i, activity_ids)
                trip_ops.append(
                    UpdateOne({"_id": trip_doc["_id"]}, {"$set": {"experiences": activity_ids}})
                )

        if trip_ops:
            trips_collection.bulk_write(trip_ops, ordered=False)
    except Exception:
        print("ERROR")
        if trip_ops:
            trips_collection.bulk_write(trip_ops, ordered=False)
        return


def cutActivities(activities, trip_type, budget):
    """Return only activity IDs (strings) suitable for trip.experiences — not full objects."""

    def _ids(acts):
        return [a["id"] for a in acts if a.get("id")]

    # First sort trips first
    reverse = trip_type == "Backpacking"
    missing_val = float("-inf") if reverse else float("inf")

    def _price_usd(activity):
        val = activity.get("price_USD")
        try:
            return float(val)
        except (TypeError, ValueError):
            return missing_val

    activities.sort(key=_price_usd, reverse=reverse)

    activity_sum = sum(
        float(a.get("price_USD") or 0) for a in activities
    )

    if activity_sum <= budget or budget is None:
        return _ids(activities)

    current_sum = 0
    for end in range(len(activities)):
        current_sum += float(activities[end].get("price_USD") or 0)

        if activity_sum - current_sum <= budget:
            return _ids(activities[end + 1 :])

    return _ids(activities)

# Used to search which activities
def suggestActivities(filtered_activities: list[dict], trip_type, season, budget):
    print(f"\n--- Saving Recommendations for {season} {trip_type} ({budget}) ---")

    exchange_rates = {
        "USD": 1.00,
        "EUR": 1.09,
        "GBP": 1.28,
        "JPY": 0.0067,
        "CAD": 0.74,
    }
    #actual_python_list = json.loads(filtered_activities)
    
    # Now it is a real Python list! (<class 'list'>)
    filtered_activities = ast.literal_eval(filtered_activities)
    print(type(filtered_activities))
    print("FILTERED ACTIVITIES", filtered_activities, len(filtered_activities))
    for act in filtered_activities:
        print(type(act))
        price = act.get("price") or {}
        currency = price.get("currencyCode", "USD").upper()
        amount_str = price.get("amount")
        try:
            amount = float(amount_str)
        except (TypeError, ValueError):
            amount = None
        if amount is not None:
            rate = exchange_rates.get(currency)
            if rate is not None:
                act["price_USD"] = round(amount * rate, 2)
        # Assuming the AI passes back a list of dictionaries with a 'name' key
        print(f"✅ Approved: {act.get('name', 'Unknown Activity')}")
        
    # In a real app, you'd save this to a database or return it to your frontend here.
    
    return filtered_activities


classifier_agent = Agent(
        name="Travel Classifier",
        instructions="""You are an elite travel consultant. 
    The user will provide a list of activities, along with a target trip_type, season, and budget.
    Read the `shortDescription` of each activity. 
    Filter all the values of the activities in Python object format that strongly match the requested trip_type and season.
    Once you have your filtered list, call the `suggestActivities` tool to save your final recommendations.""",
        functions=[suggestActivities],
    )

if __name__ == "__main__":
    fill_missing_experiences()
