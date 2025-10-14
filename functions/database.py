from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from contextlib import contextmanager
from typing import Generator


@contextmanager
def mongodb_client(user:str, password:str) -> Generator[MongoClient, None, None]:
    uri = f"mongodb+srv://{user}:{password}@cluster0.dkiat2v.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Send a ping to confirm a successful connection and yield client
    try:
        client.admin.command('ping')
        print("Connection to MongoDB successful!")
        yield client
        
    except Exception as e:
        print(e)
        raise
    
    finally:
        client.close()
        
        
        
        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='testing MongoDB database connection')
    parser.add_argument("--user", type=str, required=False, help="The username for the database")
    parser.add_argument("--password", type=str, required=False, help="The password for the database")
    
    args = parser.parse_args()
    
    with mongodb_client(args.user, args.password) as client:
        dbs = client.list_database_names()
        print("Databases : ", dbs)