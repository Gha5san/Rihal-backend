import motor.motor_asyncio

#Connect to Mongo database
MONGODB_URL   = f"mongodb://root:password@mongodb:27017/"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL,
                                                serverSelectionTimeoutMS=15000)
mongodb = client["collection"]
