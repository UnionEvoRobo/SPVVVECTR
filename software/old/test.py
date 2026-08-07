# SPVVVECTR modules live in the parent directory (software/) after the
# 2026 restructure; add it to sys.path so this legacy script still runs.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SPVVVECTR_Class import SPVVVECTR
import tkinter as tk
import asyncio
import threading, asyncio

def main():
    #Robot initialization
    robot = SPVVVECTR()

    #New thread
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()

    #Window and title
    root = tk.Tk()
    title = tk.Label(root, text = "TEST")
    title.grid(
        row = 0,
        column = 0,
        columnspan = 3
    )

    async def connect_pressed():
        await robot.connect_strut("SPVVVECTR1")
        if await robot.get_status("SPVVVECTR1") == "ONLINE":
            print("Connected to SPVVVECTR1")
        else:
            print("Failed to connect to SPVVVECTR1")
    connect_btn = tk.Button(root, text="Connect Strut 1", 
                            command=lambda: 
                            asyncio.run_coroutine_threadsafe(connect_pressed(), loop))
    connect_btn.grid(
        row = 1,
        column = 0,
    )

    connect_sta = tk.StringVar()
    connect_label = tk.Label(root, textvariable=connect_sta)
    connect_label.grid(
        row = 2,
        column = 0,
    )

    #Function to update data
    def update_data():
        status = asyncio.run_coroutine_threadsafe(robot.get_status("SPVVVECTR1"), loop).result()
        connect_sta.set(status)
        root.after(500, update_data)  # Schedule the next update after 1 second

    #root mainloop
    root.eval('tk::PlaceWindow . center')
    update_data()
    root.mainloop()

if __name__ == "__main__":
    main()

