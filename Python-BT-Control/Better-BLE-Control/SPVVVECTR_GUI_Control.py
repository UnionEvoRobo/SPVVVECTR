from SPVVVECTR_Class import SPVVVECTR
from spvvvectr_tracker import QtmTracker # Import your refactored tracker
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
    tracker = QtmTracker("10.76.30.85")

    # Main app window and title
    root = tk.Tk()
    root.title("SPVVVECTR Control & Optimization")
    root.minsize(800, 400) # Slightly wider to accommodate new buttons
    tk.Label(root, text="Tensegrity Control", font=("Arial", 14, "bold")).grid(
        row=CURR_ROW, column=0, columnspan=5, pady=5)
    CURR_ROW += 1

    # Global message Setup
    global_message = tk.StringVar()
    global_message.set("Welcome to the Tensegrity Control Panel!")

    # ... [ASSUMING ALL YOUR EXISTING BUTTONS ARE KEPT HERE] ...
    # (Connect All, Speed Entry, UI Registry, etc.)

    # =========================================================
    # --- BAYESIAN OPTIMIZATION UI SECTION ---
    # =========================================================
    
    # Visual Separator
    tk.Frame(root, height=2, bd=1, relief="sunken").grid(row=CURR_ROW, column=0, columnspan=5, sticky="ew", pady=10)
    CURR_ROW += 1

    tk.Label(root, text="Bayesian Optimization", font=("Arial", 12, "bold")).grid(
        row=CURR_ROW, column=0, columnspan=5)
    CURR_ROW += 1

    bo_status = tk.StringVar(value="BO Status: Idle")
    tk.Label(root, textvariable=bo_status, fg="blue").grid(row=CURR_ROW, column=0, columnspan=5, sticky="w")
    CURR_ROW += 1

    # Async events for halting the loop
    robot_reset_event = asyncio.Event()
    trial_decision_future = None # Will hold the Save/Retry decision

    # 1. The Physical Trial Logic
    async def run_physical_trial(rpm_combo, trial_num, total_trials):
        root.after(0, bo_status.set, f"Trial {trial_num}/{total_trials}: PLEASE RESET ROBOT. Click 'Confirm Reset' when ready.")
        await robot_reset_event.wait()
        robot_reset_event.clear()

        root.after(0, bo_status.set, f"Trial {trial_num}/{total_trials}: Running {rpm_combo}...")
        
        await robot.set_speed("SPVVVECTR1", rpm_combo[0])
        await robot.set_speed("SPVVVECTR2", rpm_combo[1])
        await robot.set_speed("SPVVVECTR3", rpm_combo[2])
        
        # FIX: Append [0] to extract position from the (pos, rot) tuple
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

    # 2. The Main BO Loop
    async def run_bo_routine():
        nonlocal trial_decision_future

        # Accounting for noise (Update this value after your baseline variance test)
        # noise_variance = 150.0 

        # Define custom gaussian process expecting physical trial noise 
        gp = GaussianProcessRegressor(
            kernel=Matern(nu=2.5), # Added missing comma here
            alpha=noise_variance,  # Tells the math not to perfectly trust results 
            normalize_y=True
        )

        space = [Integer(-1000, 1000), Integer(-1000, 1000), Integer(-1000, 1000)]
        # Pass the custom GP as the base_estimator
        opt = Optimizer(space, base_estimator=gp, acq_func="EI")
        
        lhs = Lhs(lhs_type="classic", criterion=None)
        initial_points = lhs.generate(opt.space.dimensions, 15)
        
        total_trials = 50 
        current_trial = 1

        # Phase 1: Priors
        for rpm_combo in initial_points:
            while True: # Loop allows us to retry the exact same RPM if needed
                disp = await run_physical_trial(rpm_combo, current_trial, total_trials)
                
                # Decision Gate
                root.after(0, bo_status.set, f"Trial {current_trial} Disp: {disp:.2f}mm. Save or Retry?")
                trial_decision_future = loop.create_future()
                decision = await trial_decision_future 
                
                if decision == "save":
                    opt.tell(rpm_combo, -disp) 
                    break # Exit the while loop, move to next prior
                elif decision == "retry":
                    root.after(0, global_message.set, "Discarding run. Retrying...")
            
            current_trial += 1
            
        # Phase 2: Optimization
        for _ in range(35):
            next_rpm = opt.ask()
            while True: 
                disp = await run_physical_trial(next_rpm, current_trial, total_trials)
                
                # Decision Gate
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

    # 3. GUI Buttons to control the loop
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

    # Placing the 4 BO control buttons in a row
    tk.Button(root, text="Start Opt.", width=15, command=start_bo_cmd).grid(row=CURR_ROW, column=1)
    tk.Button(root, text="Confirm Reset", width=15, bg="yellow", command=confirm_reset_cmd).grid(row=CURR_ROW, column=2)
    tk.Button(root, text="Retry (Discard)", width=15, bg="salmon", command=retry_cmd).grid(row=CURR_ROW, column=3)
    tk.Button(root, text="Save & Next", width=15, bg="lightgreen", command=save_cmd).grid(row=CURR_ROW, column=4)
    CURR_ROW += 1

    # =========================================================

    root.eval('tk::PlaceWindow . center')
    root.mainloop()

if __name__ == "__main__":
    main()