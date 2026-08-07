import asyncio
from bleak import BleakClient

# --- CONFIGURATION ---
# MAC Address (From Scanner) and UUIDs (From Arduino Code)
BOARDS_CONFIG = {
    "Tensegrity-BT1": {
        "address": "0C:8B:95:AA:8B:CE", 
        "char": "83147421-2684-43ec-af39-58533d866c8e"
    },
    "Tensegrity-BT2": {
        "address": "0C:8B:95:AA:8C:52", 
        "char": "2a612f78-13b2-4b3a-bab8-50b00d2f003f"
    },
    "Tensegrity-BT3": {
        "address": "0C:8B:95:AA:8B:FE", 
        "char": "ccba8d13-8743-45f7-9fd9-69a20a9acddc"
    }
}


def notification_handler(sender, data, board_name):
    """Callback for when the ESP32 pushes new RPM data"""
    try:
        message = data.decode('utf-8')
        print(f"[{board_name}] {message}")
    except Exception as e:
        print(f"[{board_name}] Data Error: {e}")

async def manage_board(name, config):
    """Handles the lifecycle of a single board connection"""
    print(f"Attempting to connect to {name}...")
    
    async with BleakClient(config["address"]) as client:
        if client.is_connected:
            print(f"CONNECTED: {name}")
            
            # Start notifications. The ESP32 must have PROPERTY_NOTIFY enabled.
            await client.start_notify(config["char"], lambda s, d: notification_handler(s, d, name))
            
            # Keep this specific connection alive indefinitely
            while client.is_connected:
                await asyncio.sleep(1.0)
                
        print(f"DISCONNECTED: {name}")

async def main():
    print("--- Tensegrity RPM Monitor ---")
    print("Press Ctrl+C to stop reading\n")
    
    # Create tasks for all three boards to run concurrently
    tasks = [manage_board(name, cfg) for name, cfg in BOARDS_CONFIG.items()]
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\nStopping RPM Monitor...")

if __name__ == "__main__":
    asyncio.run(main())