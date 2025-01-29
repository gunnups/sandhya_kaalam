from ics import Calendar, Event
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)

    if location and 'timezone' in location.raw:
        timezone = pytz.timezone(location.raw['timezone']['tzid'])
        return timezone
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

def get_ical_sunrise_sunset(location, start_date, end_date):
    cal = Calendar()
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if location_data:
        lat, lon = location_data.latitude, location_data.longitude
        timezone = get_timezone(lat, lon)

        print(f'latitude: {lat}, longitude: {lon}')

        # Define the Eastern Standard Time (EST) timezone for Mason, OH
        est_timezone = pytz.timezone('America/New_York')  # EST timezone

        date_format = "%Y-%m-%d"
        current_date = datetime.strptime(start_date, date_format)
        end_date = datetime.strptime(end_date, date_format)
        days = []

        while current_date <= end_date:
            days.append(current_date.strftime(date_format))
            current_date += timedelta(days=1)

        print(f'# of days: {days}')

        for day, sunrise_time, sunset_time in get_sunrise_sunset_batch(days, lat, lon):
            for event_time, event_name in [(sunrise_time, "praatah:"), (sunset_time, "saayam")]:
                event = Event()
                event.name = f"{event_name} sandhya samayam"

                # Convert event time to EST timezone
                event_time_est = event_time.replace(tzinfo=pytz.utc).astimezone(est_timezone)
                print(f"event_time_est {event_time_est}")

                event_begin = event_time_est - timedelta(minutes=48)
                event_end = event_time_est + timedelta(minutes=24)
                event.begin = event_begin
                event.end = event_end

                # Print event start and end dates for debugging
                print(f"{event_name} Meeting Start: {event_begin}")
                print(f"{event_name} Meeting End: {event_end}")

                cal.events.add(event)    

                # Print event begin and end dates for the last event added
                print(f"Last Event Start: {event_begin}")
                print(f"Last Event End: {event_end}")   


        file_name = f"{location.replace(', ','_').replace(' ','_')}_sandhya_kaalam_{start_date[:4]}.ics"

        cal_content = cal.serialize()  # cal_content = str(cal)
        with open(file_name, 'w') as file:
            file.writelines(cal_content)

# Example usage
get_ical_sunrise_sunset("Mason, OH", "2025-01-19", "2025-01-20")