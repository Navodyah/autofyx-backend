# config/mongo_async.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB")

# Async MongoDB client
async_client = None
async_db = None

def get_async_mongo_client():
    """Get async MongoDB client"""
    global async_client
    if async_client is None:
        async_client = AsyncIOMotorClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000
        )
    return async_client

def get_async_database():
    """Get async database instance"""
    global async_db
    if async_db is None:
        client = get_async_mongo_client()
        async_db = client["autofyx"]
    return async_db

async def close_async_mongodb():
    """Close async MongoDB connection"""
    global async_client
    if async_client:
        async_client.close()
