from ics import Calendar, Event
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests

def get_sunrise_sunset(date, address):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(address)

    if location:
        lat, lon = location.latitude, location.longitude
        sunrise_sunset_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date}"
        response_ss = requests.get(sunrise_sunset_url)

        if response_ss.status_code == 200:
            data_ss = response_ss.json()
            if data_ss["status"] == "OK":
                results = data_ss["results"]
                sunrise = results.get("sunrise", "Not available")
                sunset = results.get("sunset", "Not available")
                return sunrise, sunset
    return None, None

def get_ical_sunrise_sunset(location, start_date, end_date):
    cal = Calendar()

    date_format = "%Y-%m-%d"
    current_date = datetime.strptime(start_date, date_format)
    end_date = datetime.strptime(end_date, date_format)

    while current_date <= end_date:
        date_str = current_date.strftime(date_format)
        sunrise, sunset = get_sunrise_sunset(date_str, location)

        if sunrise is not None and sunset is not None:
            sunrise_time = datetime.strptime(sunrise, "%I:%M:%S %p")
            sunset_time = datetime.strptime(sunset, "%I:%M:%S %p")

            for event_time, event_name in [(sunrise_time, "Sunrise"), (sunset_time, "Sunset")]:
                event = Event()
                event.name = f"{event_name} Meeting"
                event.begin = event_time - timedelta(minutes=48)
                event.end = event_time + timedelta(minutes=24)
                cal.events.add(event)

        current_date += timedelta(days=1)

    file_name = f"{location.replace(', ','_').replace(' ','_')}_{start_date}_{end_date}.ics"
    with open(file_name, 'w') as file:
        file.writelines(cal)

# Example usage
get_ical_sunrise_sunset("Mason, OH", "2025-01-19", "2025-01-31")