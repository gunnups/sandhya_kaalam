from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)

    if location and 'timezone' in location.raw:
        return pytz.timezone(location.raw['timezone']['tzid'])
    return pytz.utc

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

def create_google_calendar_link(location, start_date, end_date):
    link = "https://calendar.google.com/calendar/render?action=TEMPLATE"

    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if location_data:
        lat, lon = location_data.latitude, location_data.longitude
        timezone = get_timezone(lat, lon).zone

        date_format = "%Y-%m-%d"
        current_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)
        days = []

        while current_date <= end_date:
            days.append(current_date.strftime(date_format))
            current_date += timedelta(days=1)

        for day, sunrise_time, sunset_time in get_sunrise_sunset_batch(days, lat, lon):
            sunrise_datetime = datetime.strptime(f"{day} {sunrise_time.strftime('%H:%M:%S')}", "%Y-%m-%d %H:%M:%S").astimezone(pytz.utc)
            sunset_datetime = datetime.strptime(f"{day} {sunset_time.strftime('%H:%M:%S')}", "%Y-%m-%d %H:%M:%S").astimezone(pytz.utc)

            link += f"&dates={sunrise_datetime.strftime('%Y%m%dT%H%M%S')}/{sunrise_datetime.strftime('%Y%m%dT%H%M%S')}"
            link += f"&dates={sunset_datetime.strftime('%Y%m%dT%H%M%S')}/{sunset_datetime.strftime('%Y%m%dT%H%M%S')}"
            link += f"&location={location.replace(' ', '+')}"
            link += f"&details=Sunrise+and+Sunset+Events+for+{day}\n"

    print("Google Calendar Invite Link:")
    print(link)

# Example usage
create_google_calendar_link("Mason, OH", "2025-01-19", "2025-01-20")