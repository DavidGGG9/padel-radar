from typing import List
import os
import asyncio
from functions import schemas
from pymongo import AsyncMongoClient


async def insert_availabilities(mongodb_client:AsyncMongoClient, 
                                availabilities:List[schemas.AvailabilityCreate]):
    with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
    
        try:
            slots = [slot.model_dump() for slot in availabilities]
            await collection.insert_many(slots)
            return True      
        
        except Exception as e:
            print(e)
            raise

async def query_availabilities(mongodb_client:AsyncMongoClient,
                              query_filters:schemas.AvailabilityRead):
    with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
        
        # Retrieve the non-empty fields
        mongo_filters = {k : v for k, v in query_filters.model_dump().items() if v is not None}
        
        try:
            if len(mongo_filters) == 1:
                final_query = mongo_filters[0]
            else:
                final_query = {"$and": mongo_filters}
            
            cursor = collection.find(final_query)
            return cursor.to_list()
            
        except Exception as e:
            print(str(e))
            return False
    
    
            
  
        
        
