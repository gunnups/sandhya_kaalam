#!/usr/bin/env python

from prokerala_api import ApiClient
from geopy.geocoders import Nominatim
import pytz
import argparse
import json
import toml

# Load the secrets from secrets.toml file
secrets = toml.load('secrets.toml')

def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)
    return pytz.timezone(location.raw['timezone']['tzid']) if location and 'timezone' in location.raw else pytz.utc

def panchangam(location):
    client = ApiClient(secrets['api']['YOUR_CLIENT_ID'], secrets['api']['YOUR_CLIENT_SECRET'])

    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if not location_data:
        print("Error: Unable to geocode the location.")
        return

    lat, lon = location_data.latitude, location_data.longitude
    timezone = get_timezone(lat, lon)
    local_tz = timezone

    result = client.get('v2/astrology/panchang', {  # /advanced
        'ayanamsa': 1,
        'coordinates': '23.1765,75.7885',
        'datetime': '2025-01-29T12:31:14+00:00',
        'la': 'te'  # Telugu, if none specified, it will be English
    })
    print(json.dumps(result, indent=4))

if __name__ == '__main__':
    panchangam("Mason, OH")
