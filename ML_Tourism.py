import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path
import os
dataset = pd.read_csv('tourism_with_continent.csv')
#print(dataset.head())


load_dotenv(Path(__file__).resolve().parent.parent / '.env')

app = Flask(__name__)
CORS(app)
password = os.getenv('VITE_MONGO_PASSWORD')
print("Password:", password)
uri = 'mongodb+srv://azad:'+password+'@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster'
print(uri)
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection

# Adding data from tourism_with_continent.csv to trip database if they already exist
dataset_path = Path(__file__).resolve().parents[2] / 'tourism_with_continent.csv'
dataset = pd.read_csv(dataset_path)

# Handle honeymoon trips where the group size is one.
dataset = dataset[(dataset['group_size'] != 1) & (dataset['trip_type'] != 'Honeymoon')]

for index, row in dataset.iterrows():
    if client.Brochadia.Trips.find_one({'user_id': row['user_id']}):        
        continue
    client.Brochadia.Trips.insert_one({
        'id': index,
        'user_id': row['user_id'],
        'location': row['location'],
        'continent': row['continent'],
        'trip_type': row['trip_type'],
        'group_size': row['group_size'],
        'season': row['season'],
        'budget_usd': round(row['budget_usd'], 2),
        'experiences': {}
    })


#print(dataset[(dataset['trip_type'] == 'Honeymoon') & (dataset['group_size'] == 1)].count() / dataset[(dataset['trip_type'] == 'Honeymoon')].count())


# There is an error where The group count for Honeymoon Trips are set to 1 which doesnt make sense in the context
# Of a honeymoon

dataset = dataset[(dataset['group_size'] != 1) & (dataset['trip_type'] != 'Honeymoon')]
print(dataset[(dataset['trip_type'] == 'Honeymoon') & (dataset['group_size'] == 1)].count() / dataset[(dataset['trip_type'] == 'Honeymoon')].count())
print(dataset)

