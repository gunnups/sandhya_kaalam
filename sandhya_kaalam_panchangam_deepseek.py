# Author: Goutham Mylavarapu
# Updated: 29 January 2025
# Version: 2.0 [panchangam, 60 years in Telugu]

# [USAGE]: python *t.py "Mason, OH" \
    # --start-date 2025-01-01 \
    # --end-date 2025-01-07 \
    # --ugadi-date 2025-04-12 \
    # --events sunrise noon sunset

# Summary:
# Generates .ics file for a given location and date range
# Shows the panchangam details in Telugu


from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz
import argparse
import time
from prokerala_api import ApiClient
import toml

# Load the secrets from secrets.toml file
secrets = toml.load('secrets.toml')

# Configure Prokerala API credentials
CLIENT_ID = secrets['api']['YOUR_CLIENT_ID']
CLIENT_SECRET = secrets['api']['YOUR_CLIENT_SECRET']

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

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)
    return pytz.timezone(location.raw['timezone']['tzid']) if location and 'timezone' in location.raw else pytz.utc

def get_sunrise_sunset(lat, lon, date):
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0&date={date}"
    response = requests.get(url)
    if response.status_code == 200 and response.json()["status"] == "OK":
        return response.json()["results"]
    print(f"Error fetching data for {date}")
    return None

def get_vedic_details(date, ugadi_date):
    """Get Vedic month, ayana, and samvatsara"""
    # Uttarayana calculation
    ayana = 'ఉత్తరాయణము' if (date.month > 1 and date.month < 7) or \
        (date.month == 1 and date.day >= 14) or \
        (date.month == 7 and date.day < 14) else 'దక్షిణాయనము'
    
    # Samvatsara calculation
    year = ugadi_date.year if date >= ugadi_date else ugadi_date.year - 1
    samvatsara_idx = (year - 1987) % 60  # Adjust base year as needed
    samvatsara = SAMVATSARA[samvatsara_idx] + ' నామ సంవత్సరం'
    
    return {
        'masa': Vedic_month_map.get(date.month, ''),
        'ayana': ayana,
        'samvatsara': samvatsara
    }

def get_panchangam_details(lat, lon, event_time, tz):
    """Fetch Panchangam details for specific event time"""
    client = ApiClient(CLIENT_ID, CLIENT_SECRET)
    
    try:
        result = client.get('v2/astrology/panchang', {
            'ayanamsa': 1,
            'coordinates': f"{lat},{lon}",
            'datetime': event_time.isoformat(),
            'timezone': tz,
            'la': 'te'
        })
        
        panchang = result['data']['panchang']
        return {
            'tithi': f"{panchang['tithi']['paksha']} {panchang['tithi']['name']}",
            'nakshatra': panchang['nakshatra'][0]['name'],
            'vaara': VAARA_MAP.get(panchang['vaara']['name'], panchang['vaara']['name'])
        }
    except Exception as e:
        print(f"Error fetching Panchangam: {str(e)}")
        return None

def generate_event(start_time, end_time, summary, location, day_str, event_type, panchangam, vedic_details):
    """Generate calendar event with time-specific Panchangam"""
    if panchangam:
        tithi_display = panchangam['tithi']
    else:
        tithi_display = "సమాచారం అందుబాటులో లేదు"
        
    description = (
        f"{summary} {location} వద్ద {day_str}న\n"
        f"సంవత్సరము: {vedic_details['samvatsara']}\n"
        f"అయనము: {vedic_details['ayana']}\n"
        f"మాసము: {vedic_details['masa']}\n"
        f"తిథి: {tithi_display}\n"
        f"వారము: {vedic_details['vaara']}\n"
        f"నక్షత్రము: {panchangam['nakshatra'] if panchangam else 'N/A'}\n"
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
        f"DESCRIPTION:Reminder: {summary} in 15 minutes.",
        "END:VALARM",
        "BEGIN:VALARM",
        "TRIGGER:PT0M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {summary} is starting now.",
        "END:VALARM",
        "END:VEVENT\n"
    ]
    return "\n".join(event) + "\n"

def create_ics_file(location, start_date, end_date, events, ugadi_date):
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if not location_data:
        print("Error: Unable to geocode the location.")
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
        ss_data = get_sunrise_sunset(lat, lon, date_str)
        
        # Process events
        if ss_data:
            # Sunrise event
            if 'sunrise' in events:
                sunrise_time = datetime.fromisoformat(ss_data["sunrise"])
                sunrise_panchang = get_panchangam_details(lat, lon, sunrise_time, tz_str)
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
                sunset_panchang = get_panchangam_details(lat, lon, sunset_time, tz_str)
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
            noon_panchang = get_panchangam_details(lat, lon, noon_time, tz_str)
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
    with open(filename, "w") as ics_file:
        ics_file.write(ics_content)
    print(f"ICS file '{filename}' created successfully.")

def main():
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description="Generate a calendar of sandhya kaalam events.")
    parser.add_argument("location", type=str, nargs='?', default="Mason, OH", 
                      help="Location (e.g., 'Mason, OH'). Default: Mason, OH")
    parser.add_argument("--start-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"), 
                      default=datetime(2025, 1, 1), help="Start date (YYYY-MM-DD). Default: 2025-01-01")
    parser.add_argument("--end-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"), 
                      default=datetime(2025, 12, 31), help="End date (YYYY-MM-DD). Default: 2025-12-31")
    parser.add_argument("--ugadi-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
                      default=datetime(2025, 3, 30), help="Ugadi date (YYYY-MM-DD). Default: 2025-03-30")
    parser.add_argument("--events", nargs='+', choices=['sunrise', 'noon', 'sunset'], 
                      default=['sunrise', 'sunset'], help="Events to include. Default: sunrise sunset")
    args = parser.parse_args()

    create_ics_file(args.location.strip('"'), args.start_date, args.end_date, args.events, args.ugadi_date)
    
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
