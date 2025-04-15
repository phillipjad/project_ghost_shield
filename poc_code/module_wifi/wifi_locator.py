import os
import requests
from math import cos, sin, radians
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_location(wifi_data):
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}"
    response = requests.post(url, json={"wifiAccessPoints": wifi_data})
    response.raise_for_status()
    return response.json()

def latlon_to_xyz(lat, lon, alt=0):
    R = 6371000 + alt
    lat_rad = radians(lat)
    lon_rad = radians(lon)
    x = R * cos(lat_rad) * cos(lon_rad)
    y = R * cos(lat_rad) * sin(lon_rad)
    z = R * sin(lat_rad)
    return x, y, z

# Example usage
if __name__ == "__main__":
    wifi_data = [
        {"macAddress": "00:25:9c:cf:1c:ac", "signalStrength": -43},
        {"macAddress": "00:25:9c:cf:1c:ad", "signalStrength": -55}
    ]
    result = get_location(wifi_data)
    lat = result['location']['lat']
    lon = result['location']['lng']
    print("Lat, Lon:", lat, lon)
    print("XYZ:", latlon_to_xyz(lat, lon))
