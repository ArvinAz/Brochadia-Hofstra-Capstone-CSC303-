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
from pymongo import UpdateOne
from swarm import Swarm, Agent
from typing import List
import ast
from datetime import date
import datetime
import json
import geopy
from geopy.geocoders import Nominatim
import asyncio
from bson.objectid import ObjectId
from bson.errors import InvalidId
from trip_Functions import analyze_text

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

print("Today's Season", get_season())


@app.route('/signup', methods=['POST'])
def signup(client: MongoClient):
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


@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id, client: MongoClient):
    try:
        mongo_user_id = ObjectId(user_id)
    except InvalidId:
        return jsonify({'success': False, 'message': 'Invalid user id'}), 400

    user = client.Brochadia.users.find_one(
        {'_id': mongo_user_id},
        {'email': 1, 'full_name': 1, 'preferred_trip': 1},
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
        },
    }), 200
