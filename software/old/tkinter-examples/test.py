import asyncio
import tkinter as tk
from async_tkinter_loop import async_handler, async_mainloop
from bleak import BleakScanner

async def scan_devices():
    devices = await BleakScanner.discover()
    print("Found devices:", [d.name for d in devices])

root = tk.Tk()

btn = tk.Button(root, text="Scan BLE", command=async_handler(scan_devices))
btn.pack(padx=20, pady=20)

async_mainloop(root)