# Author: Goutham Mylavarapu
# Updated: 28 January 2025
# Version: 2.0 (With Persistent Caching)

# Summary:
# Generates .ics file for a given location and date range. Takes about 2 minutes


# [USAGE]:
# python sandhya_kaalam.py "Mason, OH" --start-date 2025-01-01 --end-date 2025-12-31 --events sunrise sunset


from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz
import argparse
import time  # <-- NEW IMPORT

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

def create_ics_file(location, start_date, end_date, events):
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if not location_data:
        print("Error: Unable to geocode the location.")
        return

    lat, lon = location_data.latitude, location_data.longitude
    timezone = get_timezone(lat, lon)
    local_tz = timezone

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Sunrise Sunset Calendar//EN\n"

    if 'sunrise' in events or 'sunset' in events:
        current_day = start_date
        delta = timedelta(days=1)
        while current_day <= end_date:
            date_str = current_day.strftime("%Y-%m-%d")
            data = get_sunrise_sunset(lat, lon, date_str)
            if data:
                sunrise_time = datetime.fromisoformat(data["sunrise"])
                sunset_time = datetime.fromisoformat(data["sunset"])

                if 'sunrise' in events:
                    sunrise_start = sunrise_time - timedelta(hours=1, minutes=12)
                    sunrise_end = sunrise_time + timedelta(minutes=48)
                    ics_content += generate_event(
                        sunrise_start, sunrise_end, "ప్రాతః సంధ్యా సమయం", location, 
                        date_str, "sunrise"
                    )

                if 'sunset' in events:
                    sunset_start = sunset_time - timedelta(minutes=24)
                    sunset_end = sunset_time + timedelta(hours=1, minutes=12)
                    ics_content += generate_event(
                        sunset_start, sunset_end, "సాయం సంధ్యా సమయం", location,
                        date_str, "sunset"
                    )
            current_day += delta

    if 'noon' in events:
        current_day = start_date.date()
        end_day = end_date.date()
        delta = timedelta(days=1)
        while current_day <= end_day:
            noon_start_naive = datetime.combine(current_day, datetime.strptime("10:48", "%H:%M").time())
            noon_end_naive = datetime.combine(current_day, datetime.strptime("12:00", "%H:%M").time())
            noon_start = local_tz.localize(noon_start_naive).astimezone(pytz.utc)
            noon_end = local_tz.localize(noon_end_naive).astimezone(pytz.utc)
            ics_content += generate_event(
                noon_start, noon_end, "మాధ్యానిక సంధ్యా సమయం", location, current_day.strftime("%Y-%m-%d"), "noon"
            )
            current_day += delta

    ics_content += "END:VCALENDAR"

    filename = f"{location.replace(' ', '_').replace(',', '')}_sandhya_kaalam_{start_date.year}.ics"
    with open(filename, "w") as ics_file:
        ics_file.write(ics_content)
    print(f"ICS file '{filename}' created successfully.")

def generate_event(start_time, end_time, summary, location, day_str, event_type):
    event = [
        "BEGIN:VEVENT",
        f"UID:{start_time.strftime('%Y%m%dT%H%M%S')}@{event_type}",
        f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{summary} at {location}",
        f"DESCRIPTION:{summary} at {location} on {day_str}.",
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

def main():
    start_time = time.time()  # <-- TIMING STARTS
    
    parser = argparse.ArgumentParser(description="Generate a calendar of sandhya kaalam events.")
    parser.add_argument("location", type=str, nargs='?', default="Mason, OH", 
                      help="Location (e.g., 'Mason, OH'). Default: Mason, OH")
    parser.add_argument("--start-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"), 
                      default=datetime(2025, 1, 1), help="Start date (YYYY-MM-DD). Default: 2025-01-01")
    parser.add_argument("--end-date", type=lambda s: datetime.strptime(s, "%Y-%m-%d"), 
                      default=datetime(2025, 12, 31), help="End date (YYYY-MM-DD). Default: 2025-12-31")
    parser.add_argument("--events", nargs='+', choices=['sunrise', 'noon', 'sunset'], 
                      default=['sunrise', 'sunset'], help="Events to include. Default: sunrise sunset")
    args = parser.parse_args()

    create_ics_file(args.location.strip('"'), args.start_date, args.end_date, args.events)
    
    # Calculate and print execution time
    end_time = time.time()  # <-- TIMING ENDS
    elapsed = end_time - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    if hours > 0:
        print(f"\nTime taken to execute: {hours}:{minutes:02d}:{seconds:02d}")
    else:
        print(f"\nTime taken to execute: {minutes}:{seconds:02d}")

if __name__ == "__main__":
    main()