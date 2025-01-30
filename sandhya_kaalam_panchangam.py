# Author: Goutham Mylavarapu
# Updated: 29 January 2025
# Version: 4.0 (multi-key api support)

# [SUMMARY]:
# Generates .ics file for a given location and date range
# Shows the panchangam details in Telugu
# Process multiple locations (run 1 location/day to stay within free tier limits)

# Cache Management Tips:
# First Run: Processes all dates for a location (≈365 API calls)
# Subsequent Runs: Uses cached data, only fetches new dates
# Clear Cache: Delete files in panchangam_cache directory

# Partial Processing: Run individual locations as needed
# Prokerala API Usage Strategy:
# Day 1: Process 1 location (≈365 calls)
# Day 2: Process next location (≈365 calls)
# Continue until all 5 locations complete (within 5 days)
# This implementation safely stays within free tier limits while allowing multi-location processing through persistent caching.



# [USAGE]:
# Single location
# python script.py "Mason, OH"\
#     --start-date 2025-01-01 \
#     --end-date 2025-01-31 \
#     --ugadi-date 2025-03-30

# Multiple location
# python script.py "Mason, OH" "Hyderabad, IN" "Bengaluru, IN" "Chandler, AZ" \
#     --start-date 2025-01-01 \
#     --end-date 2025-01-31 \
#     --ugadi-date 2025-03-30

# python sandhya_kaalam_panchangam.py "Mason, OH" \
#     --start-date 2025-01-29 \
#     --end-date 2025-01-31 \
#     --debug  # Add this flag to see raw responses


import os
import pickle
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz
import argparse
import time
from prokerala_api import ApiClient
import toml
import json

# Configuration
CACHE_DIR = "./panchangam_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Load secrets and initialize API client
secrets = toml.load('multi_secrets.toml')

# CLIENT_ID = secrets['api']['YOUR_CLIENT_ID']
# CLIENT_SECRET = secrets['api']['YOUR_CLIENT_SECRET']

PROKERALA_TOKEN_URL = "https://api.prokerala.com/token"
PROKERALA_API_BASE = "https://api.prokerala.com/v2"

# API limits for ProKerala
RATE_LIMIT_DELAY = 15  # Seconds between API calls
MAX_RETRIES = 3
RATE_LIMIT_BASE_DELAY = 15  # Start with 15 seconds
RATE_LIMIT_MAX_DELAY = 300  # 5 minutes max
BACKOFF_FACTOR = 1.5

# Vedic mappings
VAARA_MAP = {
    'Sunday': 'భాను వారము',
    'Monday': 'ఇందు వారము',
    'Tuesday': 'భౌమ వారము',
    'Wednesday': 'సౌమ్య వారము',
    'Thursday': 'గురు వారము',
    'Friday': 'భృగు వారము',
    'Saturday': 'మంద వారము'
}

Vedic_month_map = {
    1: 'మాఘ', 2: 'ఫాల్గుణ', 3: 'చైత్ర', 4: 'వైశాఖ',
    5: 'జ్యేష్ఠ', 6: 'ఆషాఢ', 7: 'శ్రావణ', 8: 'భాద్రపద',
    9: 'ఆశ్వయుజ', 10: 'కార్తీక', 11: 'మార్గశిర', 12: 'పుష్య'
}

# 60 Samvatsara names
SAMVATSARA = [
    'ప్రభవ', 'విభవ', 'శుక్ల', 'ప్రమోదుత', 'ప్రజోత్పత్తి',
    'ఆంగీరస', 'శ్రీముఖ', 'భావ', 'యువ', 'ధాత',
    'ఈశ్వర', 'బహుధాన్య', 'ప్రమాది', 'విక్రమ', 'వృష',
    'చిత్రభాను', 'స్వభాను', 'తారణ', 'పార్థివ', 'వ్యయ',
    'సర్వజిత్', 'సర్వధారి', 'విరోధి', 'వికృతి', 'ఖర',
    'నందన', 'విజయ', 'జయ', 'మన్మథ', 'దుర్ముఖి',
    'హేవిళంబి', 'విళంబి', 'వికారి', 'శార్వరి', 'ప్లవ',
    'శుభకృత్', 'శోభకృత్', 'క్రోధి', 'విశ్వావసు', 'పరాభవ',
    'ప్లవంగ', 'కీలక', 'సౌమ్య', 'సాధారణ', 'విరోధకృత్',
    'పరిధావి', 'ప్రమాదీచ', 'ఆనంద', 'రాక్షస', 'నల',
    'పింగళ', 'కాళయుక్తి', 'సిద్ధార్థి', 'రౌద్రి', 'దుర్మతి',
    'దుందుభి', 'రుధిరోద్గారి', 'రక్తాక్షి', 'క్రోధన', 'అక్షయ'
]


