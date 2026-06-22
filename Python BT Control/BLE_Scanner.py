# Bluetooth LE scanner
# Prints the name and address of every nearby Bluetooth LE device
# From the bleak github: https://github.com/hbldh/bleak

import asyncio
from bleak import BleakScanner

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)

asyncio.run(main())