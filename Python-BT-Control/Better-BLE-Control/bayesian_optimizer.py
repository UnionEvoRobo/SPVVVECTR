import asyncio
import math
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
from skopt import Optimizer
from skopt.space import Integer
from skopt.sampler import Lhs
from skopt.learning import GaussianProcessRegressor
from skopt.learning.gaussian_process.kernels import Matern 

async def run_physical_trial(rpm_combo, trial_num, total_trials, robot, tracker):
    """Handles the 20-second run, tracking, and the Save/Retry decision."""
    while True:
        # 1. The Human Reset Pause
        # Using run_in_executor so input() doesn't block background tracking
        await asyncio.get_event_loop().run_in_executor(
            None, input, f"\n[Trial {trial_num}/{total_trials}] PLEASE RESET ROBOT. Press ENTER to run {rpm_combo}..."
        )
        
        print(f"Starting trial {trial_num}...")
        
        # 2. Get Starting Position
        start_data = tracker.get_current_pos()
        start_pos = start_data[0] if start_data else None
        if not start_pos:
            print("⚠️ Warning: No starting tracking data found.")
            
        # 3. Spin up motors
        await robot.set_speed("SPVVVECTR1", int(rpm_combo[0]))
        await robot.set_speed("SPVVVECTR2", int(rpm_combo[1]))
        await robot.set_speed("SPVVVECTR3", int(rpm_combo[2]))
        
        # 4. Wait exactly 20 seconds
        for i in range(20):
            print(f"Running... {20-i} seconds left", end="\r")
            await asyncio.sleep(1)
            
        # 5. Stop motors
        await robot.stop_all()
        print("Motors stopped.                    ")
        
        # 6. Get Final Position & Calculate Displacement
        final_data = tracker.get_current_pos()
        final_pos = final_data[0] if final_data else None

        if start_pos and final_pos:
            displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)
        else:
            displacement = 0.0
            print("⚠️ Warning: Tracking lost. Displacement recorded as 0.0")

        print(f"📏 Displacement: {displacement:.2f} mm")

        # 7. The Save or Retry Decision Gate
        decision = await asyncio.get_event_loop().run_in_executor(
            None, input, "Type 's' to SAVE & NEXT, or 'r' to RETRY this run: "
        )
        
        if decision.lower().strip() == 's':
            return displacement
        else:
            print("🔄 Discarding run. Retrying the exact same RPM combination...")


async def main():
    print("Initializing Robot and Tracker...")
    
    # Connect hardware
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2) 
    
    print("\n" + "="*50)
    print("   BAYESIAN OPTIMIZATION EXPERIMENT STARTED")
    print("="*50)

    # --- BO SETUP ---
    noise_variance = 150.0  # Remember to update this with your baseline test result
    
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

    # --- PHASE 1: PRIORS (15 Trials) ---
    print("\n--- PHASE 1: LHS PRIORS ---")
    for rpm_combo in initial_points:
        disp = await run_physical_trial(rpm_combo, current_trial, total_trials, robot, tracker)
        opt.tell(rpm_combo, -disp) # Negate for maximization
        current_trial += 1
        
    # --- PHASE 2: OPTIMIZATION (35 Trials) ---
    print("\n--- PHASE 2: BAYESIAN OPTIMIZATION ---")
    for _ in range(35):
        next_rpm = opt.ask()
        disp = await run_physical_trial(next_rpm, current_trial, total_trials, robot, tracker)
        opt.tell(next_rpm, -disp)
        current_trial += 1

    # --- RESULTS ---
    print("\n" + "="*50)
    print("🎉 EXPERIMENT COMPLETE 🎉")
    print("="*50)
    
    # Retrieve the best result the optimizer found
    best_idx = opt.yi.index(min(opt.yi)) # skopt minimizes, so the minimum negative is the max displacement
    best_rpm = opt.Xi[best_idx]
    best_disp = -opt.yi[best_idx]
    
    print(f"🏆 Best Gait Found: {best_rpm}")
    print(f"📏 Max Displacement: {best_disp:.2f} mm")

if __name__ == "__main__":
    asyncio.run(main())