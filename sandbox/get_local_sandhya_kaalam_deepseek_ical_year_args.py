# python *.py "Mason, OH" 2025

from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz
import argparse

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)

    if location and 'timezone' in location.raw:
        return pytz.timezone(location.raw['timezone']['tzid'])
    return pytz.utc

def get_sunrise_sunset_month(lat, lon, year, month):
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{31 if month in [1, 3, 5, 7, 8, 10, 12] else 30 if month != 2 else 28}"
    sunrise_sunset_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0&start={start_date}&end={end_date}"
    response_ss = requests.get(sunrise_sunset_url)

    if response_ss.status_code == 200:
        data_ss = response_ss.json()
        if data_ss["status"] == "OK" and f"{year}-{month:02d}" in data_ss["results"]:
            return data_ss["results"][f"{year}-{month:02d}"]
    else:
        print(f"Error: Unable to retrieve sunrise-sunset data for {year}-{month:02d}.")
    return None


def create_ics_file(location, year):
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if location_data:
        lat, lon = location_data.latitude, location_data.longitude
        timezone = get_timezone(lat, lon).zone

        ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Sunrise Sunset Calendar//EN\n"

        for month in range(1, 13):
            results = get_sunrise_sunset_month(lat, lon, year, month)
            if results:
                for day, data in results.items():
                    sunrise_time = datetime.fromisoformat(data["sunrise"])
                    sunset_time = datetime.fromisoformat(data["sunset"])

                    # Adjust sunrise event times
                    sunrise_start = sunrise_time - timedelta(hours=1, minutes=12)
                    sunrise_end = sunrise_time + timedelta(minutes=48)

                    # Adjust sunset event times
                    sunset_start = sunset_time - timedelta(minutes=24)
                    sunset_end = sunset_time + timedelta(hours=1, minutes=12)

                    # Add sunrise event
                    ics_content += "BEGIN:VEVENT\n"
                    ics_content += f"UID:{sunrise_start.strftime('%Y%m%dT%H%M%S')}@sunrise\n"
                    ics_content += f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"DTSTART:{sunrise_start.strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"DTEND:{sunrise_end.strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"SUMMARY:ప్రాతః సంధ్యా సమయం at {location}\n"
                    ics_content += f"DESCRIPTION:ప్రాతః సంధ్యా సమయం at {location} on {day}.\n"
                    # Add first alert (15 minutes before)
                    ics_content += "BEGIN:VALARM\n"
                    ics_content += "TRIGGER:-PT15M\n"
                    ics_content += "ACTION:DISPLAY\n"
                    ics_content += "DESCRIPTION:Reminder: ప్రాతః సంధ్యా సమయం  in 15 minutes.\n"
                    ics_content += "END:VALARM\n"
                    # Add second alert (at the time of the event)
                    ics_content += "BEGIN:VALARM\n"
                    ics_content += "TRIGGER:PT0M\n"
                    ics_content += "ACTION:DISPLAY\n"
                    ics_content += "DESCRIPTION:Reminder: ప్రాతః సంధ్యా సమయం is starting now.\n"
                    ics_content += "END:VALARM\n"
                    ics_content += "END:VEVENT\n"

                    # Add sunset event
                    ics_content += "BEGIN:VEVENT\n"
                    ics_content += f"UID:{sunset_start.strftime('%Y%m%dT%H%M%S')}@sunset\n"
                    ics_content += f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"DTSTART:{sunset_start.strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"DTEND:{sunset_end.strftime('%Y%m%dT%H%M%SZ')}\n"
                    ics_content += f"SUMMARY:సాయం సంధ్యా సమయం at {location}\n"
                    ics_content += f"DESCRIPTION:సాయం సంధ్యా సమయం at {location} on {day}.\n"
                    # Add first alert (15 minutes before)
                    ics_content += "BEGIN:VALARM\n"
                    ics_content += "TRIGGER:-PT15M\n"
                    ics_content += "ACTION:DISPLAY\n"
                    ics_content += "DESCRIPTION:Reminder: సాయం సంధ్యా సమయం  in 15 minutes.\n"
                    ics_content += "END:VALARM\n"
                    # Add second alert (at the time of the event)
                    ics_content += "BEGIN:VALARM\n"
                    ics_content += "TRIGGER:PT0M\n"
                    ics_content += "ACTION:DISPLAY\n"
                    ics_content += "DESCRIPTION:Reminder: సాయం సంధ్యా సమయం  is starting now.\n"
                    ics_content += "END:VALARM\n"
                    ics_content += "END:VEVENT\n"

        ics_content += "END:VCALENDAR"

        # Create filename with location name
        filename = f"{location.replace(' ', '_').replace(',', '')}_sandhya_kaalam_{year}.ics"

        # Write to .ics file
        with open(filename, "w") as ics_file:
            ics_file.write(ics_content)

        print(f"ICS file '{filename}' created successfully.")
    else:
        print("Error: Unable to geocode the location.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate a calendar of sunrise and sunset events for a given location and year.")
    parser.add_argument("location", type=str, help="The location for which to generate the calendar (e.g., 'Mason, OH').")
    parser.add_argument("year", type=int, help="The year for which to generate the calendar (e.g., 2025).")
    args = parser.parse_args()

    # Call the function with the provided arguments
    create_ics_file(args.location, args.year)

if __name__ == "__main__":
    main()