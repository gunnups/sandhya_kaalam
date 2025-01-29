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

def get_sunrise_sunset(lat, lon, date):
    sunrise_sunset_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0&date={date}"
    response_ss = requests.get(sunrise_sunset_url)

    if response_ss.status_code == 200:
        data_ss = response_ss.json()
        if data_ss["status"] == "OK":
            sunrise_time = datetime.fromisoformat(data_ss["results"]["sunrise"])
            sunset_time = datetime.fromisoformat(data_ss["results"]["sunset"])
            return sunrise_time, sunset_time
    else:
        print(f"Error: Unable to retrieve sunrise-sunset data for {date}.")
    return None, None

def create_ics_file(location, start_date, end_date):
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

        ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Sunrise Sunset Calendar//EN\n"

        for day in days:
            sunrise_time, sunset_time = get_sunrise_sunset(lat, lon, day)
            if sunrise_time and sunset_time:
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
                ics_content += f"SUMMARY:Sunrise at {location}\n"
                ics_content += f"DESCRIPTION:Sunrise event at {location} on {day}.\n"
                # Add first alert (15 minutes before)
                ics_content += "BEGIN:VALARM\n"
                ics_content += "TRIGGER:-PT15M\n"
                ics_content += "ACTION:DISPLAY\n"
                ics_content += "DESCRIPTION:Reminder: Sunrise event in 15 minutes.\n"
                ics_content += "END:VALARM\n"
                # Add second alert (at the time of the event)
                ics_content += "BEGIN:VALARM\n"
                ics_content += "TRIGGER:PT0M\n"
                ics_content += "ACTION:DISPLAY\n"
                ics_content += "DESCRIPTION:Reminder: Sunrise event is starting now.\n"
                ics_content += "END:VALARM\n"
                ics_content += "END:VEVENT\n"

                # Add sunset event
                ics_content += "BEGIN:VEVENT\n"
                ics_content += f"UID:{sunset_start.strftime('%Y%m%dT%H%M%S')}@sunset\n"
                ics_content += f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}\n"
                ics_content += f"DTSTART:{sunset_start.strftime('%Y%m%dT%H%M%SZ')}\n"
                ics_content += f"DTEND:{sunset_end.strftime('%Y%m%dT%H%M%SZ')}\n"
                ics_content += f"SUMMARY:Sunset at {location}\n"
                ics_content += f"DESCRIPTION:Sunset event at {location} on {day}.\n"
                # Add first alert (15 minutes before)
                ics_content += "BEGIN:VALARM\n"
                ics_content += "TRIGGER:-PT15M\n"
                ics_content += "ACTION:DISPLAY\n"
                ics_content += "DESCRIPTION:Reminder: Sunset event in 15 minutes.\n"
                ics_content += "END:VALARM\n"
                # Add second alert (at the time of the event)
                ics_content += "BEGIN:VALARM\n"
                ics_content += "TRIGGER:PT0M\n"
                ics_content += "ACTION:DISPLAY\n"
                ics_content += "DESCRIPTION:Reminder: Sunset event is starting now.\n"
                ics_content += "END:VALARM\n"
                ics_content += "END:VEVENT\n"

        ics_content += "END:VCALENDAR"

        # Create filename with location name
        filename = f"{location.replace(' ', '_').replace(',', '')}_sandhya_kaalam.ics"

        # Write to .ics file
        with open(filename, "w") as ics_file:
            ics_file.write(ics_content)

        print(f"ICS file '{filename}' created successfully.")
    else:
        print("Error: Unable to geocode the location.")

# Example usage
create_ics_file("Mason, OH", "2025-01-01", "2025-12-31")