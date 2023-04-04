import os
import motor.motor_asyncio

#Connect to Mongo database
PASS = os.environ["MONGODB_PASSWORD"]
MONGODB_URL = f"mongodb+srv://asgh1234515:{PASS}@cluster0.eyo7hbj.mongodb.net/?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
mongodb = client.collection
