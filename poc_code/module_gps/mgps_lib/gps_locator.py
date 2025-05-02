import serial
import pynmea2
from pyproj import Transformer
import serial.tools.list_ports


# --- Auto-detect GPS Serial Port (STEMEdu shows up as "u-blox" or similar) ---
def find_gps_port():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if (
            "GPS" in p.description
            or "u-blox" in p.description
            or "Silicon Labs" in p.description
        ):
            return p.device
    return None


# --- EPSG:4979 = WGS84 (lat/lon/height), EPSG:4978 = ECEF XYZ ---
transformer = Transformer.from_crs("epsg:4979", "epsg:4978", always_xy=True)


def get_xyz_from_gps():
    port = find_gps_port()
    if not port:
        print("⚠️ GPS device not found. Please check USB connection.")
        return None

    try:
        with serial.Serial(port, baudrate=9600, timeout=2) as ser:
            print(f"📡 Connected to GPS on {port}. Waiting for valid data...")

            while True:
                line = ser.readline().decode("ascii", errors="replace").strip()
                if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                    try:
                        msg = pynmea2.parse(line)
                        lat = msg.latitude
                        lon = msg.longitude
                        alt = float(msg.altitude)

                        x, y, z = transformer.transform(lon, lat, alt)
                        return x, y, z
                    except Exception as e:
                        print(f"Parse error: {e}")
    except Exception as e:
        print(f"Serial connection error: {e}")
        return None


# --- Example Usage ---
result = get_xyz_from_gps()
if result:
    x, y, z = result
    print(f"ECEF Coordinates:\nX: {x:.2f}\nY: {y:.2f}\nZ: {z:.2f}")
