from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

client: AsyncIOMotorClient = None
db: AsyncIOMotorDatabase = None


def get_mongo_db() -> AsyncIOMotorDatabase:
    global client, db
    if db is None:
        client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=500)
        db_name = settings.MONGO_URI.split("/")[-1].split("?")[0] or "portfolio_db"
        db = client[db_name]
    return db


async def close_mongo_connection():
    global client
    if client:
        client.close()
