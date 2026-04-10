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
            "You are a travel curator. pick at most 3 random longitude and latitude pairs "
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
