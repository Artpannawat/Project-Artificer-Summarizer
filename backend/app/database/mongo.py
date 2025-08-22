from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

MONGO_DETAILS = config("MONGO_DETAILS", default="mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.artificer_summarizer
user_collection = database.get_collection("users")

# Add index for unique email
async def create_unique_index():
    await user_collection.create_index("email", unique=True)