import numpy as np
import asyncio
import math
import csv
import os
import re
from datetime import datetime
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
from skopt import Optimizer
from skopt import dump
from skopt.space import Integer
from skopt.sampler import Lhs
from skopt.learning import GaussianProcessRegressor
from skopt.learning.gaussian_process.kernels import Matern 

async def run_single_trial(rpm_combo, robot, seconds):
    """Handles 20 second single trial"""

    print(f"Starting Trial...")

    await print_status(robot)
    await robot.set_speed(name="SPVVVECTR1", value=int(rpm_combo[0]))
    await robot.set_speed(name="SPVVVECTR2", value=int(rpm_combo[1]))
    await robot.set_speed(name="SPVVVECTR3", value=int(rpm_combo[2]))

    for i in range(seconds):
        print(f"Running... {seconds-i} seconds left", end="\r")
        await asyncio.sleep(1)

    await robot.stop_all()
    




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
        start_pos = None
        start_yaw = None

        if start_data:
            start_pos = start_data[0]
            # tracker streams 6deuler, so [1] carries Euler angles; a1 is yaw
            start_yaw = start_data[1].a1
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
        print("Motors Stopped                        ")

        # get final position & calculate displacement
        final_data = tracker.get_current_pos()
        final_pos = None
        final_yaw = None
        if final_data:
            final_pos = final_data[0]
            final_yaw = final_data[1].a1
        else:
            print("No final position data found")

        if start_pos and final_pos:
            displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)
            x_diff = final_pos.x - start_pos.x
            y_diff = final_pos.y - start_pos.y
            z_diff = final_pos.z - start_pos.z

            if start_yaw is not None and final_yaw is not None:
                yaw_rotation = final_yaw - start_yaw
            else:
                yaw_rotation = 0.0

            if math.isnan(displacement):
                print("Displacement was nan for some reason, maybe qualisys. retry!")
                displacement = 0.0

        else:
            displacement = 0.0
            x_diff = y_diff = z_diff = 0.0
            yaw_rotation = 0.0
            print("Tracking issue. Displacement not found, set to 0.0 by default")

        print(f"Displacement: {displacement:.2f} mm | Yaw: {yaw_rotation:.2f} deg")

        await print_status(robot)

        decision = await asyncio.get_event_loop().run_in_executor(
            None, input, "Press 's' to SAVE and CONTINUE; Press 'r' to RETRY this trial: "
        )

        if decision.lower().strip() == 's':
            return displacement, x_diff, y_diff, z_diff, yaw_rotation
        
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


async def bayesian_optimization(method):
    """
    Runs the full Bayesian Optimization process with the specified method for generating priors.
    method: str - "random priors", "lhs priors", or "no priors"
    """

    print("Starting Robot & Tracker...")

    # csv
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"bo_results_{timestamp}.csv"

    # initialize the file and write the header row
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Trial_Number", "Phase", "RPM_1", "RPM_2", "RPM_3", "Displacement_mm",
                         "X_diff_mm", "Y_diff_mm", "Z_diff_mm", "Yaw_rotation_deg"])


    print(f"Saving data to: {csv_filename}")

    # connect hardware (need async)
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2)

    # noise_variance = 3799.32 # previous testing, not used anymore.

    gp = GaussianProcessRegressor(
        kernel=Matern(nu=2.5), # the smoothness of curve
        #alpha=noise_variance,
        normalize_y=True,
        noise='gaussian'
    )

    bounds = [Integer(-1000, 1000), Integer(-1000, 1000), Integer(-1000, 1000)]
    opt = Optimizer(bounds, base_estimator=gp, acq_func="EI")

    total_trials = 50
    optimize_trials = 35
    current_trial = 1

    if method == "random priors":
        initial_points_x = generate_random_priors(15)

    elif method == "lhs priors":
        initial_points_x = generate_lhs_priors(opt)

    else:
        optimize_trials = 50
        opt = Optimizer(bounds, base_estimator=gp, acq_func="EI", n_initial_points=1)

    if method == "random priors" or method == "lhs priors":
        print(f"Prior inputs (method: {method}): {initial_points_x}")
        for rpm_combo in initial_points_x:
            displacement, x_diff, y_diff, z_diff, yaw_rotation = await run_physical_trials(rpm_combo, current_trial, total_trials, robot, tracker)
            # Force the values into standard Python integers so skopt never complains
            clean_rpm = [int(rpm_combo[0]), int(rpm_combo[1]), int(rpm_combo[2])]
            opt.tell(clean_rpm, -displacement) # negative for max
            
            # save each trial to csv 
            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([current_trial, "Prior", int(rpm_combo[0]), int(rpm_combo[1]), int(rpm_combo[2]), round(displacement, 2),
                                 round(x_diff, 2), round(y_diff, 2), round(z_diff, 2), round(yaw_rotation, 2)])
            
            current_trial += 1
        
        print("Done with priors...")

    for i in range(optimize_trials):
        next_rpm = opt.ask()
        displacement, x_diff, y_diff, z_diff, yaw_rotation = await run_physical_trials(next_rpm, current_trial, total_trials, robot, tracker)
        opt.tell(next_rpm, -displacement)
        
        # save each trial to csv 
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_trial, "Optimization", int(next_rpm[0]), int(next_rpm[1]), int(next_rpm[2]), round(displacement, 2),
                             round(x_diff, 2), round(y_diff, 2), round(z_diff, 2), round(yaw_rotation, 2)])
            
        current_trial += 1

    print("Bayesian Optimization Complete!")
    print(f"All results fully saved to {csv_filename}")
    
    # saving the ml model 
    res = opt.get_result()
    pkl_filename = f"bo_model_{timestamp}.pkl"
    dump(res, pkl_filename)
    print(f"Gaussian Process model now dumped into {pkl_filename}")


