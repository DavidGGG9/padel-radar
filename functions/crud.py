from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import asyncio
import schemas
from pymongo import AsyncMongoClient
from database import instantiate_mongodb_client


async def check_freshness(mongodb_client:AsyncMongoClient, 
                          availabilities:List[schemas.AvailabilityRead],
                          minutes:int):
    """
    Freshness is checked by first retrieving documents via a regular query.
    Then, the oldest scraping date is checked for each club. Each club that has an oldest scraping date 
    that is older than {minutes} returns False
    
    Returns:
    freshness (dict): {club : True/False}  
    """
    
    query_result = await query_availabilities(mongodb_client, availabilities)
    freshness_dict = {}
    oldest_scraping_datetime = datetime(2025, 1, 1, tzinfo= ZoneInfo("Indian/Reunion"))
    for document in query_result:
        freshness_club = document['club']
        freshness_timestamp = freshness_dict.setdefault(freshness_club, oldest_scraping_datetime)
        document_timestamp = datetime.fromisoformat(document['scraping_datetime'])
        
        if document_timestamp > freshness_timestamp:
            freshness_dict[freshness_club] = document_timestamp
        
        
    # Check data freshness for each club
    for club in freshness_dict:
        delta = (datetime.now(ZoneInfo("Indian/Reunion")) - freshness_dict[club]).total_seconds() /60
        if delta > minutes:
            print(f'data for {club} is not fresh enough...')
            freshness_dict[club] = False
        else:
            freshness_dict[club] = True
    
    return freshness_dict


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
            result = await collection.delete_many(final_query)
            return result
        
        except Exception as e:
            print(str(e))
            return False


async def main_query(client, query_filters):
    availabilities = await query_availabilities(client, query_filters)
    print(availabilities)
    
async def main_delete(client, query_filters):
    deleted = await delete_availabilities(client, query_filters)
    print(deleted) 
    
async def main_freshness(client, query_filters):
    freshness = await check_freshness(client, query_filters, 10)
    print(freshness)
 
 
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='testing crud functions')
    parser.add_argument("--mongodb_user", type=str, help="The username for the mongodb database if data is to be inserted in a collection")
    parser.add_argument("--mongodb_password", type=str, help="The password for the mongodb database")
    parser.add_argument("--region", action= 'append',type=str, required=False, help="The region for the search")
    parser.add_argument("--city", action= 'append',type=str, required=False, help="The city for the search")
    parser.add_argument("--club", action= 'append', type=str, required=False, help="The club for the search")
    parser.add_argument("--court", action= 'append', type=str, required=False, help="The court for the search")
    parser.add_argument("--date", type=str, required=True, help="The date for the search")
    parser.add_argument("--time", type=str, required=False, help="The time for the search")
    parser.add_argument("--duration", type=str, required=False, help="The duration for the search")
    
    args = parser.parse_args()
    
    ### Test the query function
    # asyncio.run(main_query(
    #     instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
    #     schemas.AvailabilityRead(
    #         region = args.region,
    #         city = args.city,
    #         club = args.club,
    #         court = args.court,
    #         availability_date = datetime.strptime(args.date, "%d/%m/%Y").date(),
    #         availability_time = args.time,
    #         availability_duration = args.duration
    #     )
    # ))

    ### Test the delete function
    # asyncio.run(main_delete(
    #     instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
    #     schemas.AvailabilityRead(
    #         region = args.region,
    #         city = args.city,
    #         club = args.club,
    #         court = args.court,
    #         availability_date = datetime.strptime(args.date, "%d/%m/%Y").date()
    #     )
    # ))

    ## Test the freshness function
    asyncio.run(main_freshness(
            instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
            schemas.AvailabilityRead(
                region = args.region,
                city = args.city,
                club = args.club,
                court = args.court,
                availability_date = datetime.strptime(args.date, "%d/%m/%Y").date(),
                availability_time = args.time,
                availability_duration = args.duration
            )
        ))