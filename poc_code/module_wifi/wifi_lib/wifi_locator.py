from math import cos, radians, sin

import geocoder


def get_latlon_from_ip() -> list[float]:
    """Gets approximate lat/lon using your public IP (no API key needed)."""
    g = geocoder.ip("me")
    if g.ok:
        return g.latlng  # returns [lat, lon]
    else:
        raise Exception("Failed to get geolocation from IP.")


def latlon_to_xyz(
    lat: float, lon: float, alt: float = 0.0
) -> tuple[float, float, float]:
    """Convert lat/lon/alt to Cartesian X, Y, Z coordinates (in meters)."""
    r = 6371000 + alt  # Earth's radius + optional altitude
    lat_rad = radians(lat)
    lon_rad = radians(lon)
    x = r * cos(lat_rad) * cos(lon_rad)
    y = r * cos(lat_rad) * sin(lon_rad)
    z = r * sin(lat_rad)
    return x, y, z


def get_xyz_from_ip() -> tuple[float, float, float]:
    latlon = get_latlon_from_ip()
    lat, lon = latlon
    return latlon_to_xyz(lat, lon)


if __name__ == "__main__":
    lat, lon = get_latlon_from_ip()
    x, y, z = get_xyz_from_ip()
    print(f"Latitude: {lat}, Longitude: {lon}")
    print(f"XYZ Coordinates: x={x:.2f}, y={y:.2f}, z={z:.2f}")
