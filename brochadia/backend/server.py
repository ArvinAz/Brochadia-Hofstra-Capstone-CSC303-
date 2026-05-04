
import random
from pdf_funcs import create_Resume, modify_resume as rebuild_resume_pdf
from flask import Flask, request, jsonify, send_file
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
from trip_Functions import get_access_token, get_city_geocode, latLong_Agent, convert_price_to_usd, extract_experiences, calculate_userPref_score, single_userPref_score, get_random_coordinates
from travel_preference import analyze_text

from multiprocessing.connection import Client
import gridfs.errors
import bson.errors


import os
import gridfs
from pymongo import MongoClient
from pdf2image import convert_from_bytes
import hashlib
from pymongo.server_api import ServerApi
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from flask import Flask, request, jsonify
from bson.objectid import ObjectId

# Load .env from project root (brochadia/.env)
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

MONGO_PASSWORD = os.getenv("VITE_MONGO_PASSWORD")
AMA_KEY = os.getenv("VITE_AMA_API_KEY")
AMA_SEC = os.getenv("VITE_AMA_API_SEC")

app = Flask(__name__)
CORS(app)
password = os.getenv('VITE_MONGO_PASSWORD')
uri = 'mongodb+srv://azad:'+password+'@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster'

# Create a new client and connect to the server
client = MongoClient(password, server_api=ServerApi('1'))
mongoDB = client["Brochadia"]
openAI_client = Swarm()
session = requests.Session()
access_token = get_access_token(session)
experiences_collection = mongoDB["Experiences"]

# Path to save File
save_name = os.path.join(os.path.expanduser("~"), "Desktop/Hofstra/Brochadia/brochadia/src/documents", "SASD.pdf")
fs = gridfs.GridFS(mongoDB)

def calculate_hash(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()



TOURISM_CONTINENT_PATH = Path(__file__).resolve().parent / "tourism_with_continent.csv"
try:
    tourism_continent_df = pd.read_csv(
        TOURISM_CONTINENT_PATH,
        usecols=["location", "continent"],
    )
    LOCATION_TO_CONTINENT = {
        str(row["location"]).strip().lower(): str(row["continent"]).strip()
        for _, row in tourism_continent_df.dropna(subset=["location", "continent"])
        .drop_duplicates(subset=["location"])
        .iterrows()
    }
except Exception:
    LOCATION_TO_CONTINENT = {}

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

fs = gridfs.GridFS(mongoDB)

def calculate_hash(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()


# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    print("Databases:", client.list_database_names())
    print("Brochadia Database:", client.Brochadia.list_collection_names())
except Exception as e:
    print(e)


print("Today's Season", get_season())


@app.route('/upload/<customer_id>', methods=['POST'])
def upload_pdf(customer_id):
    try:
        #print(userCollection)
        # 1. Basic Flask file validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        pdf_file = request.files['file']
        if pdf_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # 2. Read content once for hashing and GridFS storage
        pdf_content = pdf_file.read()
        pdf_hash = calculate_hash(pdf_content)
        
        # 3. Check for duplicates specifically inside this user's document
        # This looks for a document with the matching userId that already has this hash in its 'files' array
        existing_file = client.Brochadia.users.find_one({
            'userId': ObjectId(customer_id), 
            'files.hash': pdf_hash
        })
        
        if existing_file:
            return jsonify({'message': 'Duplicate PDF file detected for this user'}), 409
        
        # 4. Insert the PDF file content into GridFS
        file_id = fs.put(pdf_content, filename=pdf_file.filename)
        print(file_id)
        # 5. Insert metadata into the specific customer's document using $push
        metadata = {
            'filename': pdf_file.filename,
            'hash': pdf_hash,
            'file_id': file_id,
            'user_id': customer_id
        }
        #print("Customer_ID",ObjectId(customer_id))
        # Update the document matching the userId by appending to the 'files' array
        update_result = client.Brochadia.users.update_one(
            {'_id': ObjectId(customer_id)},
            {'$push': {'files': metadata}}
        )
        
        # 6. Safety check: Ensure the user actually existed
        if update_result.matched_count == 0:
            # If the user doesn't exist, you might want to delete the orphaned file from GridFS here
            fs.delete(file_id)
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'PDF file uploaded successfully'}), 201
        
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

