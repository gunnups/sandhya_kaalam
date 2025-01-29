
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def get_lat_long(address):
    geolocator = Nominatim(user_agent="my_geocoder")

    try:
        location = geolocator.geocode(address)

        if location:
            return location.latitude, location.longitude
        else:
            return "Location not found"

    except GeocoderTimedOut:
        return "Geocoding service timed out"

# Example usage
location = input("Enter a location: ")
lat_long = get_lat_long(location)
print(lat_long)

# import requests

# def get_lat_long(address):
#     base_url = "https://nominatim.openstreetmap.org/search"
#     params = {
#         "q": address,
#         "format": "json"
#     }

#     response = requests.get(base_url, params=params)

#     print(response.status_code)

#     if response.status_code == 200:
#         try:
#             data = response.json()
#             if data:
#                 latitude = data[0]["lat"]
#                 longitude = data[0]["lon"]

#                 return latitude, longitude
#         except (IndexError, KeyError):
#             return "Latitude and longitude not found for this address"
#     else:
#         return "Error fetching data"

# # Example usage
# location = input("Enter a location: ")
# lat_long = get_lat_long(location)
# print(lat_long)