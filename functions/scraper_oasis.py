import time
import schemas
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
from database import instantiate_mongodb_client
from crud import insert_availabilities
import asyncio


def scrape_oasis(username:str = None, password:str = None, selected_date: str = None) -> List[schemas.AvailabilityCreate]:
    
    solpak = {"name": "Padel 1 - SOLPAK",
          "id": "21185ff2-c3cc-4f93-b3b4-eac9070dd8f6"}
    porsche = {"name": "Padel 2 - PORSCHE",
                "id" : "836d44ae-692f-4fd0-80ff-5a050762c3f1"}
    caprice = {"name": "Padel 3 - CAPRICE",
            "id": "9e678e91-72a4-4ffe-8f00-a1f0d64f6f52"}
    
    session = requests.Session()
    
    
    ### Scrape availabilities ### 
    today = datetime.today().strftime("%d/%m/%Y")
    selected_date_formated = datetime.strftime(
        datetime.strptime(selected_date, "%d/%m/%Y"),
        "%Y-%m-%d"
    )

    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr,en-US;q=0.9,en;q=0.8',
        'if-none-match': '"d7bac161e4a2ab87817b85651de80790"',
        'origin': 'https://oasis-padel.doinsport.club',
        'priority': 'u=1, i',
        'referer': 'https://oasis-padel.doinsport.club/',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'x-locale': 'fr',
    }

    response = session.get(f'https://api-v3.doinsport.club/clubs/playgrounds/plannings/{selected_date_formated}?club.id=3ddfa83f-19dc-4ff5-b2c1-2543eb1556a4&from=04:00&to=23:29:00&activities.id=8ee9b629-c5b1-4fd5-a680-51b1288e2527&bookingType=unique', headers=headers)
    response.raise_for_status()
    response.status_code
    json_to_parse = response.json()
    time.sleep(1.5)
    
    ### Retrieve available time slots ###
    scraping_datetime = datetime.now(ZoneInfo("Indian/Reunion"))
    region = "Ouest"
    city = 'Saint-Paul'
    club = 'Oasis'
    output = []

    for playground in json_to_parse['hydra:member']:
        if playground['name'] in (solpak['name'], porsche['name'], caprice['name']):
            for activity in playground.get("activities", []):
                for slot in activity["slots"]:
                    availability_time = datetime.strptime(slot["startAt"], "%H:%M").time()
                    for price in slot["prices"]:
                        if price['bookable']:
                            output.append(schemas.AvailabilityCreate(
                                scraping_datetime= scraping_datetime,
                                region= region,
                                city= city,
                                club= club,
                                court= playground['name'],
                                availability_date= datetime.strptime(selected_date, "%d/%m/%Y"),
                                availability_time= availability_time,
                                availability_duration= price['duration'] // 60
                            ))
    return output
                    

async def main_insert():                   
    available_slots = scrape_oasis(args.username, args.password, args.date)
    await insert_availabilities(instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
                          available_slots)    
        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='test scraping for Oasis padel club')
    parser.add_argument("--username", type=str, required=False, help="The username of the oasis account")
    parser.add_argument("--password", type=str, required=False, help="The password for the oasis account")
    parser.add_argument("--date", type=str, required=True, help="The selected date in the format DD/MM/YYYY")
    parser.add_argument("--mongodb_user", type=str, help="The username for the mongodb database if data is to be inserted in a collection")
    parser.add_argument("--mongodb_password", type=str, help="The password for the mongodb database")
    
    args = parser.parse_args()
    
    available_slots = scrape_oasis(args.username, args.password, args.date)

    asyncio.run(main_insert())   