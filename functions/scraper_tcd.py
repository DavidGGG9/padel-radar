from typing import List
import schemas
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
from database import instantiate_mongodb_client
from crud import insert_availabilities




def scrape_tcd(username:str, password:str, selected_date: str) -> List[schemas.AvailabilityCreate]:
    """
    Scraper for court availabilities at TCD.
    
    Parameters:
        - username (str): Username used to login to https://dpr.gestion-sports.com/connexion.php?
        - password (str): Username used to login to https://dpr.gestion-sports.com/connexion.php?
        - selected_date (str): Date for which you want to scrape availabilities, in the format 'DD/MM/YYYY'
    
    Returns:
        - list of court availabilities (List[schemas.AvailabilityCreate]) : A list of availabilities, in the format defined by the pydantic model in schemas.AvalabilityCreate 
    
    """
    
    LOGIN_URL = 'https://dpr.gestion-sports.com/traitement/connexion.php?'
    BOOKING_URL = 'https://dpr.gestion-sports.com/membre/reservation.html'
    
    session = requests.Session()
    
    # 1) GET login page to obtain cookies and CSRF token
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        # 'Referer': 'https://dpr.gestion-sports.com/membre/compte/menu.html',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    try:
        resp = session.get(LOGIN_URL, headers= headers, timeout=10)
        resp.raise_for_status()  
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred on first login:", e)  
    
    time.sleep(3)
    
    # Log in
    payload = {
        'ajax' : 'connexionUser',
        'id_club' : '308',
        'email' : username,
        'form_ajax' : '1',
        'pass' : password,
        'compte' : 'user',
        'playeridonesignal' : '0',
        'identifiant' : 'identifiant',
        'externCo' : True
    }
    
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'fr,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://dpr.gestion-sports.com',
        'Referer': 'https://dpr.gestion-sports.com/connexion.php?',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
       }
    
    try:
        password_login_resp = session.post(LOGIN_URL, data=payload, headers=headers)
        password_login_resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("HTTP error occurred on second login:", e)  
        
    time.sleep(3)
    
    # Booking
    ## Iterating over multiples hours to retrieve all possible availabilities
    ## for a given availability date
    scraping_datetime = datetime.now(ZoneInfo("Indian/Reunion"))
    region = "Nord"
    city = 'Saint-Denis'
    club = 'TCD'
    hours = [f"{h:02d}:00" for h in range(6, 24, 2)]
    output = []

    for hour in hours:
        print(f'Scraping availabilities on the {selected_date} at {hour}...')
        
        payload = {
            'ajax': 'loadCourtDispo',
            'idSport': '885',
            'date' : selected_date,
            'hour' : hour
        }

        
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'fr,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://dpr.gestion-sports.com',
            'Referer': 'https://dpr.gestion-sports.com/membre/reservation.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        } 
        
        try:
            booking_resp = session.post(BOOKING_URL, data=payload, headers=headers)
            booking_resp.raise_for_status()
            response = booking_resp.json()
        except requests.exceptions.HTTPError as e:
            print("HTTP error occurred on booking request:", e) 
        except requests.exceptions.JSONDecodeError as e:
            print("JSONDecode error occurred on booking request:", e)  
            
        if booking_resp.status_code == 200:
            print(f'Request successful for hour {hour}')
            
            for court in response:
                for dispo in court['heuresDispo']:
                    for duration in dispo['duration']:
                        availability = schemas.AvailabilityCreate(
                            scraping_datetime= scraping_datetime,
                            region= region,
                            city= city,
                            club= club,
                            court= court['name'],
                            availability_date= datetime.strptime(selected_date, "%d/%m/%Y"),
                            availability_time= dispo['hourStart'],
                            availability_duration= duration['duration']
                        )
                        if availability not in output: 
                            output.append(availability)
            print(f'Availabilities successfully loaded for hour {hour}')
            time.sleep(2)
            
    return output


async def main_insert():
    available_slots = scrape_tcd(args.username, args.password, args.date)
    await insert_availabilities(instantiate_mongodb_client(args.mongodb_user, args.mongodb_password),
                          available_slots)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='test scraping for TCD padel club')
    parser.add_argument("--username", type=str, required=True, help="The username of the CF account")
    parser.add_argument("--password", type=str, required=True, help="The password for the CF account")
    parser.add_argument("--date", type=str, required=True, help="The selected date in the format DD/MM/YYYY")
    parser.add_argument("--mongodb_user", type=str, help="The username for the mongodb database if data is to be inserted in a collection")
    parser.add_argument("--mongodb_password", type=str, help="The password for the mongodb database")
    args = parser.parse_args()
    
    asyncio.run(main_insert())
    
    