def get_file_id_by_name(customer_id, target_filename="file.pdf"):
    """
    Retrieves the GridFS file_id for a specific file owned by a user.
    """
    try:
        # 1. Find the user AND the specific file in one query
        user_doc = client.Brochadia.users.find_one(
            {
                '_id': ObjectId(customer_id),
                'files.filename': target_filename
            },
            {
                # 2. Projection: Return ONLY the array item that matched
                'files.$': 1, 
                '_id': 0
            }
        )
        print("ID",user_doc['files'][0]['file_id'])
        # 3. Check if we actually found a match
        if user_doc and 'files' in user_doc:
            # Extract the file_id from the single returned array item
            return user_doc['files'][0]['file_id']
            
        # Return None if the user doesn't exist or the file wasn't found
        return None
        
    except Exception as e:
        print(f"Database error: {e}")
        return None

@app.route('/download/<user_id>', methods=['GET'])
def download_resume(user_id, file_name="file.pdf"):
    print("file_name",file_name)
    print("user_id",user_id)
    try:
        # 1. Convert the string file_id from the URL into a MongoDB ObjectId
        try:
            file_id = get_file_id_by_name(user_id, file_name)

            obj_id = ObjectId(file_id)
        except bson.errors.InvalidId:
            return jsonify({'error': 'Invalid file ID format'}), 400

        # 2. Ask GridFS for the file
        try:
            grid_out = fs.get(obj_id)
            #grid_out = fs.find_one({"files_id": obj_id})
        except gridfs.errors.NoFile:
            print("File not found")
            return jsonify({'error': 'File not found'}), 404

        '''
        save_directory = 'Desktop/Hofstra/Brochadia/brochadia/src/documents'

    # 2. Make sure the directory actually exists (creates it if it doesn't)
        #os.makedirs(save_directory, exist_ok=True)

        # 3. Create the full file path (e.g., 'src/documents/myfile.pdf')
        file_path = os.path.join(save_directory, grid_out.filename)

        with open(file_path, 'wb') as f:
            f.write(grid_out.read())
        
        '''
        # 3. Send the file-like object directly to the client
        
        return send_file(
            grid_out,
            mimetype='application/pdf',
            as_attachment=False,          # Set to True to force a file download
            download_name=grid_out.filename # Preserves the original filename
        )

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

def display_resume(user_id):
    pdf = download_resume(user_id)


    # 4. Read the data from grid_out and write it to the physical file
    return pdf


def regenerate_resume_for_user(
    user_id,
    file_name="file.pdf",
    review_data=None,
    description=None,
    rating=None,
):
    mongo_user_id = normalize_object_id(user_id)
    if not mongo_user_id:
        raise ValueError('Invalid user id')

    file_id = get_file_id_by_name(user_id, file_name)
    if not file_id:
        raise FileNotFoundError('File not found')

    try:
        obj_id = ObjectId(file_id)
    except bson.errors.InvalidId as exc:
        raise ValueError('Invalid file ID format') from exc

    user = get_user_document(
        user_id,
        {
            '_id': 1,
            'full_name': 1,
            'email': 1,
            'preferred_trip': 1,
            'trip_history': 1,
            'travel_history': 1,
            'travel_preference': 1,
            'location_preference': 1,
            'Saved_Trips_ID': 1,
            'Past_Trips_ID': 1,
            'files': 1,
        },
    )
    if not user:
        raise LookupError('User not found')

    updated_file = rebuild_resume_pdf(
        user,
        obj_id,
        fs,
        file_name=file_name,
        review_data=review_data,
        description=description,
        rating=rating,
    )

    metadata_update = client.Brochadia.users.update_one(
        {
            '_id': mongo_user_id,
            'files.filename': file_name,
        },
        {
            '$set': {
                'files.$.file_id': updated_file['file_id'],
                'files.$.hash': updated_file['hash'],
                'files.$.user_id': user_id,
            }
        },
    )
    if metadata_update.matched_count == 0:
        client.Brochadia.users.update_one(
            {'_id': mongo_user_id},
            {
                '$push': {
                    'files': {
                        'filename': file_name,
                        'hash': updated_file['hash'],
                        'file_id': updated_file['file_id'],
                        'user_id': user_id,
                    }
                }
            },
        )

    return updated_file


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    mongo_user_id = normalize_object_id(user_id)
    if not mongo_user_id:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = get_user_document(
        user_id,
        {
            'email': 1,
            'full_name': 1,
            'preferred_trip': 1,
            'travel_preference': 1,
            'trip_history': 1,
            'Saved_Trips_ID': 1,
            'location_preference': 1,
        },
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
            'travel_preference': user.get('travel_preference'),
            'trip_history':  user.get('trip_history'),
            'Saved_Trips_ID': user.get('Saved_Trips_ID'),
            'location_preference':user.get('location_preference')
        },
    }), 200


