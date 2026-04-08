

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import os
from pathlib import Path
import os
import requests
from pymongo import UpdateOne
from swarm import Swarm, Agent
from typing import List
import ast
from datetime import date
import datetime
import json
import asyncio
from bson.objectid import ObjectId
from bson.errors import InvalidId
from trip_Functions import  get_access_token, get_city_geocode, latLong_Agent
from travel_preference import analyze_text


# Load .env from project root (brochadia/.env)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
AMA_KEY = os.getenv("VITE_AMA_API_KEY")
AMA_SEC = os.getenv("VITE_AMA_API_SEC")

app = Flask(__name__)
CORS(app)
password = os.getenv('VITE_MONGO_PASSWORD')
print("Password:", password)
uri = 'mongodb+srv://azad:'+password+'@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster'

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
mongoDB = client["Brochadia"]
openAI_client = Swarm()
session = requests.Session()
experiences_collection = mongoDB["Experiences"]

def get_season(current_date=date.today()):
    """
    Determine the season based on the month and day.
    Uses meteorological seasons for the Northern Hemisphere.
    """
    
    if isinstance(current_date, str):
        year, month, day = current_date.split("-")
        month = int(current_date.split("-")[1])
        day = int(current_date.split("-")[2])
        
    else:    
        month = current_date.month
        day = current_date.day

    # Meteorological seasons:
    if (month == 12 and day >= 1) or month in (1, 2):
        return "Winter"
    elif (month == 3 and day >= 1) and (month < 6 or (month == 6 and day < 1)):
        return "Spring" if month >= 3 else "Winter"
    elif month in (3, 4, 5):
        return "Spring"
    elif month in (6, 7, 8):
        return "Summer"
    elif month in (9, 10, 11):
        return "Autumn"
    else:   
        return "Unknown"


# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    print("Databases:", client.list_database_names())
    print("Brochadia Database:", client.Brochadia.list_collection_names())
except Exception as e:
    print(e)


print("Today's Season", get_season())



@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        mongo_user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = client.Brochadia.users.find_one(
        {'_id': mongo_user_id},
        {'email': 1, 'full_name': 1, 'preferred_trip': 1, 'travel_preference': 1},
    )
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    return jsonify({
        'success': True,
        'user': {
            'userId': str(user['_id']),
            'email': user.get('email'),
            'full_name': user.get('full_name'),
            'preferred_trip': user.get('preferred_trip'),
            'travel_preference': user.get('travel_preference')
        },
    }), 200


def get_user_travel_preference(user_id):
    if not user_id:
        return None

    try:
        mongo_user_id = ObjectId(user_id)
    except InvalidId:
        return None

    user = client.Brochadia.users.find_one(
        {'_id': mongo_user_id},
        {'travel_preference': 1},
    )
    if not user:
        return None

    return user.get('travel_preference')

@app.route('/save_trip', methods=['POST'])
def save_Trip():
    data = request.get_json() or {}
    user_id = (data.get('userId') or '').strip()
    trip_doc = data.get('trip')

    if not user_id:
        return jsonify({'success': False, 'message': 'userId is required'}), 400

    if not isinstance(trip_doc, dict) or not trip_doc:
        return jsonify({'success': False, 'message': 'trip is required'}), 400

    try:
        mongo_user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = client.Brochadia.users.find_one({'_id': mongo_user_id}, {'_id': 1})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    trip_id = trip_doc.get('_id')
    temp_trips = client.Brochadia.Temp_Trips

    if trip_id:
        try:
            mongo_trip_id = ObjectId(trip_id)
        except InvalidId:
            mongo_trip_id = None

        if mongo_trip_id and temp_trips.find_one({'_id': mongo_trip_id}, {'_id': 1}):
            trip_id = str(mongo_trip_id)
        else:
            trip_insert_doc = dict(trip_doc)
            trip_insert_doc.pop('_id', None)
            insert_result = temp_trips.insert_one(trip_insert_doc)
            trip_id = str(insert_result.inserted_id)
    else:
        insert_result = temp_trips.insert_one(dict(trip_doc))
        trip_id = str(insert_result.inserted_id)

    update_result = client.Brochadia.users.update_one(
        {'_id': mongo_user_id},
        {'$addToSet': {'Saved_Trips_ID': trip_id}},
    )

    already_saved = update_result.modified_count == 0
    return jsonify({
        'success': True,
        'message': 'Trip already saved' if already_saved else 'Trip saved successfully',
        'tripId': trip_id,
        'alreadySaved': already_saved,
    }), 200

@app.route('/countries', methods=['GET'])
def get_countries():
    continent = request.args.get('continent')
    if not continent:
        return jsonify({'success': False, 'message': 'Provide ?continent=...'}), 400
    trips = client.Brochadia.Trips.find({'continent': continent})
    countries = trips.distinct('location')
    
    return jsonify({'success': True, 'continent': continent, 'countries': countries})

