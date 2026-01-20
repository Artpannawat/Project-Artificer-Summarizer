from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

import certifi
MONGO_DETAILS = config("MONGO_DETAILS", default="mongodb://localhost:27017")

# Use certifi for SSL only if connecting to Cloud (Atlas), skip for Localhost to avoid SSL Error
if "localhost" in MONGO_DETAILS or "127.0.0.1" in MONGO_DETAILS:
    client = AsyncIOMotorClient(MONGO_DETAILS, serverSelectionTimeoutMS=5000)
else:
    client = AsyncIOMotorClient(MONGO_DETAILS, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
db = client.artificer_summarizer # Export 'db' as well for flexible usage
database = db # Alias for existing code
user_collection = database.get_collection("users")
history_collection = database.get_collection("history")

# Add index for unique email
async def create_unique_index():
    await user_collection.create_index("email", unique=True)
    await history_collection.create_index("user_id") # Index for faster history queries