def normalize_object_id(value):
    normalized_value = str(value or '').strip()
    if not normalized_value:
        return None

    try:
        return ObjectId(normalized_value)
    except InvalidId:
        return None


def get_user_document(user_id, projection=None):
    mongo_user_id = normalize_object_id(user_id)
    
    if not mongo_user_id:
        return None

    return client.Brochadia.users.find_one({'_id': mongo_user_id}, projection)


def get_user_travel_preference(user_id):
    if not user_id:
        return None

    user = get_user_document(
        user_id,
        {'travel_preference': 1},
    )
    print(user_id, user) 
    if not user:
        return None
    
    return user.get('travel_preference')


def get_continent_for_location(location):
    normalized_location = (location or "").strip()
    if not normalized_location:
        return None

    trip = client.Brochadia.Trips.find_one(
        {"location": normalized_location},
        {"continent": 1},
    )
    if trip and trip.get("continent"):
        return trip.get("continent")

    return LOCATION_TO_CONTINENT.get(normalized_location.lower())


def get_trip_document_by_id(trip_id):
    normalized_trip_id = str(trip_id or '').strip()
    if not normalized_trip_id:
        return None

    try:
        mongo_trip_id = ObjectId(normalized_trip_id)
    except InvalidId:
        return None

    temp_trip = client.Brochadia.Temp_Trips.find_one({'_id': mongo_trip_id})
    if temp_trip:
        return temp_trip

    return client.Brochadia.Trips.find_one({'_id': mongo_trip_id})


def build_trip_history_entry(trip_id):
    trip = get_trip_document_by_id(trip_id)
    trip_payload = serialize_trip_document(trip) or {}
    budget_usd = trip_payload.get("budget_usd")

    if budget_usd is None:
        budget_usd = trip_payload.get("activities_total_usd")

    trip_history_entry = {
        "trip_id": trip_id,
        "location": trip_payload.get("location"),
        "continent": trip_payload.get("continent"),
        "trip_type": trip_payload.get("trip_type"),
        "group_size": trip_payload.get("group_size"),
        "season": trip_payload.get("season"),
        "budget_usd": budget_usd,
        "activities_total_usd": trip_payload.get("activities_total_usd"),
        "experiences": trip_payload.get("experiences") or [],
        "purchased_at": datetime.datetime.utcnow().isoformat(),
    }

    return {key: value for key, value in trip_history_entry.items() if value is not None}


def serialize_trip_document(trip):
    if not trip:
        return None

    trip_payload = dict(trip)
    experience_ids = trip_payload.get("experiences") or []
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

    if "_id" in trip_payload:
        trip_payload["_id"] = str(trip_payload["_id"])

    trip_payload["activities"] = activities
    trip_payload["activities_total_usd"] = round(total_usd, 2)
    return trip_payload


@app.route('/saved_trips', methods=['POST'])
def get_saved_trips():
    data = request.get_json() or {}
    trip_ids = data.get('tripIds')

    if not isinstance(trip_ids, list):
        return jsonify({'success': False, 'message': 'tripIds must be an array'}), 400

    trips = []
    for trip_id in trip_ids:
        trip = get_trip_document_by_id(trip_id)
        trip_payload = serialize_trip_document(trip)
        if trip_payload:
            trips.append(trip_payload)

    return jsonify({'success': True, 'trips': trips}), 200


