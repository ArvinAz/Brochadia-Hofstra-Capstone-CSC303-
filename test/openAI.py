from swarm import Swarm, Agent
from dotenv import load_dotenv
from pathlib import Path
import pandas as pd
import os
from geopy.geocoders import Nominatim
import time
import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path
from typing import List
import json



# Load .env from project root (brochadia/.env)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

client = Swarm()

uri = "mongodb+srv://azad:pOfXLo5WBVp8JSuS@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster"
# Create a new client and connect to the server
clientdb = MongoClient(uri, server_api=ServerApi('1'))
db = clientdb["Brochadia"]


cheap_trip = True

# Data Related to User's Preference
cust_budget = 2000
occasion = "Leisure"
c_user_id = 9000
season = "Spring"
duration = 3
group_size = 1
trip_id = 1201

sec_data = {

  "grant_type": 'client_credentials',
  "client_id": os.getenv('VITE_AMA_API_KEY'),
  "client_secret": os.getenv('VITE_AMA_API_SEC')
}

url_sec = f"https://test.api.amadeus.com/v1/security/oauth2/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
response = requests.post(url_sec, data=sec_data, )
if response.status_code == 200:
    posts = response.json()
    access_token = posts['access_token']
else:
    print('Error:', response.status_code)
    



def coordinate_agent(city):
    #print("search for location",city)
    url = f'https://test.api.amadeus.com/v1/reference-data/locations/cities'
    #print("Access Token: ", access_token)
    headers = {"Authorization": "Bearer "+access_token}
    payload = {'keyword': city}
    response = requests.get(url, headers=headers, params=payload )
    
    if response.status_code == 200:
        #print("DA answer is found")
        ans = response.json()
        #print(ans['data'][0]['geoCode'])
        return ans['data'][0]['geoCode']
        

def db_agent(activities: List[dict], trip_id):
    print("GO DB AGENT")
    ex_Collection = db["Experiences"]
    tr_Collection = db['Trips']
    # --- ADD THIS CHECK ---
    # If the LLM still passes a string, parse it into a Python list
    if isinstance(activities, str):
        try:
            activities = json.loads(activities)
        except json.JSONDecodeError:
            return "Error: Could not parse the activities string into a list."

    #Insert Activities by the trip ID
    trip_act_id = []
    for activity in activities:
        print(activity['id'])
        trip_act_id.append(activity['id'])
        
        activity_id = activity.get("id")
        if activity_id is None:
            continue

        if ex_Collection.find_one({"id": activity_id}) is None:
            ex_Collection.insert_one(activity)
    
    # Add Activity ID's of each
    print("Final ACtivity Lists", trip_act_id)
    trip_doc = {
        "id": trip_id,
        "user_id": c_user_id,
        "location":"Reykjavik",
        "continent":"Europe",
        "trip_type": occasion, 
        "group_size": 1,
        "budget_usd": cust_budget,
        "experiences": trip_act_id
    }
    tr_Collection.insert_one(trip_doc)
#def n_activity(long, lat):
    # Help find the nearest Activity

def convert_prices_to_usd(activities):
    """
    Converts the price attribute of each activity to USD.
    """
    # Hardcoded conversion rates to USD (1 unit of currency = X USD)
    # Note: These fluctuate, so update them or use an API for production.
    exchange_rates = {
        'EUR': 1.09,  # Euro
        'GBP': 1.28,  # British Pound
        'JPY': 0.0067, # Japanese Yen
        'CAD': 0.74,  # Canadian Dollar
        'USD': 1.00   # US Dollar (Base)
    }

    for activity in activities:
        act_price = activity['price']
        #print("DUM",act_price)
        currency = act_price.get('currencyCode', 'USD').upper()
        price = act_price.get('amount', 0.0)
        price = float(price)
        #print(act_price)
        #print("DUM",currency, price)
        if currency == 'USD':
            continue  # Already in USD
            
        if currency in exchange_rates:
            # Convert to USD and round to 2 decimal places
            usd_price = price * exchange_rates[currency]
            #print("Price",price , exchange_rates[currency])
            act_price['USD'] = round(usd_price, 2)
            #print(act_price)

        else:
            print(f"Warning: Exchange rate for {currency} not found. Skipping '{activity.get('name')}'.")

    return activities



def activity_agent(long, lat, curr_budget=cust_budget, on_budget:bool = False):
    print(long, lat, curr_budget, on_budget)

    
    # Define the API endpoint URL
    url = f'https://test.api.amadeus.com/v1/shopping/activities'
    headers = {"Content-Type": "application/json",
            "Authorization": "Bearer "+access_token}
    payload = {'longitude': long,
                'latitude': lat,
                'radius': 1}
    print("Testing URL")
    try:
        # Make a GET request to the API endpoint using requests.get()
        response = requests.get(url, params=payload, headers=headers )
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            posts = response.json()
            #print(posts['data'][0])
            posts['data'] = convert_prices_to_usd(posts['data'])
            #print("Currency converted!",activities)

            if on_budget:
                def _usd_price(activity):
                    price = activity.get("price") or {}
                    val = price.get("USD", price.get("amount"))
                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        return float("inf")

                posts["data"].sort(key=_usd_price)
            
            #TODO: 
            price_activities = [activity['price']['USD'] for activity in posts["data"]]
            total_Cost_usd = sum(price_activities)

            # Get rid of
            if total_Cost_usd > curr_budget:
                del_price = min(price_activities)
                # TODO: Remove the activity in posts['data'] that has the lowest USD value in side of the price feature.
                if not on_budget:
                    price_removed = min(posts["data"], key=lambda x:x['price']['USD'])
                else:
                    price_removed = max(posts["data"], key=lambda x:x['price']['USD'])
                posts["data"].remove(price_removed)

            
            
            # TODO: Override the previous TODO if the user's budget is limited
            # Country 1:
            return posts
        else:
            print('Error:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
  
        # Handle any network-related errors or exceptions
        print('Error:', e)
        return None

def transfer_to_coord_agent():
    """Transfers control to the Weather Agent."""
    return agent_b

def transfer_to_activity_agent():

    return agent_c



agent_a = Agent(
    name="Agent A",
    instructions="You are the main Agent in control of smaller agents. When User Requests a location's latitude and longitude, transfer query to coordinate_agent.",
    functions=[transfer_to_coord_agent],
)

agent_b = Agent(
    name="Agent b",
    instructions="You are the coordinate Agent. When User Requests a location's latitude and longitude, get the exact coordinates of that country using the  coordinate_agent function. If the query also requests activities then also transfer the coordinates you found from the coordinate_agent to agent c. NOTE: Don't Give the coordinates of the country that the location is in. (example: Get Coordinates of Paris over France)",
    functions = [coordinate_agent, transfer_to_activity_agent]
)

agent_c = Agent(
    name="Agent c",
    instructions=f"You are the activity Agent. Use the longitude and latitude given to you to call the API and get the json file related to it. After that, read each the shortDescription of each activity and pick which activities would be best fit for {occasion}. {"Set the on_budget on activity_agent to be True or 1 " if cheap_trip else "" }Then take the exact output of the activity agent you chose and insert them into the DB Agent function for them to inserted to MongoDB for Future reference.",
    functions = [activity_agent, db_agent],
    output_type="json"
)


messages = [{"role": "user", "content": "What's the longitude and latitude for Paris and what activities I can go to on Paris?"}]


response = client.run(
    agent=agent_a,
    messages=[{"role": "user", "content": "What's the longitude and latitude for Reykjavik? And what activities at Reykjavik can I do."}],
)

#activity_agent(2.160873, 41.397158)


print(response.messages[-1]["content"])