@app.route('/trip', methods=['GET'])
async def get_trip():
    occasion = request.args.get('trip_type')
    location = request.args.get('Country')
    user_id = (request.args.get('userId') or request.args.get('user') or '').strip()
    user_travel_preference = get_user_travel_preference(user_id)

    if not occasion or not location:
        return jsonify({'success': False, 'message': 'Provide trip_type and Country query params'}), 400

    cursor = client.Brochadia.Trips.find({'trip_type': occasion, 'location': location, 'experiences': {'$exists': True, '$ne': []}})
    trips = list(cursor)
    #print("TRIPS if they are empty", trips)
    if not trips:
        print("Calling OpenSwarm AI")
        season = get_season()
        ai_activities = []
        submitTrips = []
        try:
            coords = latLong_Agent(location)
            print("RESULTS FOR COORD", coords)
            if len(coords) != 1:
                coords = get_city_geocode(location, session)
            print("These are the Coords")
            if coords:
                access_token = get_access_token(session)
                session.headers.update({"Authorization": f"Bearer {access_token}"})
                lat, lon = coords
                raw_activities = get_activities(lat, lon)
                #print("Raw Activities",raw_activities)
                if isinstance(raw_activities, dict):
                    raw_activities = raw_activities.get("data") or []

                candidates = []
                for activity in raw_activities:
                    if not isinstance(activity, dict):
                        continue
                    candidates.append(
                        {
                            "id": activity.get("id"),
                            "name": activity.get("name"),
                            "shortDescription": activity.get("shortDescription"),
                            "price": activity.get("price"),
                            "price_USD": activity.get("price_USD"),
                            "pictures": activity.get("pictures"),
                        }
                    )
                    if len(candidates) >= 30:
                        break

                if candidates:
                    selector_agent = Agent(
                        name="Trip Activity Selector",
                        instructions=(
                            "You are a travel curator. From the provided activities list, select "
                            "the best matches for the requested trip_type. If a user travel_preference "
                            "dictionary is provided, use it to personalize the ranking toward liked "
                            "items(items that are Greater than 0) and away from disliked ones(items that are Less than 0) Based on the shortDescription feature of each activity in activites. Return ONLY "
                            "a JSON array of activity objects taken from the input list. Do not "
                            "add new fields or commentary."
                        ),
                        output_type="json",
                    )
                    print(json.dumps(user_travel_preference or {}))
                    response = openAI_client.run(
                        agent=selector_agent,
                        messages=[
                            {
                                "role": "user",
                                "content": (
                                    f"trip_type={occasion}, location={location}, season={season}, "
                                    f"user_id={user_id or 'anonymous'}, "
                                    f"user_travel_preference={json.dumps(user_travel_preference or {})}. "
                                    f"activities={candidates}"
                                ),
                            }
                        ],
                    )
                    content = None
                    if response and getattr(response, "messages", None):
                        content = response.messages[-1].get("content")
                        content = content.strip().removeprefix('json').removesuffix('').strip()
                        
                        
                    if content:
                        try:
                            print(content.split("```json")[-1].split("```")[0])
                            content = content.split("```json")[-1].split("```")[0]
                            ai_activities = json.loads(content)
                            #print("AI ACTIVITIES", ai_activities)
                        except Exception as e:
                            print("ERROR 1",e)
                            try:
                                ai_activities = ast.literal_eval(content)
                            except Exception as e:
                                print("ERROR 2",e)
                                ai_activities = []
                    #print("AI ACTIVITIES",ai_activities)
                if not ai_activities:
                    ai_activities = candidates
        except Exception as e:
            print(e)
            ai_activities = []
        print("test",type(ai_activities),ai_activities)
        if ai_activities:
            activity_ids = []
            total_usd = 0.0
            for i, activity in enumerate(ai_activities):
                print(i, activity.keys())
                if not isinstance(activity, dict):
                    continue
                activity_id = activity.get("id")
                if not activity_id:
                    continue

                if "price_USD" not in activity and activity['price_USD'] is not None:
                    price = activity.get("price") or {}
                    currency = (price.get("currencyCode") or "").upper()
                    if currency == "USD":
                        try:
                            activity["price_USD"] = float(price.get("amount"))
                        except (TypeError, ValueError):
                            pass

                try:
                    total_usd += float(activity.get("price_USD") or 0)
                except (TypeError, ValueError):
                    pass
                print("ADDING ACTIVITY", activity)
                experiences_collection.update_one(
                    {"id": activity_id},
                    {"$setOnInsert": activity},
                    upsert=True,
                )
                activity_ids.append(activity_id)
            trips = ai_activities

        # return jsonify({'success': False, 'message': 'No trip for that country and preference was found'}), 404

        print('Trips for', location, 'with trip_type', occasion, ':', trips)

    # Convert ObjectId to string so JSON serialization works
    
    for trip in trips:
        experience_ids = trip.get("experiences") or []
        query = {"id": {"$in": experience_ids}}
        activities = list(
            experiences_collection.find(
                query, {"_id": 0, "id": 1, "name": 1, "price_USD": 1, "pictures": 1}
            )
        )

        total_usd = 0.0
        for act in activities:
            try:
                total_usd += float(act.get("price_USD") or 0)
            except (TypeError, ValueError):
                pass

        if "_id" in trip:
            trip["_id"] = str(trip["_id"])

        trip_payload = dict(trip)
        trip_payload["activities"] = activities
        trip_payload["activities_total_usd"] = round(total_usd, 2)
        submitTrips.append(trip_payload)
    print(submitTrips)
    return jsonify({"success": True, "trips": submitTrips})


