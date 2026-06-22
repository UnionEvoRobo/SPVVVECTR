from SPVVVECTR_BLE_Control import SPVVVECTR
import tkinter as tk
import asyncio
import threading, asyncio


global_speed = 0
cell_width = 25

def main():
    #Robot initialization
    robot = SPVVVECTR()
    CURR_ROW = 0


    #New thread and run loop forever
    loop = asyncio.new_event_loop()
    def run_async_loop(async_loop):
        asyncio.set_event_loop(async_loop)
        async_loop.run_forever()
    threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()


    #Main app window and title
    root = tk.Tk()
    root.minsize(600, 250)
    title = tk.Label(root, text="Tensegrity Control").grid(
        row = CURR_ROW, column = 0, columnspan = 5)
    CURR_ROW += 1


    #Global message Setup
    global_message = tk.StringVar()
    global_message.set("Welcome to the Tensegrity Control Panel!")


    #Global functions
    async def button1_pressed():
         await robot.connect_all()
         global_message.set("Connecting to all struts...")

    button1 = tk.Button(root, text="Connect All", width = cell_width, command=lambda:
                         asyncio.run_coroutine_threadsafe(button1_pressed(), loop))
    button1.grid(row = CURR_ROW, column = 0)


    async def button2_pressed():
        await robot.disconnect_all()
        global_message.set("Disconnecting from all struts...")
    button2 = tk.Button(root, text="Disconnect All", width = cell_width, command=lambda:
                        asyncio.run_coroutine_threadsafe(button2_pressed(), loop))
    button2.grid(row = CURR_ROW, column = 1)


    async def button3_pressed():
        await robot.stop_all()
        global_message.set("Stopping all struts...")
    button3 = tk.Button(root, text="Stop All", width=cell_width, command=lambda:
                        asyncio.run_coroutine_threadsafe(button3_pressed(), loop))
    button3.grid(row = CURR_ROW, column = 2)


    #Entry for global speed
    label4= tk.Label(root, text="Set Global Speed:", width=cell_width).grid(
        row = CURR_ROW,
        column = 3
    )

    def Invalid_speed():
        global_message.set("Invalid input for global speed")
        
    async def global_speed_entry(event):
        global global_speed
        try:
            global_speed = int(event.widget.get())
            if abs(global_speed) <= robot.MAX_SPEED:
                await robot.set_speed_all(global_speed)
                global_message.set(f"Global speed set to {global_speed} RPM")
            else:
                Invalid_speed()
        except:
            global_message.set("Hello")
    entry5 = tk.Entry(root, width=cell_width)
    entry5.grid(row = CURR_ROW, column = 4)
    entry5.bind("<Return>", lambda event: 
                asyncio.run_coroutine_threadsafe(global_speed_entry(event), loop))

    CURR_ROW += 1


    #Global message display
    label6 = tk.Label(root, text="Global Message:")
    label6.grid(row = CURR_ROW, column = 0)

    label7 = tk.Label(root, 
                      textvariable=global_message,
                      borderwidth=0.5,
                      relief="solid"
                      )
    label7.grid(row = CURR_ROW, column = 1, columnspan = 4)

    CURR_ROW += 1


    #UI Registry to keep track of changing data
    ui_registry = {}


    #Helper function to connect to a particular strut
    def connect_cmd(name, status_var):
        async def connect_strut():
            curr_status = ui_registry[name]['status'].get()
            if status_var.get() == "OFFLINE":
                try:
                    await robot.connect_strut(name)
                except Exception as e:
                    print(f"Error connecting to {name}: {e}")
            else:
                pass
        return lambda: asyncio.run_coroutine_threadsafe(
            connect_strut(), loop)
    
    def set_speed_cmd(name):
        async def set_strut_speed(event):
            try:
                speed = int(event.widget.get())
                if abs(speed) <= robot.MAX_SPEED:
                    await robot.set_speed(name, speed)
                else:
                    pass 
            except ValueError:
                pass
        return lambda event: asyncio.run_coroutine_threadsafe(
            set_strut_speed(event), loop)


    #Display struts data:
    for i in range(3):
        col_offset = 2*i

        #Strut name
        name = f"SPVVVECTR{i+1}"
        tk.Label(root, text=name).grid(
            row = CURR_ROW,
            column = col_offset
        )

        #Connection status
        status_var = tk.StringVar()
        status_var.set("OFFLINE")
        tk.Label(root, textvariable=status_var).grid(
            row = CURR_ROW+1,
            column = col_offset
        )

        #Connect button               
        tk.Button(root, text="Connect", width=cell_width, 
                  command=connect_cmd(name, status_var)
                  ).grid(
            row = CURR_ROW+2,
            column = col_offset
        )

        #Set Speed Entry
        speed_entry = tk.Entry(root, width=cell_width)
        speed_entry.insert(0, "Set Target RPM")
        speed_entry.grid(
            row = CURR_ROW+3,
            column = col_offset
        )
        speed_entry.bind("<Return>", set_speed_cmd(name))

        #RPM display
        rpm_message = tk.StringVar()
        rpm_message.set("Target RPM: N/A\nActual RPM: N/A")
        tk.Label(root, textvariable=rpm_message, height=2).grid(
            row = CURR_ROW+4,
            column = col_offset 
        )

        #MPU data display
        imu_message = tk.StringVar()
        imu_message.set("Accel: N/A\nGyro: N/A")
        tk.Label(root, textvariable=imu_message, height=2).grid(
            row = CURR_ROW+5,
            column = col_offset
        )

        #Reference to UI elements for data update
        ui_registry[name] = {
            'status': status_var,
            'rpm': rpm_message,
            'imu': imu_message
        }
    CURR_ROW += 6

    #Update data:
    async def update_data():
        for name, elements in ui_registry.items():
            try:
                status = await robot.get_status(name)
                elements['status'].set(status)

                if status == "ONLINE":
                    data = await robot.get_strut_data(name)
                    (
                            target_rpm,
                            actual_rpm,
                            acc_x,
                            acc_y,
                            acc_z,
                            gyro_x,
                            gyro_y,
                            gyro_z,
                        ) = data
                    
                    elements['rpm'].set(f"Target RPM: {target_rpm}\nActual RPM: {actual_rpm}")
                    elements['imu'].set(f"Accel: ({acc_x}, {acc_y}, {acc_z})\nGyro: ({gyro_x}, {gyro_y}, {gyro_z})")
                else:
                    elements['rpm'].set("Target RPM: N/A\nActual RPM: N/A")
                    elements['imu'].set("Accel: N/A\nGyro: N/A")
            except Exception as e:
                print(f"Error updating data for {name}: {e}")
        root.after(500, lambda: asyncio.run_coroutine_threadsafe(update_data(), loop))
    asyncio.run_coroutine_threadsafe(update_data(), loop)

    #Center and display the window
    root.eval('tk::PlaceWindow . center')
    root.mainloop()

if __name__ == "__main__":
    main()