def _next_displacement_column(headers):
    """Return (headers + new column, new column name, header index)."""
    
    # used = [int(h.rsplit("_", 1)[1]) for h in headers
    #         if h.startswith("Displacement_mm_")]

    for header in headers:
        if header.startswith("Displacement_mm_"):
            used = [int(header.rsplit("_", 1)[1])]
    
    d_i = max(used) + 1
    new_col = f"Displacement_mm_{d_i}"
    return headers + [new_col], new_col, d_i

async def append_displacements(csv_filename):
    """
    rerun every rpm combo in existing csv and append the displacements 
    as a new Displacement_mm_{i} column.
    """

    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)

        headers, new_col, d_i = _next_displacement_column(headers)
        for row in rows:
            row[new_col] = ""

        stem, ext = os.path.splitext(csv_filename)
        stem = re.sub(r"_r\d+$", "", stem)
        out_filename = f"{stem}_r{d_i}{ext}"

        def flush():
            with open(out_filename, 'w', newline='') as file:
                writer = csv.DictWriter(file, headers)
                writer.writeheader()
                writer.writerows(rows)

        flush()
        print(f"d_i {d_i} of {len(rows)} combos -> {out_filename}")

        print("Starting Robot & Tracker...")
        robot = SPVVVECTR()
        await robot.connect_all()
        tracker = QtmTracker("10.76.30.85")
        await asyncio.sleep(2)

        order = list(range(len(rows)))

        for n, index in enumerate(order, start=1):
            row = rows[index]
            rpm_combo = [int(row["RPM_1"]), int(row["RPM_2"]), int(row["RPM_3"])]
            print(f"Re-running combo {n}/{len(rows)}: {rpm_combo}")
            displacement, x_diff, y_diff, z_diff, yaw_rotation = await run_physical_trials(rpm_combo, n, len(order), robot, tracker)
            row[new_col] = round(displacement, 2)
            flush()

        print(f"Column {d_i} complete. Results saved to {out_filename}")

def add_mean_column(csv_filename):
    """
    Add a Displacement_mm_mean column averaging the three replicate columns.
    Writes to {stem}_mean.csv.
    """
    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        headers = [h.strip() for h in reader.fieldnames]
        rows = list(reader)

    cols = [f"Displacement_mm_{i}" for i in (1, 2, 3)]
    missing = [c for c in cols if c not in headers]
    if missing:
        raise ValueError(f"Missing column(s): {missing}. Found: {headers}")

    new_col = "Displacement_mm_mean"
    headers = headers + [new_col]

    for n, row in enumerate(rows, start=1):
        try:
            values = [float(row[c]) for c in cols]
        except (TypeError, ValueError):
            raise ValueError(f"Row {n} has a blank or non-numeric displacement: "
                            f"{[row[c] for c in cols]}")
        row[new_col] = round(sum(values) / len(values), 2)

    stem, ext = os.path.splitext(csv_filename)
    out_filename = f"{stem}_mean{ext}"
    with open(out_filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Mean column added for {len(rows)} rows -> {out_filename}")
    return out_filename


async def main():

   #await bayesian_optimization("lhs priors")
    #await append_displacements("./bo_spvvvectr-1b-lhs_r2.csv")
    #add_mean_column("./bo_spvvvectr-1b-lhs_r3.csv")
    #await run_physical_trials([982, 414, -301], 1, 1, robot=SPVVVECTR(), tracker=QtmTracker("10.76.30.85"))


    robot=SPVVVECTR()
    # await robot.connect_all()
    # await run_single_trial([982, 414, -301], robot, 20)



if __name__ == "__main__":
    asyncio.run(main())