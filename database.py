
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.encoders import jsonable_encoder

async def get_database():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    return client.App

async def get_collection(collection_name: str):
    db = await get_database()
    return db[collection_name]