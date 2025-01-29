from geopy.geocoders import Nominatim
import requests


def get_sunrise_sunset(date, address):
    # Initialize the geolocator using Nominatim
    geolocator = Nominatim(user_agent="my_geocoder")

    try:
        location = geolocator.geocode(address)

        if location:
            lat = location.latitude
            lon = location.longitude

            print(f'Location: {address}, latitude: {lat}, longitude: {lon}')

            sunrise_sunset_url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date={date}"
            response_ss = requests.get(sunrise_sunset_url)

            if response_ss.status_code == 200:
                data_ss = response_ss.json()

                if data_ss["status"] == "OK":
                    results = data_ss["results"]
                    sunrise = results.get("sunrise", "Not available")
                    sunset = results.get("sunset", "Not available")

                    return {"sunrise": sunrise, "sunset": sunset}
    except Exception as e:
        return "Error fetching data: " + str(e)

# Example usage
date = "2025-01-18"
address = input("Enter a location: ")
sunrise_sunset_info = get_sunrise_sunset(date, address)
print(sunrise_sunset_info)