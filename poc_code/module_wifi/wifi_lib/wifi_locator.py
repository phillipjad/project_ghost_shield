import geocoder
from math import radians, cos, sin

def get_latlon_from_ip():
    """Gets approximate lat/lon using your public IP (no API key needed)."""
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng  # returns [lat, lon]
    else:
        raise Exception("Failed to get geolocation from IP.")

def latlon_to_xyz(lat, lon, alt=0):
    """Convert lat/lon/alt to Cartesian X, Y, Z coordinates (in meters)."""
    R = 6371000 + alt  # Earth's radius + optional altitude
    lat_rad = radians(lat)
    lon_rad = radians(lon)
    x = R * cos(lat_rad) * cos(lon_rad)
    y = R * cos(lat_rad) * sin(lon_rad)
    z = R * sin(lat_rad)
    return x, y, z

def get_xyz_from_ip():
    latlon = get_latlon_from_ip()
    lat, lon = latlon
    return latlon_to_xyz(lat, lon)

if __name__ == "__main__":
    lat, lon = get_latlon_from_ip()
    x, y, z = get_xyz_from_ip()
    print(f"Latitude: {lat}, Longitude: {lon}")
    print(f"XYZ Coordinates: x={x:.2f}, y={y:.2f}, z={z:.2f}")