def get_activities(lat: float, lon: float):
    url = "https://test.api.amadeus.com/v1/shopping/activities"
    response = session.get(url, params={"latitude": lat, "longitude": lon, "radius": 1})
    if response.status_code == 429 or response.status_code == 404:
        return {
  "meta": {
    "count": "4",
    "links": {
      "self": "https://test.api.amadeus.com/v1/shopping/activities?longitude=149.1300&latitude=-35.2809&radius=5"
    }
  },
  "data": [
    {
      "id": "1001",
      "type": "activity",
      "self": {
        "href": "https://test.api.amadeus.com/v1/shopping/activities/1001",
        "methods": [
          "GET"
        ]
      },
      "name": "Guided E-Bike Tour of Lake Burley Griffin",
      "shortDescription": "Enjoy a scenic ride around Lake Burley Griffin on an e-bike, taking in the beautiful waterfront views and the city's meticulously planned landscape.",
      "geoCode": {
        "latitude": "-35.287500",
        "longitude": "149.128400"
      },
      "rating": "4.800000",
      "pictures": [
        "https://example.com/images/lake-burley-griffin-ebike.jpg"
      ],
      "bookingLink": "https://b2c.mla.cloud/c/QCejqyor?c=bike123",
      "price": {
        "currencyCode": "AUD",
        "amount": "85.00"
      }
    },
    {
      "id": "1002",
      "type": "activity",
      "self": {
        "href": "https://test.api.amadeus.com/v1/shopping/activities/1002",
        "methods": [
          "GET"
        ]
      },
      "name": "Canberra Geometric Urban Planning Walk",
      "shortDescription": "Discover the vision of Walter Burley Griffin on this architectural walking tour. Explore the precise geometry and design principles that shaped Australia's capital.",
      "geoCode": {
        "latitude": "-35.282000",
        "longitude": "149.128600"
      },
      "rating": "4.600000",
      "pictures": [
        "https://example.com/images/canberra-urban-planning.jpg"
      ],
      "bookingLink": "https://b2c.mla.cloud/c/QCejqyor?c=walk456",
      "price": {
        "currencyCode": "AUD",
        "amount": "45.00"
      }
    },
    {
      "id": "1003",
      "type": "activity",
      "self": {
        "href": "https://test.api.amadeus.com/v1/shopping/activities/1003",
        "methods": [
          "GET"
        ]
      },
      "name": "Parliament House Architectural Masterclass",
      "shortDescription": "Go beyond the standard tour with an architect-led walkthrough of the grand Parliament House, exploring its monumental design and structural significance.",
      "geoCode": {
        "latitude": "-35.308200",
        "longitude": "149.124400"
      },
      "rating": "4.900000",
      "pictures": [
        "https://example.com/images/parliament-house-tour.jpg"
      ],
      "bookingLink": "https://b2c.mla.cloud/c/QCejqyor?c=parl789",
      "price": {
        "currencyCode": "AUD",
        "amount": "120.00"
      }
    },
    {
      "id": "1004",
      "type": "activity",
      "self": {
        "href": "https://test.api.amadeus.com/v1/shopping/activities/1004",
        "methods": [
          "GET"
        ]
      },
      "name": "Sunrise Hot Air Balloon Flight",
      "shortDescription": "Experience the ultimate view of Canberra's symmetrical layout and the tranquil Lake Burley Griffin from above during a breathtaking sunrise balloon flight.",
      "geoCode": {
        "latitude": "-35.295000",
        "longitude": "149.125000"
      },
      "rating": "5.000000",
      "pictures": [
        "https://example.com/images/canberra-balloon.jpg"
      ],
      "bookingLink": "https://b2c.mla.cloud/c/QCejqyor?c=ball000",
      "price": {
        "currencyCode": "AUD",
        "amount": "350.00"
      }
    }
  ]
}
    if response.status_code != 200:
        return []
    return response.json().get("data") or []