@app.route('/unsave_trip', methods=['POST'])
def unsave_trip():
    data = request.get_json() or {}
    user_id = str(data.get('userId') or '').strip()
    trip_id = str(data.get('tripId') or '').strip()

    if not user_id:
        return jsonify({'success': False, 'message': 'userId is required'}), 400

    if not trip_id:
        return jsonify({'success': False, 'message': 'tripId is required'}), 400

    try:
        mongo_user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = client.Brochadia.users.find_one({'_id': mongo_user_id}, {'_id': 1})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    update_result = client.Brochadia.users.update_one(
        {'_id': mongo_user_id},
        {'$pull': {'Saved_Trips_ID': trip_id}},
    )

    removed_from_temp = False
    try:
        mongo_trip_id = ObjectId(trip_id)
    except InvalidId:
        mongo_trip_id = None

    if mongo_trip_id:
        delete_result = client.Brochadia.Temp_Trips.delete_one({'_id': mongo_trip_id})
        removed_from_temp = delete_result.deleted_count > 0

    return jsonify({
        'success': True,
        'message': 'Trip removed from saved trips',
        'removedFromUser': update_result.modified_count > 0,
        'removedFromTemp': removed_from_temp,
    }), 200

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

@app.route('/buy_trip', methods=['POST'])
def buy_trip():
    data = request.get_json() or {}
    user_id = (data.get('userId') or '').strip()
    trip_doc = data.get('trip')

    if not user_id:
        return jsonify({'success': False, 'message': 'userId is required'}), 400

    if not isinstance(trip_doc, dict) or not trip_doc:
        return jsonify({'success': False, 'message': 'trip is required'}), 400

    mongo_user_id = normalize_object_id(user_id)
    if not mongo_user_id:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = get_user_document(user_id, {'_id': 1, 'trip_history': 1})
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    trip_id = trip_doc.get('_id')
    Trips = client.Brochadia.Trips

    if trip_id:
        try:
            mongo_trip_id = ObjectId(trip_id)
        except InvalidId:
            mongo_trip_id = None

        if mongo_trip_id and Trips.find_one({'_id': mongo_trip_id}, {'_id': 1}):
            trip_id = str(mongo_trip_id)
        else:
            trip_insert_doc = dict(trip_doc)
            trip_insert_doc.pop('_id', None)
            insert_result = Trips.insert_one(trip_insert_doc)
            trip_id = str(insert_result.inserted_id)
    else:
        insert_result = Trips.insert_one(dict(trip_doc))
        trip_id = str(insert_result.inserted_id)


    trip_history_entry = build_trip_history_entry(trip_id)
    trip_history_update = client.Brochadia.users.update_one(
        {
            '_id': mongo_user_id,
        },
        {'$push': {'trip_history': trip_history_entry}},
    )


    return jsonify({
        'success': True,
        'message': 'Trip purchased successfully',
        'tripId': trip_id,        
    }), 200


