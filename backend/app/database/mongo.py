from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config

MONGO_DETAILS = config("MONGO_DETAILS", default="mongodb://localhost:27017")

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client.artificer_summarizer # Export 'db' as well for flexible usage
database = db # Alias for existing code
user_collection = database.get_collection("users")
history_collection = database.get_collection("history")

# Add index for unique email
async def create_unique_index():
    await user_collection.create_index("email", unique=True)
    await history_collection.create_index("user_id") # Index for faster history queries