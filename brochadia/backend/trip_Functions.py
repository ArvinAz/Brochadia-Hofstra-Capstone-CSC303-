from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import importlib.util
import pandas as pd
import os
import requests
import geopy
from geopy.geocoders import Nominatim
from swarm import Swarm, Agent
import json
import ast
import geopandas as gpd
import random
from shapely.geometry import Point



load_dotenv(Path(__file__).resolve().parent.parent / '.env')
openAI_client = Swarm()
MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
AMA_KEY = os.getenv("VITE_AMA_API_KEY")
AMA_SEC = os.getenv("VITE_AMA_API_SEC")


geoApp = Nominatim(user_agent="tutorial")
USD_EXCHANGE_RATES = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("1.09"),
    "GBP": Decimal("1.28"),
    "AUD": Decimal("0.66"),
    "CAD": Decimal("0.74"),
    "JPY": Decimal("0.0067"),
    "CNY": Decimal("0.14"),
    "INR": Decimal("0.012"),
    "MXN": Decimal("0.059"),
    "BRL": Decimal("0.20"),
    "CHF": Decimal("1.11"),
    "NZD": Decimal("0.61"),
}

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


def extract_experiences(mongo_doc):
    """
    Extracts the 'experiences' feature from a MongoDB document and converts 
    a stringified list of numbers into an actual Python list of numbers.
    
    Args:
        mongo_doc (dict or object): The MongoDB document instance.
        
    Returns:
        list: A Python list of numbers (ints or floats). Returns an empty list if missing or invalid.
    """
    # 1. Safely extract the feature whether the doc is a dictionary or an object
    if isinstance(mongo_doc, dict):
        
        experiences_str = mongo_doc.get("experiences")
        
    else:
        experiences_str = getattr(mongo_doc, "experiences", None)
        
    # Check if the feature exists and is actually a string
    return experiences_str
    if not experiences_str or not isinstance(experiences_str, str):
        return []

    # 2. Try to safely evaluate strings that are formatted as Python/JSON lists (e.g., "[1, 2, 3]")
    try:
        parsed_data = ast.literal_eval(experiences_str)
        
        # Make sure the evaluated data is a list
        if isinstance(parsed_data, list):
            return parsed_data
        elif isinstance(parsed_data, (int, float)): 
            # In case the string was just a single number like "1"
            return [parsed_data]
            
    except (ValueError, SyntaxError):
        # If ast.literal_eval fails, pass and move to the manual fallback
        pass

    # 3. Fallback: Manually parse strings that are just comma-separated (e.g., "1, 2.5, 3")
    try:
        # Strip any extraneous brackets just in case
        cleaned_str = experiences_str.strip("[]")
        
        if not cleaned_str.strip():
            return []
            
        result_list = []
        for val in cleaned_str.split(','):
            val = val.strip()
            # Convert to float if it has a decimal, otherwise int
            if '.' in val:
                result_list.append(float(val))
            else:
                result_list.append(int(val))
                
        return experiences_str
        
    except ValueError:
        # If all conversions fail (e.g., the string contains letters), return an empty list
        return []

#For Existing Trips


def get_random_coordinates(country_name, num_points=3):
    """
    Generates random (latitude, longitude) pairs within a specified country.
    """
    # 1. Load the built-in low-resolution world map from geopandas
    # Note: Depending on your geopandas version, you may see a deprecation warning 
    # for get_path, but it remains the standard built-in dataset for this purpose.
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)

    # 2. Filter the dataset for the requested country
    country_data = world[world['NAME'] == country_name]

    if country_data.empty:
        raise ValueError(f"Country '{country_name}' not found. Please check your spelling (e.g., 'United States of America' instead of 'USA').")

    # 3. Extract the geometry (Polygon or MultiPolygon) for the country
    country_geom = country_data.geometry.iloc[0]

    # 4. Get the bounding box coordinates of the country (min_lon, min_lat, max_lon, max_lat)
    minx, miny, maxx, maxy = country_geom.bounds

    valid_points = []
    
    print(f"Generating {num_points} points inside {country_name}...")

    # 5. Loop until we find the requested number of valid points
    while len(valid_points) < num_points:
        # Generate a random longitude (x) and latitude (y) within the bounding box
        random_lon = random.uniform(minx, maxx)
        random_lat = random.uniform(miny, maxy)
        
        # Create a Shapely Point object
        point = Point(random_lon, random_lat)

        # 6. Check if the randomly generated point is actually inside the country's borders
        if country_geom.contains(point):
            # Append as (Latitude, Longitude)
            valid_points.append((random_lat, random_lon))

    return valid_points



