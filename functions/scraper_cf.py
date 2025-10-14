import time
import re
from datetime import datetime
import schemas
import requests
from bs4 import BeautifulSoup
from typing import List
    

def scrape_champ_fleuri(username:str, password:str, selected_date: str) -> List[schemas.AvailableSlot]:
    LOGIN_URL = "https://tennispadelchampfleuri.re/login"
    AVAILABILITIES_URL = "https://tennispadelchampfleuri.re/user/disponibilites"  
    session = requests.Session()

    # GET login page to obtain cookies + CSRF token
    response = session.get(LOGIN_URL, timeout=10)
    try:
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        print("Request failed:", e)
        

    csrf_meta = soup.find("meta", attrs={"name": "csrf-token"})["content"]
    csrf_input = soup.find("input", {"name": "_token"})
    csrf_token = csrf_input["value"] if csrf_input else csrf_meta["content"]
    
    print("CSRF token:", csrf_token)
    time.sleep(1)
    
    # Log in
    payload = {
        "email": username,
        "password": password,
        "_token": csrf_token 
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "fr,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "tennispadelchampfleuri.re",
        "Origin": "https://tennispadelchampfleuri.re",
        "Referer": LOGIN_URL,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
    }
    
    login_response = session.post(LOGIN_URL, data=payload, headers=headers)
    try:
        login_response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Login request failed:", e)
        
    time.sleep(1)
    
    # Onced logged in, send a get request to the dashboard page to get a new csrf token used to make a reservation
    availabilities_response = session.get(AVAILABILITIES_URL, timeout=15)
    try: 
        availabilities_response.raise_for_status()
        soup = BeautifulSoup(availabilities_response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        print("Avalabilities request failed:", e)
        

    csrf_meta = soup.find("meta", attrs={"name": "csrf-token"})["content"]
    csrf_input = soup.find("input", {"name": "_token"})
    csrf_token = csrf_input["value"] if csrf_input else csrf_meta["content"]

    print("CSRF token:", csrf_token)
    time.sleep(1.5)

    ## Also retrieve and parse the page snapshot that will be reused in the livewire update
    snapshot_divs = soup.find_all("div", attrs={"wire:snapshot": True})

    snapshot_length = 0
    longest_snapshot = None
    for element in snapshot_divs:
        snapshot = element["wire:snapshot"]
        if len(snapshot) >= snapshot_length:
            longest_snapshot = snapshot
            snapshot_length = len(snapshot)

    ### Update sport and selected_date
    sport_str = 'padel'

    cookies = {
        'XSRF-TOKEN': session.cookies.get('XSRF-TOKEN'),
        'tennis_et_padel_champ_fleuri_session': session.cookies.get('tennis_et_padel_champ_fleuri_session')
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'fr,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Origin': 'https://tennispadelchampfleuri.re',
        'Referer': 'https://tennispadelchampfleuri.re/user/disponibilites',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'X-Livewire': '',
        'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    json_data = {
        '_token': csrf_token,
        'components': [
            {
                'snapshot': longest_snapshot,
                'updates': {
                    'typeSport': sport_str,
                    'bookingDate': selected_date
                },
                'calls': [],
            },
        ],
    }

    update_response = session.post('https://tennispadelchampfleuri.re/livewire/update', cookies=cookies, headers=headers, json=json_data, timeout = 10)
    try: 
        update_response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        print("Update request failed:", e)
    

    
    ### Retrieve available time slots ###
    scraping_datetime = datetime.today()
    city = 'Saint-Denis'
    club = 'Champ-Fleuri'
    output = []
    
    html_string = update_response.json()['components'][0]['effects']['html']
    html = BeautifulSoup(html_string,"html.parser")
    buttons = html.find_all("button", attrs={"@click": re.compile(r"selectSlot")})

    for btn in buttons:
        click_attr = btn.get("@click")
        match = re.search(r"selectSlot\((.*?)\)", click_attr)
        string_to_parse = match.group(1)
        list_to_parse = string_to_parse.split(', ')
        
        court = list_to_parse[0].strip("'")
        availability_time = datetime.strptime(list_to_parse[1].strip("'"), "%H:%M").time()
        list_of_durations = [int(x) for x in list_to_parse[2].strip("[]").split(",")]
        max_duration = max(list_of_durations)
        
        output.append(schemas.AvailableSlot(
            scraping_datetime= scraping_datetime,
            city= city,
            club= club,
            court= court,
            availability_date= datetime.strptime(selected_date, "%d/%m/%Y"),
            availability_time= availability_time,
            availability_duration= max_duration 
        ))
        
    return output
    
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='test scraping for Champ Fleuri padel club')
    parser.add_argument("--username", type=str, required=True, help="The username of the CF account")
    parser.add_argument("--password", type=str, required=True, help="The password for the CF account")
    parser.add_argument("--date", type=str, required=True, help="The selected date in the format DD/MM/YYYY")
    
    args = parser.parse_args()
    
    available_slots = scrape_champ_fleuri(args.username, args.password, args.date)

    for slot in available_slots:
        print(slot)
    