
# SPVVVECTR Codes & Locomotion Optimization

## This repository contains the microcontroller, BLE, and Optimization/QTM code needed to control SPVVVECTR and optimize linear displacemet. 

## author: Miraj Parekh & Duy Hung Dang

## date: "August 7th, 2026"
(This code is reuploaded)

### Code used:
1. SPVVVECCTR-MCU-PP-BLE.ino
- This is the code needed to operate the microcontroller ESP32 on each strut
- This code uses Pulse Period to calculate RPM
- This code uses BLE (Bluetooth Low-Energy) for Communication.
- Flash this code onto each microcontroller before running the Python BLE code

2. BLE_Control.py
- This is the code needed from the laptop (host) side to control SPVVVECTR remotely using BLE.
- Run using VSCode with bleak installed using  pip install bleak
- This is the primitive version of the control

3. Better BLE Control
- Development finished (6/22/2026)
- Provides the Object Classes for each PCB Strut, for the entire SPECTR robot (6 bar-3PCB), and the GUI for the controller.
- Intended for Windows

4. Other notes:
- The Classic Bluetooth version is also usable, albeit not as well as developed as the BLE version
- This code will require 3 COM ports space on the laptop, so make sure you have some ports available
- SPVVVECCTR-MCU-PP-BT.ino
- ClassicBT_Control.py

# SPVVVECTR Locomotion Optimization 
*Look inside software directory for relevant README.*