from fastapi import FastAPI, status, Depends
import os
import asyncio
from functions.database import mongodb_client
from functions import crud
from functions import schemas
from pymongo import AsyncMongoClient
from typing import List


# Declare client for API calls
client = mongodb_client(user= os.getenv('MONGODB_USER'), password= os.getenv('MONGODB_PASSWORD'))

tags = [
    {'name' : 'availabilities', 'description' : 'CRUD operations for the availabilities collection'}
]

app = FastAPI(title="MongoDB database")


# App landing page
@app.get("/", status_code= status.HTTP_200_OK)
async def read_root():
    return {"Padel Radar app": "Running"}


@app.post("/availabilities/",
    response_model= None,
    status_code=status.HTTP_201_CREATED,
    tags= tags['availabilities']
)

async def create_availabilities(availabilities: List[schemas.AvailabilityCreate]):
    """
    Insert a new set of availabilities in the MongoDB [availabilities] collection.
    Does not insert availabilities if data in the collection is already fresh
    """
    
    crud.insert_availabilities(mongodb_client, availabilities)
    
    
    
    

@app.get(
    "/availabilities/",
    status_code = status.HTTP_200_OK,
)
async def read_availabilities(query_filters: schemas.AvailabilityRead):
    """
    Query a list of availabilities based on a set of filters defined by a AvailabilityRead model

    """
    crud.query_availabilities(mongodb_client, query_filters)