@app.route('/review_trip', methods=['POST'])
def review_Trip():
    data = request.get_json() or {}
    user_id = (data.get('userId') or '').strip()
    trip_id = str(data.get('trip_id') or '').strip()
    description = str(data.get('description') or '').strip()
    rating = data.get('rating')

    if not user_id:
        return jsonify({'success': False, 'message': 'userId is required'}), 400

    if not trip_id:
        return jsonify({'success': False, 'message': 'trip_id is required'}), 400

    if not description:
        return jsonify({'success': False, 'message': 'description is required'}), 400

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'rating must be an integer from 1 to 5'}), 400

    if rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'rating must be an integer from 1 to 5'}), 400

    mongo_user_id = normalize_object_id(user_id)
    if not mongo_user_id:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = get_user_document(
        user_id,
        {
            'trip_history': 1,
            'travel_preference': 1,
            'location_preference': 1,
        },
    )
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    trip_history = user.get('trip_history') or []
    matching_trip = next(
        (
            trip
            for trip in trip_history
            if str(trip.get('trip_id') or '').strip() == trip_id
        ),
        None,
    )
    if not matching_trip:
        return jsonify({'success': False, 'message': 'Trip not found in user trip history'}), 404

    updated_travel_preference, updated_location_preference = analyze_text(
        description,
        user.get('travel_preference') or {},
        user.get('location_preference') or {},
    )

    update_result = client.Brochadia.users.update_one(
        {
            '_id': mongo_user_id # 1. Find the user unconditionally
        },
        {
            '$set': {
                # 2. Use a named identifier (e.g., $[trip]) instead of the standard $
                'trip_history.$[trip].review_rating': rating,
                'trip_history.$[trip].review_description': description,
                'trip_history.$[trip].reviewed_at': datetime.datetime.utcnow().isoformat(),
                
                # 3. These will now update NO MATTER WHAT
                'travel_preference': updated_travel_preference,
                'location_preference': updated_location_preference,
            }
        },
        # 4. Define what the $[trip] identifier actually means
        array_filters=[{'trip.trip_id': trip_id}] 
    )

    if update_result.matched_count == 0:
        return jsonify({'success': False, 'message': 'Trip review could not be saved'}), 404

    try:
        updated_resume = regenerate_resume_for_user(
            user_id,
            review_data=data,
            description=description,
            rating=rating,
        )
    except (FileNotFoundError, LookupError) as e:
        return jsonify({'success': False, 'message': str(e)}), 404
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Review saved but resume update failed: {e}'}), 500

    return jsonify({
        'success': True,
        'message': 'Trip review saved successfully',
        'trip_id': trip_id,
        'rating': rating,
        'description': description,
        'travel_preference': updated_travel_preference,
        'location_preference': updated_location_preference,
        'resume_file_id': str(updated_resume['file_id']),
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
    #access_token = get_access_token(session)
    occasion = request.args.get('trip_type')
    location = request.args.get('Country')
    budget = float(request.args.get('budget'))
    travel_date = request.args.get('travelDate')
    travel_days = request.args.get('travelDays')
    continent = get_continent_for_location(location)
    user_id = (request.args.get('userId') or request.args.get('user') or '').strip()
    user_travel_preference = get_user_travel_preference(user_id)
    print("User travel dict", user_travel_preference)
    if not occasion or not location:
        return jsonify({'success': False, 'message': 'Provide trip_type and Country query params'}), 400

    cursor = client.Brochadia.Trips.find({'trip_type': occasion, 'location': location, 'experiences': {'$exists': True, '$ne': []}})
    trips = list(cursor)
    #print("TRIPS if they are empty", trips)
    if not trips:
        #print("Calling OpenSwarm AI")
        season = get_season()
        ai_activities = []
        
        try:
            coords_for_trips = get_random_coordinates(location)
        
        except Exception as e:
            # Fallbackxwx
            print("ERROR WITH AI GEN LATLONG", e)
            coords_for_trips = latLong_Agent(location)
        #print("RESULTS FOR COORD", coords_for_trips)
        if len(coords_for_trips) == 1:
            coords_for_trips = [get_city_geocode(location, session)]
        print("These are the Coords", len(coords_for_trips))
        session.headers.update({"Authorization": f"Bearer {access_token}"})
        if coords_for_trips:
                # Get List of activities for each trip
            for lat, lon in coords_for_trips:
                try:
                    print("Loop for ",lat, lon)
                    
                    raw_activities = get_activities(lat, lon)
                    
                    
                    if isinstance(raw_activities, dict):
                        raw_activities = raw_activities.get("data") or []
                    print("Raw Activities",len(raw_activities))
                    candidates = []
                    for activity in raw_activities:
                        #print("short",activity.get('shortDescription'), activity.get('description'))
                        if not isinstance(activity, dict):
                            continue
                        candidates.append(
                            {
                                "id": activity.get("id"),
                                "name": activity.get("name"),
                                "shortDescription": activity.get('shortDescription') if  activity.get('shortDescription') else  activity.get('description'),
                                "price": activity.get("price"),
                                "price_USD": convert_price_to_usd(activity.get("price")),
                                "pictures": activity.get("pictures"),
                            }
                        )


                        
                        

                    if len(candidates) >= 30:
                        
                        new_candidates = []
                        for can in candidates:
                            pers_score = single_userPref_score(user_travel_preference, can)
                            if pers_score >= 0:
                                new_candidates.append((pers_score, can))
                        
                        
                        
                        new_candidates = sorted(new_candidates, key=lambda x: x[0], reverse=True)

                        print("Candidates shortened to",len(new_candidates))
                        new_candidates = [activity[1] for  activity in new_candidates]
                        # Get the top 20 ACtivities that have the highest personalized score
                        candidates = new_candidates[0:15]
                        print("Candidates shortened to",len(candidates))       
                     
                    print("Current Activity",len([candidate.get("shortDescription") for candidate in candidates]))
                    if candidates:
                        selector_agent = Agent(
                            name="Trip Activity Selector",
                            instructions=(
                                "You are a travel curator. From the provided activities list, select "
                                "the best matches for the requested trip_type. If a user travel_preference "
                                "dictionary is provided, read the shortDescription or description features to personalize the ranking toward liked "
                                "items(items that are Greater than 0) and away from disliked ones(items that are Less than 0) Based on the shortDescription feature of each activity in activites. Return ONLY "
                                "a JSON array of activity objects taken from the input list. Do not modify existing fields or"
                                "add new fields or commentary."
                            ),
                            output_type="json",
                        )
                        #print(json.dumps(user_travel_preference or {}))
                        response = openAI_client.run(
                            agent=selector_agent,
                            messages=[
                                {
                                    "role": "user",
                                    "content": (
                                        f"location={location}, season={season}, "
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
                            
                        print("CONTENT", content)
                        if content:
                            try:
                                #print(content.split("```json")[-1].split("```")[0])
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
                    print("Error 3",e)
                
                #Sort by amount in price feature
                if occasion == "Backpacking":
                    ai_activities = sorted(ai_activities, key=lambda x: float(x['price_USD']))
                else:
                    ai_activities = sorted(ai_activities, key=lambda x: float(x['price_USD']), reverse=True)

                if ai_activities:
                    activity_ids = []
                    total_usd = 0.0
                    
                    for i, activity in enumerate(ai_activities):
                        
                        if not isinstance(activity, dict):
                            continue
                        print(i, activity.get("price_USD") is None)
                        activity_id = activity.get("id")
                        if not activity_id:
                            continue

                        if activity.get("price_USD") is None:
                            converted_price = convert_price_to_usd(activity.get("price"))
                            
                            if converted_price:
                                try:
                                    activity["price_USD"] = float(converted_price)
                                except (TypeError, ValueError):
                                    print("TYPE OR VALUE ERROR 0")
                                    pass
                        print("USD DOllars", float(budget), total_usd > budget,activity.get("price_USD"), type(activity.get("price_USD")))
                        try:
                            total_usd += activity.get("price_USD")
                            
                            if total_usd > budget:
                                break
                        except (TypeError, ValueError):
                            print("TYPE OR VALUE ERROR 1")
                            continue
                        #print("ADDING ACTIVITY", activity)
                        experiences_collection.update_one(
                            {"id": activity_id},
                            {"$setOnInsert": activity},
                            upsert=True,
                        )
                        activity_ids.append(activity_id)

                        
                        
                    trips.append(
                        {
                            "user_id": user_id,
                            "location": location,
                            "continent": continent,
                            "trip_type": occasion,
                            "group_size": 1,
                            "experiences": activity_ids,
                        }
                    )
                    if len(trips) != 0:
                        print("GENERATED TRIPS Complete for", lat, lon, "Is complete")
                # TODO Take each trip and create a Trip Document for each Generated Trips

        # return jsonify({'success': False, 'message': 'No trip for that country and preference was found'}), 404

        print('Trips for', location, 'with trip_type', occasion, ':', trips)
    else:
        # If trips were found similar to the database
        trip_copy = []
        for trip in trips:
            trip_exp = extract_experiences(trip)
            # Use the $in operator to find all documents matching any ID in the list at once
            query = {"id": {"$in": trip_exp}}
    
            # Execute the query and convert the MongoDB cursor directly to a Python list
            found_documents = list(experiences_collection.find(query))
            #print("FOUNDED DOCUMENTS",found_documents)
            
            
            
            doc_score = calculate_userPref_score(user_travel_preference, found_documents)
            
            if doc_score >= 0:
                trip_copy.append(trip)
        trips = trip_copy
                



    submitTrips = []

    for trip in trips:
        trip_payload = serialize_trip_document(trip)
        if trip_payload:
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

    new_user["_id"] = result.inserted_id
    print(new_user["_id"])
    create_Resume(new_user, "file.pdf")

    
    
    return jsonify({
        'success': True,
        'message': 'User created successfully',
        'userId': str(result.inserted_id),
    }), 201

@app.route('/login', methods=['POST'])
def login():
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
