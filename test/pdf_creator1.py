from multiprocessing.connection import Client
import requests

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
from reportlab.lib.pagesizes import letter

file_name = "Hello_World.pdf"
file_path = "Desktop/Hofstra/Brochadia/test/pdf_editor/pdfs"


signUpData =   {
        "full_name": "Maya Chen",
        "email": "maya.chen@example.com",
        "password": "TestPass!234",
        "preferred_trip": "Cultural",
        "trip_continent": "Asia",
        "trip_country": "Japan",
        "travel_party_size": "2",
        "trip_date": "2025-04-12",
        "trip_budget": "4200",
        "details": (
            "I loved Kyoto temples, quiet gardens, and small ramen shops, "
            "but disliked crowded train stations and overpriced souvenir stores in Tokyo."
        ),
    }

def create_Resume(data ,fileName, filePath):
    save_name = os.path.join(os.path.expanduser("~"), filePath, fileName)


    canvas = Canvas(save_name, pagesize=letter)
    width, height = letter

    # --- Draw the Header ---
    canvas.setFont("Helvetica-Bold", 18)
    # Draw centered string at the top of the page
    canvas.drawCentredString(width / 2.0, height - 70, "Travel Resume by"+data['full_name'])

    # --- Draw the Body (Lyrics) ---
    canvas.setFont("Helvetica", 12)


    # Start printing lyrics 120 points from the top, 100 points from the left
    y_position = height - 120 
    x_position = 100
    line_spacing = 15
    trip_details = ""
    trip_desc = data['details']
    for line in data.keys():
        if(line not in ["full_name", "details","email","password"]):
            formatted_line = line.replace("_", " ")
            formatted_line = formatted_line[:1].upper() + formatted_line[1:]
            trip_details += str(formatted_line) + ": " + data[line] + "|"
    canvas.drawString(x_position, y_position, trip_details)

    # Adding Description to the trip
    y_position -= 20

    canvas.drawString(x_position, y_position, trip_desc)


    canvas.save()

    # Upload the pdf file 
    files = 0
    url = 'http://127.0.0.1:5000//upload/69d55419522dff65078c470a'
    with open(save_name, 'rb') as img:
        files = {"file": ("file.pdf", img, "application/pdf")}
        response = requests.post(url, files=files)
    
    # Now delete the File you just uploaded
    
    print(requests.get("http://127.0.0.1:5000//get_res/69d55419522dff65078c470a"))

    print(response.status_code, response.text)

create_Resume(signUpData ,file_name, file_path)