def single_userPref_score(user_dict, trip_activity, feature_name="shortDescription"):
    """
    Calculates a total score based on the occurrence of dictionary words within 
    a single trip object.
    
    Args:
        user_dict (dict): A dictionary where keys are words and values are ints (-1 to 1).
        trip_activity (dict/obj): A single object containing the string feature.
        feature_name (str): The attribute or key name to check.
        
    Returns:
        int: The total calculated score for this single object.
    """
    total_score = 0
    
    # 1. Extract the string feature from the single object
    if isinstance(trip_activity, dict):
        text = trip_activity.get(feature_name, "")
    else:
        text = getattr(trip_activity, feature_name, "")
        
    # 2. Ensure the feature is a string before processing
    if not isinstance(text, str):
        return 0
        
    # 3. Process the text and calculate score
    words = text.lower().split()
    for word in words:
        # Strip basic punctuation
        clean_word = word.strip(".,!?\"'()[]{}")
        
        # Add value to total if word exists in user preference dictionary
        if clean_word in user_dict:
            total_score += user_dict[clean_word]
    
    return total_score

def calculate_userPref_score(user_dict, trip_Activities, feature_name="text"):
    """
    Calculates a total score based on the occurrence of dictionary words within a list of objects.
    
    Args:
        word_dict (dict): A dictionary where keys are words and values are ints (-1 to 1).
        objects_list (list): A list of objects (or dictionaries) containing the string feature.
        feature_name (str): The name of the attribute or key that holds the string feature.
        
    Returns:
        int: The total calculated score.
    """
    total_score = 0
    for obj in trip_Activities:
        # Extract the string feature whether the object is a dictionary or a class instance
        print(obj.get("shortDescription", ""))
        if isinstance(obj, dict):
            text = obj.get("shortDescription", "")
        else:
            text = getattr(obj, "shortDescription", "")
            
        # Ensure the feature is actually a string before processing
        if not isinstance(text, str):
            continue
            
        # Split the text into words and convert to lowercase for uniform matching
        words = text.lower().split()
        for word in words:
            # Strip basic punctuation to ensure "word," or "word!" matches "word" in the dict
            clean_word = word.strip(".,!?\"'()[]{}")
            
            # If the cleaned word is in our dictionary, add its value to the total score
            
            
            if clean_word in user_dict:
                total_score += user_dict[clean_word]
    
    return total_score



def _get_usd_exchange_rate(currency_code: str):
    currency = (currency_code or "").strip().upper()
    if not currency:
        return None

    return USD_EXCHANGE_RATES.get(currency)


def convert_price_to_usd(price: dict):
    """
    Convert a price object like {"currencyCode": "EUR", "amount": "16.00"}
    into the same shape in USD using in-house exchange rates.
    """
    if not isinstance(price, dict):
        return None

    currency = (price.get("currencyCode") or "").strip().upper()
    amount = price.get("amount")
    if not currency or amount is None:
        return None

    try:
        source_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return None

    usd_rate = _get_usd_exchange_rate(currency)
    if usd_rate is None:
        return None

    usd_amount = (source_amount * usd_rate).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    print("Currency in USD", round(float(usd_amount),2))
    return round(float(usd_amount),2)


# Lat Long Agent to find random latitude and longitude pairs to make more travel 
def latLong_Agent(country):
    print("Calling agent for", country)
    selector_agent = Agent(
    name="Country Location Selector",
    instructions=(
            "You are a travel curator. pick  3 random longitude and latitude pairs "
            "that is within the location_input variable, whether its a country, city, Lake, or Mountain Range. Return ONLY "
            "a JSON array of subarrays of each pairs taken from the input string with float data type. Each subarray must have"
            "first element be the latitude and the second one being longitude."
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
    print(type(content))
    return json.loads(content)
