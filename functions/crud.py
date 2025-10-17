from typing import List
from datetime import datetime
import os
import asyncio
from functions import schemas
from pymongo import AsyncMongoClient


async def check_freshness(mongodb_client:AsyncMongoClient,
                          now: datetime,
                          regions: List[str] = None,
                          cities: List[str] = None,
                          clubs: List[str] = None,
                          ):
    with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
    
        if clubs:
            for club in clubs:
                cursor = collection.find({'club' : club})
                data = cursor.to_list()
                ordered_scraping_datetimes = data['scraping_datetime']
                
                delta = (now - scraping_datetime).total_seconds() /60
                if delta > 10:
                    print(f'data for {club} is not fresh enough...')
                    return False
            return True
        
        if cities:
            # retrieve associated clubs and call check_freshness recursively
            pass
        if regions:
            # retrieve associated clubs and call check_freshness recursively
            pass
        
    return


async def insert_availabilities(mongodb_client:AsyncMongoClient, 
                                availabilities:List[schemas.AvailabilityCreate]):
    with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
    
        try:
            slots = [slot.model_dump(mode = 'json') for slot in availabilities]
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
    
    
            
  
        
        
