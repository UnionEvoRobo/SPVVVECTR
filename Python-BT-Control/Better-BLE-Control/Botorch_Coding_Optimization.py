import os
import torch 
import numpy as np
import asyncio
import math
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
from botorch.models import SingleTaskGP, ModelListGP
from gpytorch.mlls.exact_marginal_log_likelihood import ExactMarginalLogLikelihood


async def run_physical_trials(rpm_combo, trial_num, total_trials, robot, tracker):
    """Handles 20 second trials, tracking, and user choice to save/retry trial"""

    while True:

        # pause to reset robot position before next trial
        await asyncio.get_event_loop().run_in_executor(
            None, input, f"\nTrial {trial_num}/{total_trials} | reset robot position, press enter to run rpm combo: {rpm_combo}..."
        )

        print(f"Starting Trial {trial_num}...")

        # get starting position 
        start_data = QtmTracker.get_current_pos() 
        
        if start_data:
            start_pos = start_data[0]
        else:
            print("NO INITIAL STARTING POSITION FOUND (QTM ISSUE??)")

        # start motors on spvvvectr
        await robot.set_speed("SPVVVVECTR1", int(rpm_combo[0]))
        await robot.set_speed("SPVVVVECTR2", int(rpm_combo[1]))
        await robot.set_speed("SPVVVVECTR3", int(rpm_combo[2]))

        # run for 20 seconds 
        for i in range(20):
            print(f"Running... {20-i} seconds left", end="/r")
            await asyncio.sleep(1)

        # stop motors 
        await robot.stop_all()
        print("Motors Stopped")

        # get final position & calculate displacement 
        final_data = QtmTracker.get_current_pos()
        if final_data:
            final_pos = final_data[0]
        else:
            print("No final position data found")

        if start_pos and final_pos:
            displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)
        else:
            displacement = 0.0
            print("Tracking issue. Displacement not found, set to 0.0 by default")

        print(f"Displacement: {displacement:.2f} mm")

        decision = await asyncio.get_event_loop().run_in_executor(
            None, input, "Press 's' to SAVE and CONTINUE; Press 'r' to RETRY this trial: "
        )

        if decision.lower().strip() == 's':
            return displacement
        
        else:
            print("Discarding and trying again.")



def generate_random_priors(num_trials):
    """Testing random prior sampling for BO"""
    train_x = torch.randint(-1000, 1000, (num_trials, 3))
    return train_x


def generate_lhs_priors():
    """Testing prior generation with latin hypercube sampling"""

async def main():
    print("Starting robot & tracker...")

    # connect hardware 
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2) 

    # account noise from variance testing 
    noise_variance = 3799.32 

    # custom gp accounting for varying outputs
    bounds = torch.tensor([[-1000., -1000., -1000.], [1000., 1000., 1000.]])
    single_model = SingleTaskGP(likelihood=)
    
    # generate priors
    initial_points_x = generate_random_priors(15)
    # inital_points_x = generate_lhs_priors()
    print(initial_points_x)


    total_trials = 50
    current_trial = 1 

    # (1) priors - 15 trials 
    initial_points_y = []
    for rpm_combo in initial_points_x:
        initial_points_y.append(await run_physical_trials(rpm_combo, current_trial, total_trials, SPVVVECTR, QtmTracker))
        current_trial += 1
    
    # (2) optimization - 35 trials 
    #for i in range(35):
        

    # results 



    
if __name__ == "__main__":
    asyncio.run(main())