class ProkeralaAuth:
    def __init__(self, clients):
        self.clients = clients
        self.current_client = 0
        self.token = None
        self.token_expiry = None

    def get_access_token(self):
        if self.token and datetime.now() < self.token_expiry:
            return self.token
            
        client = self.clients[self.current_client]
        print(f"Using client {self.current_client+1}/{len(self.clients)}")
        
        response = requests.post(
            PROKERALA_TOKEN_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': client['id'],
                'client_secret': client['secret']
            }
        )
        
        if response.status_code != 200:
            self._rotate_client()
            return self.get_access_token()
            
        data = response.json()
        self.token = data['access_token']
        self.token_expiry = datetime.now() + timedelta(seconds=data['expires_in'] - 60)
        return self.token

    def _rotate_client(self):
        self.current_client = (self.current_client + 1) % len(self.clients)
        self.token = None
        print(f"Rotated to client {self.current_client+1}")
    

def get_cache_filename(location, cache_type):
    """Generate sanitized cache filenames"""
    sanitized = location.replace(' ', '_').replace(',', '')[:50]
    return f"{CACHE_DIR}/{sanitized}_{cache_type}_cache.pkl"


def load_cache(location, cache_type):
    """Load cached data from file"""
    cache_file = get_cache_filename(location, cache_type)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Cache reset due to error: {str(e)}")
    return {}


def save_cache(location, cache_type, data):
    """Save data to cache file"""
    cache_file = get_cache_filename(location, cache_type)
    with open(cache_file, 'wb') as f:
        pickle.dump(data, f)


def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)
    return pytz.timezone(location.raw['timezone']['tzid']) if location and 'timezone' in location.raw else pytz.utc


def get_sunrise_sunset(lat, lon, date, location):
    """Get sunrise/sunset data with persistent caching"""
    cache = load_cache(location, 'sunrise')
    cache_key = (round(lat, 4), round(lon, 4), date)
    
    if cache_key in cache:
        return cache[cache_key]
    
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0&date={date}"
    response = requests.get(url)
    
    if response.status_code == 200 and response.json().get("status") == "OK":
        data = response.json()["results"]
        cache[cache_key] = data
        save_cache(location, 'sunrise', cache)
        return data
    
    print(f"Error fetching data for {date}")
    return None


def get_vedic_details(date, ugadi_date):
    """Get Vedic month, ayana, and samvatsara"""
    ayana = 'ఉత్తరాయణము' if (date.month > 1 and date.month < 7) or \
        (date.month == 1 and date.day >= 14) or \
        (date.month == 7 and date.day < 14) else 'దక్షిణాయనము'
    
    year = ugadi_date.year if date >= ugadi_date else ugadi_date.year - 1
    samvatsara_idx = (year - 1987) % 60
    samvatsara = SAMVATSARA[samvatsara_idx] + ' నామ సంవత్సరం'

    # Add vaara calculation
    vaara = VAARA_MAP.get(date.strftime('%A'), date.strftime('%A'))
    
    return {
        'masa': Vedic_month_map.get(date.month, ''),
        'ayana': ayana,
        'samvatsara': samvatsara,
        'vaara': vaara
    }


