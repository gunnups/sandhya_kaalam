#!/usr/bin/env python

from prokerala_api import ApiClient
from geopy.geocoders import Nominatim
import pytz
import argparse
import json
import toml

# Load the secrets from secrets.toml file
secrets = toml.load('secrets.toml')

# Telugu weekday mapping
VAARA_MAP = {
    'Sunday': 'ఆదివారం',
    'Monday': 'సోమవారం',
    'Tuesday': 'మంగళవారం',
    'Wednesday': 'బుధవారం',
    'Thursday': 'గురువారం',
    'Friday': 'శుక్రవారం',
    'Saturday': 'శనివారం'
}

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

    result = client.get('v2/astrology/panchang', {
        'ayanamsa': 1,
        'coordinates': f"{lat},{lon}",  # Use actual coordinates
        'datetime': '2025-01-29T12:31:14+00:00',
        'la': 'te'
    })

    panchang = result.get('data', {})
    
    # Extract tithi information
    tithi = panchang.get('tithi', [{}])
    tithi_str = f"{tithi[0].get('paksha', '')} {tithi[0].get('name', 'N/A')}".strip() if tithi else 'N/A'

    # Extract nakshatra information
    nakshatra = panchang.get('nakshatra', [{}])
    nakshatra_str = nakshatra[0].get('name', 'N/A') if nakshatra else 'N/A'

    # Get Telugu vaara name
    vaara_en = panchang.get('vaara', 'N/A')
    vaara_te = VAARA_MAP.get(vaara_en, vaara_en)

    # Format output in Telugu
    output = f"""
    పంచాంగ వివరాలు ({location}):
    ----------------------------
    తిథి    : {tithi_str}
    నక్షత్రం : {nakshatra_str}
    వారం    : {vaara_te}
    సూర్యోదయం : {panchang.get('sunrise', 'N/A')}
    సూర్యాస్తమయం : {panchang.get('sunset', 'N/A')}
    """

    print(output)

if __name__ == '__main__':
    panchangam("Mason, OH")