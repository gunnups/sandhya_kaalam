from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)

    if location and 'timezone' in location.raw:
        return location.raw['timezone']['tzid']
    return 'UTC'

def get_sunrise_sunset_batch(days, lat, lon):
    sunrise_sunset_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&start={days[0]}&end={days[-1]}"
    response_ss = requests.get(sunrise_sunset_url)

    if response_ss.status_code == 200:
        data_ss = response_ss.json()
        for day in days:
            if day in data_ss["results"]:
                sunrise_time = datetime.strptime(data_ss["results"][day]["sunrise"], "%I:%M:%S %p")
                sunset_time = datetime.strptime(data_ss["results"][day]["sunset"], "%I:%M:%S %p")
                yield day, sunrise_time, sunset_time
    else:
        print("Error: Unable to retrieve sunrise-sunset data.")

def create_ics_file(location, start_date, end_date):
    with open(f'{location.replace(", ", "_").replace(" ", "_")}_sandhya_kaalam_{start_date[:4]}.ics', 'w') as ics_file:
        ics_file.write("BEGIN:VCALENDAR\n")
        ics_file.write("VERSION:2.0\n")
        ics_file.write(f"PRODID:-//{location}//NONSGML Calendar//EN\n")

        geolocator = Nominatim(user_agent="my_geocoder")
        location_data = geolocator.geocode(location)

        if location_data:
            lat, lon = location_data.latitude, location_data.longitude
            timezone = get_timezone(lat, lon)

            date_format = "%Y-%m-%d"
            current_date = datetime.strptime(start_date, date_format)
            end_date = datetime.strptime(end_date, date_format)
            days = []

            while current_date <= end_date:
                days.append(current_date.strftime(date_format))
                current_date += timedelta(days=1)

            for day, sunrise_time, sunset_time in get_sunrise_sunset_batch(days, lat, lon):
                ics_file.write("BEGIN:VEVENT\n")
                ics_file.write(f"DTSTART;TZID={timezone}:{day}T{sunrise_time.strftime('%H%M%S')}\n")
                ics_file.write(f"DTEND;TZID={timezone}:{day}T{sunrise_time.strftime('%H%M%S')}\n")
                ics_file.write(f"SUMMARY:Sunrise Event for {day}\n")
                ics_file.write("END:VEVENT\n")

                ics_file.write("BEGIN:VEVENT\n")
                ics_file.write(f"DTSTART;TZID={timezone}:{day}T{sunset_time.strftime('%H%M%S')}\n")
                ics_file.write(f"DTEND;TZID={timezone}:{day}T{sunset_time.strftime('%H%M%S')}\n")
                ics_file.write(f"SUMMARY:Sunset Event for {day}\n")
                ics_file.write("END:VEVENT\n")

        ics_file.write("END:VCALENDAR\n")

# Example usage
create_ics_file("Mason, OH", "2025-01-19", "2025-01-20")