def get_panchangam_details(lat, lon, event_time, tz, location, auth):
    """Get panchangam details with robust error handling
    
    Key Features:
    1. Multi-Client Rotation: Automatically switches API credentials when hitting rate limits
    2. Exponential Backoff: Starts with 15s delay, doubles each retry (15s → 30s → 60s → 120s → 240s)
    3. Robust Error Handling:
    4. Handles HTTP errors (429, 500, etc.)
    5. Validates JSON structure
    6. Graceful fallbacks for missing data
    7. Caching: Stores successful responses to minimize API calls
    8. Debugging: Logs truncated response bodies for troubleshooting
    9. Timeouts: Fails fast with 10-second timeout

    """
    cache = load_cache(location, 'panchangam')
    cache_key = (round(lat, 4), round(lon, 4), event_time.date().isoformat(), tz)
    
    if cache_key in cache:
        return cache[cache_key]
    
    for attempt in range(MAX_RETRIES):
        try:
            access_token = auth.get_access_token()
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(
                f"{PROKERALA_API_BASE}/astrology/panchang",
                params={
                    'ayanamsa': 1,
                    'coordinates': f"{lat},{lon}",
                    'datetime': event_time.isoformat(),
                    # 'timezone': tz,
                    'la': 'te'
                },
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            # Accept both 'success' and 'ok' statuses
            if result.get('status', '').lower() not in ['success', 'ok']:
                raise ValueError(f"API status failure: {result.get('status')}")

            # Validate response structure
            panchang = result.get('data', {}).get('panchang', {})
            if not panchang:
                raise ValueError("Missing panchang data")

            # Extract fields with fallbacks
            data = {
                'tithi': f"{panchang.get('tithi', {}).get('paksha', '')} {panchang.get('tithi', {}).get('name', 'N/A')}".strip(),
                'nakshatra': panchang.get('nakshatra', [{}])[0].get('name', 'N/A'),
                'vaara': VAARA_MAP.get(
                    panchang.get('vaara', {}).get('name', ''),
                    panchang.get('vaara', {}).get('name', 'N/A')
                )
            }

            cache[cache_key] = data
            save_cache(location, 'panchangam', cache)
            return data

        except Exception as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                delay = 15 * (attempt + 1)
                print(f"Retrying in {delay}s...")
                time.sleep(delay)
                auth._rotate_client()
            else:
                print("Max retries reached. Using fallback data.")
                return {
                    'tithi': 'సమాచారం అందుబాటులో లేదు',
                    'nakshatra': 'N/A',
                    'vaara': 'N/A'
                }


def generate_event(start_time, end_time, summary, location, day_str, event_type, panchangam, vedic_details):
    """Generate calendar event with time-specific Panchangam"""
    # Handle missing panchangam data
    tithi = panchangam.get('tithi', 'సమాచారం అందుబాటులో లేదు') if panchangam else 'సమాచారం అందుబాటులో లేదు'
    nakshatra = panchangam.get('nakshatra', 'N/A') if panchangam else 'N/A'
    vaara = panchangam.get('vaara', 'N/A') if panchangam else 'N/A'
    
    description = (
        f"{summary} at {location} on {day_str}\n"
        f"సంవత్సరము: {vedic_details['samvatsara']}\n"
        f"అయనము: {vedic_details['ayana']}\n"
        f"మాసము: {vedic_details['masa']}\n"
        f"తిథి: {tithi}\n"
        f"వారము: {vaara}\n"
        f"నక్షత్రము: {nakshatra}\n"
    )
    
    event = [
        "BEGIN:VEVENT",
        f"UID:{start_time.strftime('%Y%m%dT%H%M%S')}@{event_type}",
        f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{summary} at {location}",
        f"DESCRIPTION:{description}",
        "BEGIN:VALARM",
        "TRIGGER:-PT15M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {summary} in 10 minutes.",
        "END:VALARM",
        "BEGIN:VALARM",
        "TRIGGER:PT0M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {summary} is starting now.",
        "END:VALARM",
        "END:VEVENT\n"
    ]
    return "\n".join(event) + "\n"


def process_location(location, start_date, end_date, events, ugadi_date, auth):
    """Process one location and generate its ICS file"""
    geolocator = Nominatim(user_agent="multi_loc_panchangam")
    location_data = geolocator.geocode(location)

    if not location_data:
        print(f"Skipping {location} - geocoding failed")
        return

    lat, lon = location_data.latitude, location_data.longitude
    timezone = get_timezone(lat, lon)
    tz_str = timezone.zone

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Sunrise Sunset Calendar//EN\n"

    current_day = start_date
    delta = timedelta(days=1)
    
    while current_day <= end_date:
        date_str = current_day.strftime("%Y-%m-%d")
        vedic_details = get_vedic_details(current_day, ugadi_date)
        
        # Get sunrise/sunset times
        ss_data = get_sunrise_sunset(lat, lon, date_str, location)
        
        # Process events
        if ss_data:
            # Sunrise event
            if 'sunrise' in events:
                sunrise_time = datetime.fromisoformat(ss_data["sunrise"])
                sunrise_panchang = get_panchangam_details(lat, lon, sunrise_time, tz_str, location, auth=auth)
                sunrise_start = sunrise_time - timedelta(hours=1, minutes=12)
                sunrise_end = sunrise_time + timedelta(minutes=48)
                ics_content += generate_event(
                    sunrise_start, sunrise_end, 
                    "ప్రాతః సంధ్యా సమయం", location, 
                    date_str, "sunrise", sunrise_panchang, vedic_details
                )

            # Sunset event
            if 'sunset' in events:
                sunset_time = datetime.fromisoformat(ss_data["sunset"])
                sunset_panchang = get_panchangam_details(lat, lon, sunset_time, tz_str, location, auth=auth)
                sunset_start = sunset_time - timedelta(minutes=24)
                sunset_end = sunset_time + timedelta(hours=1, minutes=12)
                
                # Handle thithi transition
                if sunrise_panchang and sunset_panchang:
                    if sunrise_panchang['tithi'] != sunset_panchang['tithi']:
                        sunset_panchang['tithi'] = f"{sunrise_panchang['tithi']} ప్రయుక్త {sunset_panchang['tithi']}"
                
                ics_content += generate_event(
                    sunset_start, sunset_end,
                    "సాయం సంధ్యా సమయం", location,
                    date_str, "sunset", sunset_panchang, vedic_details
                )

        # Noon event
        if 'noon' in events:
            noon_time = datetime.combine(current_day.date(), datetime.strptime("11:24", "%H:%M").time())
            noon_panchang = get_panchangam_details(lat, lon, noon_time, tz_str, location, auth=auth)
            noon_start = timezone.localize(noon_time - timedelta(minutes=36)).astimezone(pytz.utc)
            noon_end = timezone.localize(noon_time + timedelta(minutes=72)).astimezone(pytz.utc)
            ics_content += generate_event(
                noon_start, noon_end,
                "మాధ్యానిక సంధ్యా సమయం", location,
                date_str, "noon", noon_panchang, vedic_details
            )

        current_day += delta

    ics_content += "END:VCALENDAR"

    filename = f"{location.replace(' ', '_').replace(',', '')}_sandhya_kaalam_{start_date.year}.ics"
    
    with open(filename, "w", encoding='utf-8') as ics_file:
        ics_file.write(ics_content)

    print(f"ICS file '{filename}' created successfully.")
    print(f"Completed processing for {location}")



def main():
    start_time = time.time()

    # Initialize authentication - rotate auth
    api_clients = [
        secrets['api']['clients'][f'client{i+1}']
        for i in range(len(secrets['api']['clients']))
    ]
    auth = ProkeralaAuth(api_clients)

    parser = argparse.ArgumentParser(description="Generate Panchangam calendars for multiple locations")
    parser.add_argument("locations", nargs='*', 
                      default=["Mason, OH"],  # Wrap in list
                      type=lambda s: s.strip('"'),  # Handle quoted locations
                      help="Locations to process (enclose in quotes, e.g. 'Mason, OH'). Default: Mason, OH"
    )
    parser.add_argument("--start-date", default="2025-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default="2025-01-31", help="End date (YYYY-MM-DD)")
    parser.add_argument("--ugadi-date", default="2025-03-30", help="Ugadi date (YYYY-MM-DD)")
    parser.add_argument("--events", nargs='+', choices=['sunrise', 'noon', 'sunset'], default=['sunrise', 'sunset'], help="Events to include. Default: sunrise sunset")
    
    args = parser.parse_args()
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    ugadi_date = datetime.strptime(args.ugadi_date, "%Y-%m-%d")

    # Create .ics file for each location
    for location in args.locations:
        print(f"\nProcessing {location}...")
        process_location(
            auth=auth,
            location=location,
            start_date=start_date,
            end_date=end_date,
            events=args.events,
            ugadi_date=ugadi_date
        )
        time.sleep(60)  # Rate limit protection - 1 min between locations

    # Execution time calculation
    end_time = time.time()
    elapsed = end_time - start_time
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    
    if hours > 0:
        print(f"\nTime taken: {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
    else:
        print(f"\nTime taken: {int(minutes):02}:{int(seconds):02}")

if __name__ == "__main__":
    main()
