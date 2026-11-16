
import os
import certifi

from dotenv import load_dotenv
from pymongo import MongoClient
from gridfs import GridFSBucket

# Get the main project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Explicitly load the project's .env file
# override=True ensures old environment values do not take priority
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "triad_dms")

if not MONGO_URI:
    raise ValueError("MONGO_URI is missing from .env")

client = MongoClient(
    MONGO_URI,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=15000
)

db = client[DATABASE_NAME]

fs = GridFSBucket(db)

users_collection = db["users"]
documents_collection = db["documents"]
metadata_fields_collection = db["metadata_fields"]
access_requests_collection = db["access_requests"]
