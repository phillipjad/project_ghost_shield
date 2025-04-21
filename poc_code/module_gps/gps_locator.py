import serial
import pynmea2
from pyproj import Transformer

# --- Setup Serial Port ---
# Update this to match your system's USB port name
SERIAL_PORT = '/dev/ttyUSB0'  # or 'COM3' on Windows
BAUD_RATE = 9600

# --- Setup Transformer ---
# EPSG:4979 = WGS84 with ellipsoidal height
# EPSG:4978 = ECEF (Earth-Centered, Earth-Fixed)
transformer = Transformer.from_crs("epsg:4979", "epsg:4978", always_xy=True)

def get_xyz_from_gps():
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        while True:
            line = ser.readline().decode("ascii", errors="replace").strip()
            if line.startswith('$GPGGA') or line.startswith('$GNGGA'):
                try:
                    msg = pynmea2.parse(line)
                    lat = msg.latitude
                    lon = msg.longitude
                    alt = float(msg.altitude)

                    x, y, z = transformer.transform(lon, lat, alt)
                    return x, y, z
                except Exception as e:
                    print(f"Parse error: {e}")

# --- Example Usage ---
x, y, z = get_xyz_from_gps()
print(f"X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}")