async def async_get_access_token(session: requests.Session) -> str:
    return await asyncio.to_thread(get_access_token, session)


async def async_get_city_geocode(city: str, session: requests.Session):
    return await asyncio.to_thread(get_city_geocode, city, session)


async def async_get_activities(lat: float, lon: float):
    return await asyncio.to_thread(get_activities, lat, lon)


@app.route('/ai_response', methods=['POST'])
async def ai_response():
    data = request.get_json() or {}
    preferredTrip = data.get("preferredTrip")
    location = data.get("location")
    season = data.get("season")
    return await travel_agent_async(preferredTrip, location, season)


async def travel_agent_async(preferredTrip, location, season):
    print("Calling AI Agent 2")
    if not location:
        print("ERROR For location")
        return jsonify({"success": False, "message": "Missing location"}), 400

    try:
        access_token = await async_get_access_token(session)
    except Exception:
        print("ERROR For Token")

        return jsonify({"success": False, "message": "Failed to get access token"}), 502

    session.headers.update({"Authorization": f"Bearer {access_token}"})

    coords = await async_get_city_geocode(location, session)
    if not coords:
        print("ERROR For coordinates")

        return jsonify({"success": False, "message": "Could not geocode location"}), 404

    lat, lon = coords
    activities = await async_get_activities(lat, lon)
    
    if not activities:
        print("ERROR getting activities")
        return jsonify({"success": False, "message": "No activities found"}), 404

    return jsonify(
        {
            "success": True,
            "preferredTrip": preferredTrip,
            "location": location,
            "season": season,
            "coords": {"lat": lat, "lon": lon},
            "activities": activities,
        }
    )

    



print("Today's Season", get_season())


@app.route('/signup', methods=['POST'])
async def signup():
    data = request.get_json() or {}
    full_name = (data.get('full_name') or '').strip()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    preferred_trip = (data.get('preferred_trip') or '').strip()
    trip_continent = (data.get('trip_continent') or '').strip()
    trip_country = (data.get('trip_country') or '').strip()
    trip_season = get_season((data.get('trip_date') or '').strip())
    trip_details = (data.get('trip_details') or '').strip()
    travel_party_size = data.get('travel_party_size')
    trip_budget = data.get('trip_budget')

    required_fields = {
        'full_name': full_name,
        'email': email,
        'password': password,
        'preferred_trip': preferred_trip,
        'trip_continent': trip_continent,
        'trip_country': trip_country,
        'trip_season': trip_season,
        'travel_party_size': travel_party_size,
        'trip_budget': trip_budget,
    }

    missing_fields = [field for field, value in required_fields.items() if value in (None, '')]
    if missing_fields:
        return jsonify({
            'success': False,
            'message': f"Missing required fields: {', '.join(missing_fields)}",
        }), 400

    valid_trip_types = {'Leisure', 'Cultural', 'Honeymoon', 'Adventure', 'Business'}
    if preferred_trip not in valid_trip_types:
        return jsonify({'success': False, 'message': 'Invalid preferred_trip value'}), 400

    try:
        travel_party_size = int(travel_party_size)
        if travel_party_size < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'travel_party_size must be a positive integer'}), 400

    try:
        trip_budget = float(trip_budget)
        if trip_budget < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'trip_budget must be a valid non-negative number'}), 400

    user = client.Brochadia.users.find_one({'email': email})

    if user:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400

    trip_history = {
        'continent': trip_continent,
        'country': trip_country,
        'travel_party_size': travel_party_size,
        'trip_season': trip_season,
        'budget_usd': round(trip_budget, 2),
    }
    travel_preference = {}
    location_preference = {}

    if trip_details:
        trip_history['details'] = trip_details
        travel_preference, location_preference = analyze_text(trip_details)
        trip_history['travel_preference'] = travel_preference

    new_user = {
        'full_name': full_name,
        'email': email,
        'password': password,
        'preferred_trip': preferred_trip,
        'trip_history': [trip_history],
        'travel_preference': travel_preference,
        'location_preference': location_preference,
    }

    result = client.Brochadia.users.insert_one(new_user)
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'userId': str(result.inserted_id),
    }), 201

@app.route('/login', methods=['POST'])
def login(client: MongoClient):
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    user = client.Brochadia.users.find_one({'email': email})
    if not user or user.get('password') != password:
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

    return jsonify({
        'success': True,
        'message': 'Logged in successfully',
        'email': email,
        'userId': str(user['_id']),
    }), 200



async def travel_agent(preferredTrip, location, season):
    variable1 = await travel_agent_async(preferredTrip, location, season)
    print(variable1)
    return variable1



if __name__ == '__main__':
    app.run(debug=True)
