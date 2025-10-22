from typing import List
from datetime import datetime
import os
import asyncio
import schemas
from pymongo import AsyncMongoClient
from database import instantiate_mongodb_client


async def check_freshness(mongodb_client:AsyncMongoClient,
                          now: datetime,
                          regions: List[str] = None,
                          cities: List[str] = None,
                          clubs: List[str] = None,
                          ):
#     with mongodb_client as client:
#         db = client[os.getenv('MONGODB_DB_TEST')]
#         collection = db.availabilities
    
#         if clubs:
#             for club in clubs:
#                 cursor = collection.find({'club' : club})
#                 data = cursor.to_list()
#                 ordered_scraping_datetimes = data['scraping_datetime']
                
#                 delta = (now - scraping_datetime).total_seconds() /60
#                 if delta > 10:
#                     print(f'data for {club} is not fresh enough...')
#                     return False
#             return True
        
#         if cities:
#             # retrieve associated clubs and call check_freshness recursively
#             pass
#         if regions:
#             # retrieve associated clubs and call check_freshness recursively
            # pass
    return


async def insert_availabilities(mongodb_client:AsyncMongoClient, 
                                availabilities:List[schemas.AvailabilityCreate]):
    async with mongodb_client as client:
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
    async with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
        
        # Retrieve the non-empty fields
        mongo_filters = [{k : v} for k, v in query_filters.model_dump(mode = 'json').items() if v is not None]
        
        # reformat fields that are lists into $in
        formatted_filters = []
        for filter in mongo_filters:
            for k, v in filter.items(): 
                if isinstance(v, list):
                    formatted_filters.append({k : {'$in' : v}})
                else:
                    formatted_filters.append({k:v})
                     
        try:
            if len(formatted_filters) == 1:
                final_query = formatted_filters[0]
            else:
                final_query = {"$and": formatted_filters}
            
            print(f'query filter looks like : {final_query}')
            cursor = collection.find(final_query)
            result = await cursor.to_list()
            return result
        
        except Exception as e:
            print(str(e))
            return False
    

async def delete_availabilities(mongodb_client:AsyncMongoClient,
                              query_filters:schemas.AvailabilityDelete):
    async with mongodb_client as client:
        db = client[os.getenv('MONGODB_DB_TEST')]
        collection = db.availabilities
        
        # Retrieve the non-empty fields
        mongo_filters = [{k : v} for k, v in query_filters.model_dump(mode = 'json').items() if v is not None]
        
        # reformat fields that are lists into $in
        formatted_filters = []
        for filter in mongo_filters:
            for k, v in filter.items(): 
                if isinstance(v, list):
                    formatted_filters.append({k : {'$in' : v}})
                else:
                    formatted_filters.append({k:v})
                     
        try:
            if len(formatted_filters) == 1:
                final_query = formatted_filters[0]
            else:
                final_query = {"$and": formatted_filters}
            
            print(f'query filter looks like : {final_query}')
            cursor = collection.find(final_query)
            result = await cursor.to_list()
            return result
        
        except Exception as e:
            print(str(e))
            return False

async def main_query(client, query_filters):
    availabilities = await query_availabilities(
                        mongodb_client = client,
                        query_filters = query_filters
                        )
    print(availabilities)
 
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='testing crud functions')
    parser.add_argument("--mongodb_user", type=str, help="The username for the mongodb database if data is to be inserted in a collection")
    parser.add_argument("--mongodb_password", type=str, help="The password for the mongodb database")
    parser.add_argument("--region", type=str, required=False, help="The region for the search")
    parser.add_argument("--city", type=str, required=False, help="The city for the search")
    parser.add_argument("--club", type=str, required=False, help="The club for the search")
    parser.add_argument("--court", type=str, required=False, help="The court for the search")
    parser.add_argument("--date", type=str, required=True, help="The date for the search")
    parser.add_argument("--time", type=str, required=False, help="The time for the search")
    parser.add_argument("--duration", type=str, required=False, help="The duration for the search")
    
    args = parser.parse_args()
    
    asyncio.run(main_query(
        instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
        schemas.AvailabilityRead(
            region = [args.region],
            # city = [args.city],
            club = [args.club],
            court = [args.court],
            availability_date = datetime.strptime(args.date, "%d/%m/%Y").date(),
            availability_time = args.time,
            availability_duration = args.duration
        )
    ))