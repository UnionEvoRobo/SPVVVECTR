import numpy as np
import asyncio
import math
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
from skopt import Optimizer
from skopt.space import Integer
from skopt.sampler import Lhs
from skopt.learning import GaussianProcessRegressor
from skopt.learning.gaussian_process.kernels import Matern 


async def run_physical_trials(rpm_combo, trial_num, total_trials, robot:SPVVVECTR, tracker):
    """Handles 20 second trials, tracking, and user choice to save/retry trial"""

    while True:

        # pause to reset robot position before next trial
        await asyncio.get_event_loop().run_in_executor(
            None, input, f"\nTrial {trial_num}/{total_trials} | reset robot position, press enter to run rpm combo: {rpm_combo}..."
        )

        print(f"Starting Trial {trial_num}...")

        # get starting position 
        start_data = tracker.get_current_pos() 
        
        if start_data:
            start_pos = start_data[0]
        else:
            print("NO INITIAL STARTING POSITION FOUND (QTM ISSUE??)")

        await print_status(robot)
        await robot.set_speed(name="SPVVVECTR1", value=int(rpm_combo[0]))
        await robot.set_speed(name="SPVVVECTR2", value=int(rpm_combo[1]))
        await robot.set_speed(name="SPVVVECTR3", value=int(rpm_combo[2]))

        # run for 20 seconds 
        for i in range(20):
            print(f"Running... {20-i} seconds left", end="\r")
            await asyncio.sleep(1)

        # stop motors 
        await robot.stop_all()
        print("Motors Stopped")

        # get final position & calculate displacement 
        final_data = tracker.get_current_pos()
        if final_data:
            final_pos = final_data[0]
        else:
            print("No final position data found")

        if start_pos and final_pos:
            displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)

            if math.isnan(displacement):
                print("Displacement was nan for some reason, maybe qualisys. retry!")
                displacement = 0.0

        else:
            displacement = 0.0
            print("Tracking issue. Displacement not found, set to 0.0 by default")

        print(f"Displacement: {displacement:.2f} mm")

        await print_status(robot)

        decision = await asyncio.get_event_loop().run_in_executor(
            None, input, "Press 's' to SAVE and CONTINUE; Press 'r' to RETRY this trial: "
        )

        if decision.lower().strip() == 's':
            return displacement
        
        else:
            print("Discarding and trying again.")



async def print_status(robot):
    # start motors on spvvvectrxs
    print("getting status of struts...")
    for i in range (1,4):
        strut = f"SPVVVECTR{i}"
        status = await robot.get_status(strut)
        if status == "OFFLINE":
            try:
                await robot.connect_strut(strut)
            except Exception as E:
                pass
        status = await robot.get_status(strut)
        print (f"{strut} is {status}")

def generate_random_priors(num_trials):
    """Testing random prior sampling for BO"""
    train_x = np.random.randint(-1000, 1000, size=(num_trials, 3))
    return train_x

def generate_lhs_priors(opt):
    """Testing prior generation with latin hypercube sampling"""
    lhs = Lhs(lhs_type="classic", criterion=None)
    initial_points = lhs.generate(opt.space.dimensions, 15)
    return initial_points

async def main():
    print("Starting robot & tracker...")

    # connect hardware 
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2) 

    # account noise from variance testing 
    noise_variance = 3799.32 

    gp = GaussianProcessRegressor(
        kernel=Matern(nu=2.5), # the smoothness of curve
        alpha=noise_variance,
        normalize_y=True
    )

    bounds = [Integer(-1000, 1000), Integer(-1000, 1000), Integer(-1000, 1000)]
    opt = Optimizer(bounds, base_estimator=gp, acq_func="EI")

    
    # generate priors
    initial_points_x = generate_random_priors(15)
    #inital_points_x = generate_lhs_priors(opt)

    total_trials = 50
    current_trial = 1 

    # (1) priors - 15 trials 

    print(f"Prior inputs are: {initial_points_x}")
    for rpm_combo in initial_points_x:
        displacement = await run_physical_trials(rpm_combo, current_trial, total_trials, robot, tracker)
        opt.tell(rpm_combo.tolist(), -displacement) # negative for max
        current_trial += 1
    
    print("Done with priors...")
    
    # (2) optimization - 35 trials 
    for i in range(35):
        next_rpm = opt.ask()
        displacement = await run_physical_trials(next_rpm, current_trial, total_trials, robot, tracker)
        opt.tell(next_rpm, -displacement)
        current_trial += 1
        

    # results 
    print("Bayesian Optimization Complete!")
    best_index = opt.yi.index(min(opt.yi))
    best_rpm = opt.Xi[best_index]
    best_displacement = -opt.yi[best_index]

    print(f"Best Gait is: {best_rpm}")
    print(f"Results in max displacement of: {best_displacement:.2f} mm")
    
if __name__ == "__main__":
    asyncio.run(main())


