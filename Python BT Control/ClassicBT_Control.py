'''
Dang Duy Hung
April 2026

Code description: This code will allow you to read/write three seperate UM-Tinypico-Nano boards
using the Serial Bluetooth Communication. The Shell allows you to:
1. See the information sent by each board, including: name, target RPM, and average RPM.
2. write to each board using these commands:

[name] + [number]
E.g: bt1 150 will make the Tensegrity BT1 strut rotate clockwise at 150 RPM.
[name]
Make all motor spin in the CW direction at that RPM
[exit]
Close this script
[stop]
Turn off all motor

Note: The COM port occupied by the Serial BT Communication is different on each
computer, so you may need to use Arduino IDE to see which port belongs to each board.
Also, all boards need to be powered and uploaded with the code for this script to run properly.
'''




import serial
import threading
import time

# --- MAPPED CONFIGURATION ---
BOARDS = {
    "Tensegrity-BT1": "COM8",
    "Tensegrity-BT2": "COM11",
    "Tensegrity-BT3": "COM13"
}
BAUD_RATE = 115200

#Receive BT input from each online board
def read_from_board(ser, board_name):
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    # This will display: [Tensegrity-BT1] Target:...,Avg:...
                    print(f"[{board_name}] {line}")
        except Exception:
            print(f"!!! Connection lost to {board_name}")
            break

def main():
    #Setup
    connections = {}

    print("--- Initializing Tensegrity Wireless Link ---")
    
    # 1. Connect to all Bluetooth ports
    for name, port in BOARDS.items():
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=0.1)
            connections[name] = ser
            print(f"ONLINE: {name} on {port}")
        except Exception as e:
            print(f"OFFLINE: {name} on {port} (Check if paired/powered)")

    # 2. Start background listeners
    for name, ser in connections.items():
        thread = threading.Thread(target=read_from_board, args=(ser, name), daemon=True)
        thread.start()

    if not connections:
        print("No boards connected. Exiting.")
        return

    print("\n--- Command Mode ---")
    print("Commands:")
    print("  [number]       -> Set ALL motors to that RPM (e.g., 100)")
    print("  [name] [num]   -> Set ONE motor (e.g., BT1 80)")
    print("  stop           -> All motors to 0")
    print("  exit           -> Close script")

    # 3. Control Loop
    try:
        while True:
            cmd = input("\nRobot Control > ").strip().lower()
            
            if cmd == 'exit':
                break
            if cmd == 'stop':
                cmd = "0"

            # Check if user wants to control a specific board (e.g., "bt1 150")
            parts = cmd.split()
            
            if len(parts) == 2:
                target_name_part = parts[0]
                target_val = parts[1]
                
                # Find the board that matches the nickname
                found = False
                for name, ser in connections.items():
                    if target_name_part in name.lower():
                        ser.write(f"{target_val}\n".encode())
                        print(f"Sent {target_val} to {name}")
                        found = True
                if not found:
                    print(f"Board '{target_name_part}' not found.")

            elif len(parts) == 1:
                # Global command for all boards
                try:
                    val = float(parts[0])
                    msg = f"{val}\n".encode()
                    for ser in connections.values():
                        ser.write(msg)
                    print(f"Global sync: {val} RPM")
                except ValueError:
                    print("Invalid input. Use a number or 'BT# [number]'.")

    except KeyboardInterrupt:
        pass
    finally:
        for ser in connections.values():
            ser.close()
        print("Connections closed safely.")

if __name__ == "__main__":
    main()