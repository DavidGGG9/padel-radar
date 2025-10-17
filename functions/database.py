from pymongo import AsyncMongoClient
import os
from pymongo.server_api import ServerApi
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import json
import asyncio


@asynccontextmanager
async def mongodb_client(user:str, password:str) -> AsyncGenerator[AsyncMongoClient, None]:
    uri = f"mongodb+srv://{user}:{password}@cluster0.dkiat2v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = AsyncMongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection and yield client
    try:
        await client.admin.command('ping')
        print("Connection to MongoDB successful!")
        yield client
        
    except Exception as e:
        print(e)
        raise
    
    finally:
        await client.close()
        print("Connection to MongoDB successfully closed !")
        
        
        
async def init_collection(mongodb_client: AsyncMongoClient, db_name: str, collection_name: str, content_path:str =None):
    """
    Function to create a collection if it does not exist.
    Parameters:
      - mongodb_client (AsyncMongoClient): Mongo DB client used to connect to the database
      - collection_name (str): The name of the collection to create
      - content_path (str) : absolute path to the documents to be added to the collection
    
    """
    async with mongodb_client as client:
        db = client[db_name]
        existing_collections = await db.list_collection_names()
        
        if collection_name not in existing_collections:
            print(f"Collection '{collection_name}' does not exist. Creating it...")
            try:
                await db.create_collection(collection_name)
                print(f"Collection '{collection_name}' has been successfully created !")
                if content_path:
                    print('inserting content to the newly_created collection...')
                    with open(content_path, 'r', encoding = 'utf-8') as f:
                        content = json.load(f)
                        for key, value in content.items():
                            await db[collection_name].insert_one({key : value})
                return True
            except Exception as e:
                print(e)
        else:
            print(f"collection {collection_name} already exists in the database.]")
        
        

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='testing MongoDB database connection')
    parser.add_argument("--user", type=str, required=False, help="The username for the database")
    parser.add_argument("--password", type=str, required=False, help="The password for the database")
    parser.add_argument("--db", type=str, required=False, help="The name of the database")
    parser.add_argument("--collection", type=str, required=False, help="The name of the collection")
    parser.add_argument("--content_path", type=str, required=False, help="The path to the documents to be inserted to the newly created collection")
    
    args = parser.parse_args()
    
    async with mongodb_client(args.user, args.password) as client:
        await init_collection(client, args.db, args.collection, args.content_path)
    
        
if __name__ == '__main__':
    asyncio.run(main())