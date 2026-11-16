
import os
from urllib.parse import urlsplit, unquote
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

# Load .env directly from the project folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

uri = os.getenv("MONGO_URI")

if not uri:
    print("ERROR: MONGO_URI was not found in .env")
    raise SystemExit

try:
    parsed = urlsplit(uri)

    print("Environment file found:", os.path.exists(env_path))
    print("MongoDB URI found:", bool(uri))
    print("MongoDB host:", parsed.hostname)
    print("Username present:", bool(parsed.username))
    print("Password present:", bool(parsed.password))
    print("Database name:", os.getenv("DATABASE_NAME"))

    client = MongoClient(
        uri,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=15000
    )

    client.admin.command("ping")
    print("\nSUCCESS: MongoDB authentication and connection working!")

except Exception as e:
    print("\nCONNECTION FAILED:")
    print(type(e).__name__, str(e))
