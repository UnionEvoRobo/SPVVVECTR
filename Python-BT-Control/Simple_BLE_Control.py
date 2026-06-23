'''

Dang Duy Hung

April 2026



Code description: This code will allow you to read/write three seperate UM-Tinypico-Nano boards

using the BLE. The Shell allows you to:

1. See the information sent by each board, including: name, target RPM, and average RPM.

2. write to each board using these commands:


[name] + [number]

E.g: bt1 150 will make the Tensegrity BT1 strut rotate clockwise at 150 RPM.

[name]

Make all motor spin in the CW direction at that RPM

[exit]

End the control loop

[stop]

Turn off all motor


Note:
You will need to install bleak through cmd prompt: pip install bleak
All boards need to be powered and uploaded with the BLE code for this script to run properly.
You can input both negative number (CCW) and positive number (CW) for the speed.

'''


import asyncio
from bleak import BleakClient, BleakScanner
import threading
import tkinter as tk

# --- CONFIGURATION ---
# Replace these with MAC adresses from Scanner and UUID from Arduino codes
BOARDS_CONFIG = {
    "Tensegrity-BT1": {"address": "8C:94:DF:2B:28:E6", "service": "afcdeba4-f8a9-4ca1-baa5-021afe634998", "char": "83147421-2684-43ec-af39-58533d866c8e"},
    "Tensegrity-BT2": {"address": "8C:94:DF:2B:29:22", "service": "8aaba9c2-7f68-49d6-97cb-b9783ea29fd6", "char": "2a612f78-13b2-4b3a-bab8-50b00d2f003f"},
    "Tensegrity-BT3": {"address": "8C:94:DF:2B:28:F2", "service": "e132a2ee-a68a-4b4b-98fa-29ef8bbc0be2", "char": "ccba8d13-8743-45f7-9fd9-69a20a9acddc"}
}

connections = {} # Stores active BleakClient objects

def notification_handler(sender, data, board_name):
    """Callback for when the ESP32 sends Notify data (Target/Avg RPM) using Text utf-8"""
    message = data.decode('utf-8')
    print(f"[{board_name}] {message}")

async def connect_to_board(name, config):
    client = BleakClient(config["address"])
    try:
        await client.connect()
        if client.is_connected:
            print(f"ONLINE: {name}")
            # Start listening for the Notify updates we set up in Arduino
            await client.start_notify(config["char"], lambda s, d: notification_handler(s, d, name))
            connections[name] = {"client": client, "char": config["char"]}
            return True
    except Exception as e:
        print(f"OFFLINE: {name} ({e})")
        return False

async def main():
    print("--- Initializing Tensegrity BLE Link ---")
    
    # 1. Connect to all boards
    tasks = [connect_to_board(name, cfg) for name, cfg in BOARDS_CONFIG.items()]
    await asyncio.gather(*tasks)

    if not connections:
        print("No boards connected. Exiting.")
        return

    print("\n--- Command Mode ---")
    print("Commands: [number], [name] [num], stop, exit")

    # 2. Control Loop
    while True:
        # Use run_in_executor to handle blocking input() in an async loop
        cmd = await asyncio.get_event_loop().run_in_executor(None, lambda: input("\nRobot Control > ").strip().lower())
        
        if cmd == 'exit':
            break
        if cmd == 'stop':
            cmd = "0"

        parts = cmd.split()
        
        try:
            if len(parts) == 2:
                target_name_part = parts[0]
                target_val = parts[1]
                
                for name, conn in connections.items():
                    if target_name_part in name.lower():
                        await conn["client"].write_gatt_char(conn["char"], target_val.encode(), response=False)
                        print(f"Sent {target_val} to {name}")

            elif len(parts) == 1:
                val = float(parts[0])
                for name, conn in connections.items():
                    await conn["client"].write_gatt_char(conn["char"], str(val).encode(), response=False)
                print(f"Global sync: {val} RPM")
        except Exception as e:
            print(f"Command Error: {e}")

    # 3. Cleanup
    print("Closing BLE connections...")
    for conn in connections.values():
        await conn["client"].disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


