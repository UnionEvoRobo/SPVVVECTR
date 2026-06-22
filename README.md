
# title: SPVVVECTR Codes

## "This repository contains the microcontroller and BLE code needed to control SPVVVECTR"

## author: "Dang, Duy Hung"

## date: "2026-06-17"
(This code is reuploaded)

### Code used:
1. PID_Pulse_Period_and_BLE.ino
- This is the code needed to operate the microcontroller ESP32 on each strut
- Flash this code onto each microcontroller before running the Python BLE code

2. BLE_Control.py
- This is the code needed from the laptop (host) side to control SPVVVECTR remotely using BLE.
- Run using VSCode with bleak installed using  pip install bleak
- This is the primitive version of the control

3. Better BLE Control
- In development
- Will use OOP technique to simplify the code structure, with the aim of improving code readability and modularity
- Aim to integrate the built-in Tkinter GUI to make the data reading more readable

4. Other notes:
- The Classic Bluetooth version is also usable, albeit not as well as developed as the BLE version
- This code will require 3 COM ports space on the laptop, so make sure you have some ports available
- PID_Pulse_period_and_classicBT.ino
- ClassicBT_Control.py
