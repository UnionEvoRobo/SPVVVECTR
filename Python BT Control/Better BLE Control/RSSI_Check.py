'''Modified from https://github.com/boshyxd/RSSICheck/blob/main/RSSICheck.py '''

import asyncio
from bleak import BleakScanner

def classify_rssi(rssi):
    if rssi >= -50:
        return "Excellent"
    elif rssi >= -60:
        return "Good"
    elif rssi >= -70:
        return "Fair"
    elif rssi >= -80:
        return "Weak"
    elif rssi >= -90:
        return "Very Weak"
    else:
        return "Unusable"

async def scan():
    target_rssi = 0
    devices_found = {}

    def detection_callback(device, advertisement_data):
        nonlocal target_rssi
        if device.address not in devices_found:
            rssi = advertisement_data.rssi
            signal_quality = classify_rssi(rssi)
            devices_found[device.address] = (rssi, signal_quality)
            if device.address == "8C:94:DF:2B:28:E6":
                target_rssi = rssi
                print(f"Device: {device.name or 'Unknown'}, \n"
                      f"      Address: {device.address}, \n"
                      f"      RSSI: {rssi} dBm, \n"
                      f"      Signal Quality: {signal_quality}")

    scanner = BleakScanner(detection_callback=detection_callback)
    
    print("Scanning for Bluetooth devices...")
    await scanner.start()
    await asyncio.sleep(1)
    await scanner.stop() 

    return target_rssi

if __name__ == "__main__":
    total_rssi = 0
    number_of_scans = 20
    for i in range(number_of_scans):
        temp = asyncio.run(scan())
        total_rssi += temp
    average_rssi = total_rssi / number_of_scans
    print(f"Average RSSI over {number_of_scans} scans: {average_rssi:.2f} dBm")
