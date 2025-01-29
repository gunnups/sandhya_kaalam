# Key Features of the Streamlit App:
# Title and Credits Banner: A greyish rectangular banner with the title, credits, and contact information.

# Location Input: Users can enter a location (default: Mason, OH). If the location is not found, an error message is displayed.

# Date Selection: Dropdowns for year (2025–2030), month (Jan–Dec), and day (1–31). Invalid dates (e.g., Feb 31) trigger an error message.

# Event Selection: Checkboxes for sunrise, sunset, and noon events. Users can select multiple events.

# .ics File Generation: The app generates an .ics file and provides a download link. Success or error messages are displayed in the bottom message box



import streamlit as st
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import pytz

# Title and Credits Banner
st.markdown(
    """
    <div style="background-color:#f0f0f0; padding:10px; border-radius:10px;">
        <h1 style="text-align:center;">సంధ్యా కాల గణనం</h1>
        <p style="text-align:center;">Credits: Goutham Mylavarapu</p>
        <p style="text-align:center;">Contact: <a href="mailto:goutham.mylavarapu@gmail.com">goutham.mylavarapu@gmail.com</a></p>
    </div>
    """,
    unsafe_allow_html=True
)

# Function to get timezone
def get_timezone(lat, lon):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse(f"{lat},{lon}", exactly_one=True)
    return pytz.timezone(location.raw['timezone']['tzid']) if location and 'timezone' in location.raw else pytz.utc

# Function to get sunrise and sunset data
def get_sunrise_sunset_month(lat, lon, year, month):
    start_date = datetime(year, month, 1)
    end_date = (
        datetime(year, month, 31) if month in {1,3,5,7,8,10,12} else
        datetime(year, month, 30) if month != 2 else
        datetime(year, month, 29) if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else
        datetime(year, month, 28)
    )
    
    url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0&start={start_date.strftime('%Y-%m-%d')}&end={end_date.strftime('%Y-%m-%d')}"
    response = requests.get(url)
    
    if response.status_code == 200 and response.json()["status"] == "OK":
        return response.json()["results"]  # Directly return the list of daily data
    st.error(f"Error fetching data for {year}-{month:02d}")
    return None

# Function to generate .ics file content
def generate_ics_content(location, start_date, end_date, events):
    geolocator = Nominatim(user_agent="my_geocoder")
    location_data = geolocator.geocode(location)

    if not location_data:
        st.error("The location is not found. Please enter City, State or City, State, Country format (e.g., Mason, OH).")
        return None

    lat, lon = location_data.latitude, location_data.longitude
    timezone = get_timezone(lat, lon)
    local_tz = timezone

    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Sunrise Sunset Calendar//EN\n"

    # Process sunrise and sunset events
    if 'sunrise' in events or 'sunset' in events:
        current_month = start_date.replace(day=1)
        end_month = end_date.replace(day=1)
        while current_month <= end_month:
            year = current_month.year
            month = current_month.month
            data = get_sunrise_sunset_month(lat, lon, year, month)
            if data:
                for idx, daily_data in enumerate(data):
                    day_date = (datetime(year, month, 1) + timedelta(days=idx)).date()
                    if start_date.date() <= day_date <= end_date.date():
                        sunrise_time = datetime.fromisoformat(daily_data["sunrise"])
                        sunset_time = datetime.fromisoformat(daily_data["sunset"])

                        if 'sunrise' in events:
                            sunrise_start = sunrise_time - timedelta(hours=1, minutes=12)
                            sunrise_end = sunrise_time + timedelta(minutes=48)
                            ics_content += generate_event(
                                sunrise_start, sunrise_end, "ప్రాతః సంధ్యా సమయం", location, 
                                day_date.strftime("%Y-%m-%d"), "sunrise"
                            )

                        if 'sunset' in events:
                            sunset_start = sunset_time - timedelta(minutes=24)
                            sunset_end = sunset_time + timedelta(hours=1, minutes=12)
                            ics_content += generate_event(
                                sunset_start, sunset_end, "సాయం సంధ్యా సమయం", location,
                                day_date.strftime("%Y-%m-%d"), "sunset"
                            )
            current_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Process noon events
    if 'noon' in events:
        current_day = start_date.date()
        end_day = end_date.date()
        delta = timedelta(days=1)
        while current_day <= end_day:
            noon_start_naive = datetime.combine(current_day, datetime.strptime("10:48", "%H:%M").time())
            noon_end_naive = datetime.combine(current_day, datetime.strptime("12:00", "%H:%M").time())
            noon_start = local_tz.localize(noon_start_naive).astimezone(pytz.utc)
            noon_end = local_tz.localize(noon_end_naive).astimezone(pytz.utc)
            ics_content += generate_event(
                noon_start, noon_end, "మాధ్యానిక సంధ్యా సమయం", location, current_day.strftime("%Y-%m-%d"), "noon"
            )
            current_day += delta

    ics_content += "END:VCALENDAR"
    return ics_content

# Function to generate an event in .ics format
def generate_event(start_time, end_time, summary, location, day_str, event_type):
    event = [
        "BEGIN:VEVENT",
        f"UID:{start_time.strftime('%Y%m%dT%H%M%S')}@{event_type}",
        f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end_time.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{summary} at {location}",
        f"DESCRIPTION:{summary} at {location} on {day_str}.",
        "BEGIN:VALARM",
        "TRIGGER:-PT15M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {summary} in 15 minutes.",
        "END:VALARM",
        "BEGIN:VALARM",
        "TRIGGER:PT0M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {summary} is starting now.",
        "END:VALARM",
        "END:VEVENT\n"
    ]
    return "\n".join(event) + "\n"

# Streamlit UI
st.sidebar.header("User Inputs")

# Location Input
location = st.sidebar.text_input("Enter Location (e.g., Mason, OH):", "Mason, OH")
st.sidebar.caption("Default: Mason, OH")

# Date Selection
year = st.sidebar.selectbox("Select Year:", range(2025, 2031), index=0)
month = st.sidebar.selectbox("Select Month:", range(1, 13), index=0)
day = st.sidebar.selectbox("Select Day:", range(1, 32), index=0)

# Validate Date
try:
    start_date = datetime(year, month, day)
    end_date = datetime(year, month, day)
except ValueError:
    st.error("Invalid date selected. Please choose a valid date.")
    st.stop()

# Event Selection
events = st.sidebar.multiselect("Select Events:", ["sunrise", "noon", "sunset"], default=["sunrise", "sunset"])

# Generate .ics File
if st.sidebar.button("Generate .ics File"):
    ics_content = generate_ics_content(location, start_date, end_date, events)
    if ics_content:
        filename = f"{location.replace(' ', '_').replace(',', '')}_sandhya_kaalam_{year}.ics"
        with open(filename, "w") as ics_file:
            ics_file.write(ics_content)
        st.success(f"Successfully created .ics file. Check your downloads folder for '{filename}'.")
        st.download_button(
            label="Download .ics File",
            data=ics_content,
            file_name=filename,
            mime="text/calendar"
        )

# Message Box at the Bottom
st.markdown(
    """
    <div style="background-color:#f0f0f0; padding:10px; border-radius:10px;">
        <p style="color:red; text-align:center;">Messages will appear here.</p>
    </div>
    """,
    unsafe_allow_html=True
)