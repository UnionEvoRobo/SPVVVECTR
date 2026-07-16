from SPVVVECTR_Class import SPVVVECTR
from spvvvectr_tracker import QtmTracker
from skopt import Optimizer
from skopt.space import Integer
from skopt.sampler import Lhs
from skopt.learning import GaussianProcessRegressor
from skopt.learning.gaussian_process.kernels import Matern 
import tkinter as tk
from tkinter import filedialog
import threading
import asyncio
import math

global_speed = 0
cell_width = 25

def main():
    # Robot initialization
    robot = SPVVVECTR()
    CURR_ROW = 0

    # New thread and run loop forever
    loop = asyncio.new_event_loop()
    def run_async_loop(async_loop):
        asyncio.set_event_loop(async_loop)
        async_loop.run_forever()
    threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()

    # --- INITIALIZE TRACKER IN THE ASYNC THREAD ---
    tracker = QtmTracker("10.76.30.85", loop=loop)

    # Main app window and title
    root = tk.Tk()
    root.title("SPVVVECTR Control & Optimization")
    root.minsize(900, 700) # Increased size to fit both manual and BO controls
    tk.Label(root, text="Tensegrity Control", font=("Arial", 14, "bold")).grid(
        row = CURR_ROW, column = 0, columnspan = 6, pady=5)
    CURR_ROW += 1

    # Global message Setup
    global_message = tk.StringVar()
    global_message.set("Welcome to the Tensegrity Control Panel!")

    # =========================================================
    # --- ORIGINAL MANUAL CONTROL SECTION ---
    # =========================================================

    async def button1_pressed():
         global_message.set("Connecting to all struts...")
         await robot.connect_all()
    tk.Button(root, text="Connect All", width=cell_width, command=lambda: asyncio.run_coroutine_threadsafe(button1_pressed(), loop)).grid(row=CURR_ROW, column=0)

    async def button2_pressed():
        global_message.set("Disconnecting from all struts...")
        await robot.disconnect_all()
    tk.Button(root, text="Disconnect All", width=cell_width, command=lambda: asyncio.run_coroutine_threadsafe(button2_pressed(), loop)).grid(row=CURR_ROW, column=1)

    async def button3_pressed():
        global_message.set("Stopping all struts...")
        await robot.stop_all()
    tk.Button(root, text="Stop All", width=cell_width, command=lambda: asyncio.run_coroutine_threadsafe(button3_pressed(), loop)).grid(row=CURR_ROW, column=2)

    tk.Label(root, text="Set Global Speed:", width=cell_width).grid(row=CURR_ROW, column=3)

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
            Invalid_speed()
    entry5 = tk.Entry(root, width=cell_width)
    entry5.grid(row=CURR_ROW, column=4)
    entry5.bind("<Return>", lambda event: asyncio.run_coroutine_threadsafe(global_speed_entry(event), loop))
    CURR_ROW += 1

    curr_dir = "Not set"
    def select_directory():
        directory = filedialog.askdirectory(title="Select Working Directory")
        nonlocal curr_dir
        curr_dir = directory
        short_dir = "..." + directory[-20:] if len(directory) > 20 else directory
        work_dir.set(f"Working Directory: {short_dir}")
        if directory:
            asyncio.run_coroutine_threadsafe(robot.set_working_directory(directory), loop)
            
    tk.Button(root, text="Select Working Directory", width=cell_width, command=select_directory).grid(row=CURR_ROW, column=0)
    work_dir = tk.StringVar()
    work_dir.set(f"Working Directory: {curr_dir}")
    tk.Label(root, textvariable=work_dir).grid(row=CURR_ROW, column=1, columnspan=2)

    recording_status = False
    recording_message = tk.StringVar()
    recording_message.set("Recording: OFF")
    tk.Label(root, textvariable=recording_message).grid(row=CURR_ROW, column=3)

    def toggle_recording():
        if curr_dir == "Not set":
            global_message.set("Please select a working directory before recording.")
        else:
            nonlocal recording_status
            recording_status = not recording_status
            if recording_status:
                recording_message.set("Recording: ON")
                asyncio.run_coroutine_threadsafe(robot.start_record(), loop)
            else:
                recording_message.set("Recording: OFF")
                asyncio.run_coroutine_threadsafe(robot.stop_record(), loop)
        
    tk.Button(root, text="Toggle Recording", width=cell_width, command=toggle_recording).grid(row=CURR_ROW, column=4)
    CURR_ROW += 1
    
    tk.Label(root, text="Global Message:").grid(row=CURR_ROW, column=0)
    tk.Label(root, textvariable=global_message, borderwidth=0.5, relief="solid").grid(row=CURR_ROW, column=1, columnspan=4, sticky="ew")
    CURR_ROW += 1

    ui_registry = {}

    def connect_cmd(name, status_var):
        async def connect_strut():
            if status_var.get() == "OFFLINE":
                try:
                    await robot.connect_strut(name)
                except Exception as e:
                    print(f"Error connecting to {name}: {e}")
        return lambda: asyncio.run_coroutine_threadsafe(connect_strut(), loop)
    
    def disconnect_cmd(name, status_var):
        async def disconnect_strut():
            if status_var.get() == "ONLINE":
                try:
                    await robot.disconnect_strut(name)
                except Exception as e:
                    print(f"Error disconnecting from {name}: {e}")
        return lambda: asyncio.run_coroutine_threadsafe(disconnect_strut(), loop)
    
    def set_speed_cmd(name):
        async def set_strut_speed(event):
            try:
                speed = int(event.widget.get())
                if abs(speed) <= robot.MAX_SPEED:
                    await robot.set_speed(name, speed)
            except ValueError:
                pass
        return lambda event: asyncio.run_coroutine_threadsafe(set_strut_speed(event), loop)

    def calibrate_cmd(name):
        async def calibrate_strut():
            try:
                await robot.calibrate(name)
            except Exception as e:
                print(f"Error calibrating IMU for {name}: {e}")
        return lambda: asyncio.run_coroutine_threadsafe(calibrate_strut(), loop)

    # Display struts data
    for i in range(3):
        col_offset = i * 2 # Adjusted for better spacing

        name = f"SPVVVECTR{i+1}"
        tk.Label(root, text=name, font=("Arial", 10, "bold")).grid(row=CURR_ROW, column=col_offset, columnspan=2)
        
        status_var = tk.StringVar()
        status_var.set("OFFLINE")
        tk.Label(root, textvariable=status_var).grid(row=CURR_ROW+1, column=col_offset, columnspan=2)

        tk.Button(root, text="Connect", width=15, command=connect_cmd(name, status_var)).grid(row=CURR_ROW+2, column=col_offset, columnspan=2)
        tk.Button(root, text="Disconnect", width=15, command=disconnect_cmd(name, status_var)).grid(row=CURR_ROW+3, column=col_offset, columnspan=2)

        speed_entry = tk.Entry(root, width=15)
        speed_entry.insert(0, "Set Target RPM")
        speed_entry.grid(row=CURR_ROW+4, column=col_offset, columnspan=2)
        speed_entry.bind("<Return>", set_speed_cmd(name))

        rpm_message = tk.StringVar()
        rpm_message.set("Target RPM: N/A\nActual RPM: N/A")
        tk.Label(root, textvariable=rpm_message, height=2).grid(row=CURR_ROW+5, column=col_offset, columnspan=2)

        imu_message = tk.StringVar()
        imu_message.set("Accel: N/A\nGyro: N/A")
        tk.Label(root, textvariable=imu_message, height=2).grid(row=CURR_ROW+6, column=col_offset, columnspan=2)

        tk.Button(root, text="Calibrate IMU", width=15, command=calibrate_cmd(name)).grid(row=CURR_ROW+7, column=col_offset, columnspan=2)

        ui_registry[name] = {'status': status_var, 'rpm': rpm_message, 'imu': imu_message}
    
    CURR_ROW += 8

    # =========================================================
    # --- BAYESIAN OPTIMIZATION UI SECTION ---
    # =========================================================
    
    tk.Frame(root, height=2, bd=1, relief="sunken").grid(row=CURR_ROW, column=0, columnspan=6, sticky="ew", pady=15)
    CURR_ROW += 1

    tk.Label(root, text="Bayesian Optimization", font=("Arial", 12, "bold")).grid(row=CURR_ROW, column=0, columnspan=6)
    CURR_ROW += 1

    bo_status = tk.StringVar(value="BO Status: Idle")
    tk.Label(root, textvariable=bo_status, fg="blue").grid(row=CURR_ROW, column=0, columnspan=6)
    CURR_ROW += 1

    robot_reset_event = asyncio.Event()
    trial_decision_future = None

    async def run_physical_trial(rpm_combo, trial_num, total_trials):
        root.after(0, bo_status.set, f"Trial {trial_num}/{total_trials}: PLEASE RESET ROBOT. Click 'Confirm Reset' when ready.")
        await robot_reset_event.wait()
        robot_reset_event.clear()

        root.after(0, bo_status.set, f"Trial {trial_num}/{total_trials}: Running {rpm_combo}...")
        
        await robot.set_speed("SPVVVECTR1", rpm_combo[0])
        await robot.set_speed("SPVVVECTR2", rpm_combo[1])
        await robot.set_speed("SPVVVECTR3", rpm_combo[2])
        
        start_data = tracker.get_current_pos()
        start_pos = start_data[0] if start_data else None
        
        for _ in range(20):
            await asyncio.sleep(1)
            
        await robot.stop_all()
        
        final_data = tracker.get_current_pos()
        final_pos = final_data[0] if final_data else None

        if start_pos and final_pos:
            displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)
        else:
            displacement = 0.0 

        return displacement

    async def run_bo_routine():
        nonlocal trial_decision_future

        # Set this after your baseline manual testing!
        noise_variance = 150.0 

        gp = GaussianProcessRegressor(
            kernel=Matern(nu=2.5), 
            alpha=noise_variance,  
            normalize_y=True
        )

        space = [Integer(-1000, 1000), Integer(-1000, 1000), Integer(-1000, 1000)]
        opt = Optimizer(space, base_estimator=gp, acq_func="EI")
        
        lhs = Lhs(lhs_type="classic", criterion=None)
        initial_points = lhs.generate(opt.space.dimensions, 15)
        
        total_trials = 50 
        current_trial = 1

        for rpm_combo in initial_points:
            while True: 
                disp = await run_physical_trial(rpm_combo, current_trial, total_trials)
                
                root.after(0, bo_status.set, f"Trial {current_trial} Disp: {disp:.2f}mm. Save or Retry?")
                trial_decision_future = loop.create_future()
                decision = await trial_decision_future 
                
                if decision == "save":
                    opt.tell(rpm_combo, -disp) 
                    break 
                elif decision == "retry":
                    root.after(0, global_message.set, "Discarding run. Retrying...")
            current_trial += 1
            
        for _ in range(35):
            next_rpm = opt.ask()
            while True: 
                disp = await run_physical_trial(next_rpm, current_trial, total_trials)
                
                root.after(0, bo_status.set, f"Trial {current_trial} Disp: {disp:.2f}mm. Save or Retry?")
                trial_decision_future = loop.create_future()
                decision = await trial_decision_future 
                
                if decision == "save":
                    opt.tell(next_rpm, -disp)
                    break 
                elif decision == "retry":
                    root.after(0, global_message.set, "Discarding run. Retrying...")
            current_trial += 1

        root.after(0, bo_status.set, "BO Complete! Check logs for optimal gaits.")

    def start_bo_cmd():
        asyncio.run_coroutine_threadsafe(run_bo_routine(), loop)

    def confirm_reset_cmd():
        loop.call_soon_threadsafe(robot_reset_event.set)

    def save_cmd():
        if trial_decision_future and not trial_decision_future.done():
            loop.call_soon_threadsafe(trial_decision_future.set_result, "save")

    def retry_cmd():
        if trial_decision_future and not trial_decision_future.done():
            loop.call_soon_threadsafe(trial_decision_future.set_result, "retry")

    # BO Control Buttons
    tk.Button(root, text="Start Opt.", width=15, command=start_bo_cmd).grid(row=CURR_ROW, column=1)
    tk.Button(root, text="Confirm Reset", width=15, bg="yellow", command=confirm_reset_cmd).grid(row=CURR_ROW, column=2)
    tk.Button(root, text="Retry (Discard)", width=15, bg="salmon", command=retry_cmd).grid(row=CURR_ROW, column=3)
    tk.Button(root, text="Save & Next", width=15, bg="lightgreen", command=save_cmd).grid(row=CURR_ROW, column=4)
    
    # =========================================================
    # --- UI UPDATE LOOP ---
    # =========================================================
    
    async def update_data():
        for name, elements in ui_registry.items():
            try:
                status = await robot.get_status(name)
                elements['status'].set(status)

                if status == "ONLINE":
                    data = await robot.get_strut_data(name)
                    target_rpm, actual_rpm, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z = data
                    elements['rpm'].set(f"Target RPM: {target_rpm}\nActual RPM: {actual_rpm}")
                    elements['imu'].set(f"Accel: ({acc_x:.2f}, {acc_y:.2f}, {acc_z:.2f})\nGyro: ({gyro_x:.2f}, {gyro_y:.2f}, {gyro_z:.2f})")
                else:
                    elements['rpm'].set("Target RPM: N/A\nActual RPM: N/A")
                    elements['imu'].set("Accel: N/A\nGyro: N/A")
            except Exception as e:
                print(f"Error updating data for {name}: {e}")
        root.after(500, lambda: asyncio.run_coroutine_threadsafe(update_data(), loop))
        
    asyncio.run_coroutine_threadsafe(update_data(), loop)

    root.eval('tk::PlaceWindow . center')
    root.mainloop()

if __name__ == "__main__":
    main()