from multiprocessing.connection import Client

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

app = Flask(__name__)


save_name = os.path.join(os.path.expanduser("~"), "Desktop/Hofstra/Brochadia/test/pdf_editor/pdfs", "SASD.pdf")

#fs = gridfs.GridFS(db)

password = "mongodb+srv://azad:pOfXLo5WBVp8JSuS@dwcluster.2zyrq7o.mongodb.net/?appName=DWCluster"

client = MongoClient(password, server_api=ServerApi('1'))
mongoDB = client["Brochadia"]
userCollection = mongoDB['users']

fs = gridfs.GridFS(mongoDB)

def calculate_hash(content):
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()


@app.route('/get_res/<user_id>', methods=['GET'])
def get_pdf(user_id):
    existing_file = userCollection.find_one({
        'userId': ObjectId(user_id), 
        'files': {
            "$ne": None
        }
    })
    #mongoDB.fs.chunks.find( { files_id: myFileID } ).sort( { n: 1 } )
    bucket = gridfs.GridFSBucket(mongoDB)
    file = bucket.open_download_stream_by_name("file.pdf")
    print(file)
    contents = file.read()
    print(contents)

    with open("recovered_document.pdf", "wb") as file:
        file.write(contents)
        return file

    




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
        existing_file = userCollection.find_one({
            'userId': ObjectId(customer_id), 
            'files.hash': pdf_hash
        })
        
        if existing_file:
            return jsonify({'message': 'Duplicate PDF file detected for this user'}), 409
        
        # 4. Insert the PDF file content into GridFS
        file_id = fs.put(pdf_content, filename=pdf_file.filename)
        
        # 5. Insert metadata into the specific customer's document using $push
        metadata = {
            'filename': pdf_file.filename,
            'hash': pdf_hash,
            'file_id': file_id
        }
        #print("Customer_ID",ObjectId(customer_id))
        # Update the document matching the userId by appending to the 'files' array
        update_result = userCollection.update_one(
            {'_id': ObjectId(customer_id)},
            {'$push': {'files': metadata}}
        )
        
        # 6. Safety check: Ensure the user actually existed
        if update_result.matched_count == 0:
            # If the user doesn't exist, you might want to delete the orphaned file from GridFS here
            fs.delete(file_id)
            randomUser = userCollection.find_one()
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'message': 'PDF file uploaded successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)





# Upload the pdf file 


