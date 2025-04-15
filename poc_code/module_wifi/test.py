import pywifi
import time

wifi = pywifi.PyWiFi()
iface = wifi.interfaces()[0]

iface.scan()
time.sleep(3)
results = iface.scan_results()

for network in results:
    print(f"SSID: {network.ssid}, BSSID: {network.bssid}, Signal: {network.signal}")
