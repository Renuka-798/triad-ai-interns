
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFSBucket

load_dotenv()

# Connect to MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "triad_dms")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

# Select database
db = client[DATABASE_NAME]

# Initialize GridFS
fs = GridFSBucket(db)

# Collections
users_collection = db["users"]
documents_collection = db["documents"]
metadata_fields_collection = db["metadata_fields"]
access_requests_collection = db["access_requests"]
