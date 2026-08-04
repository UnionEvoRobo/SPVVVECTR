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

# Which Euler angle is rotation about the vertical axis. a1=0, a2=1, a3=2.
# Confirm by running spvvvectr_tracker.py directly and rotating the robot by hand.
YAW_INDEX = 2

NAN = float('nan')

# Per-replicate column bases, in write order.
REPLICATE_COLS = ["Displacement_mm", "X_mm", "Y_mm", "Z_mm", "Yaw_deg"]


def _unpack_pose(data):
    """Split a QTM 6DOF-euler reading into (position, yaw_degrees). (None, None) if unusable."""
    if not data:
        return None, None
    try:
        pos, euler = data
    except (TypeError, ValueError):
        return None, None

    if pos is None or any(math.isnan(v) for v in (pos.x, pos.y, pos.z)):
        return None, None

    yaw = None
    if euler is not None:
        angles = (euler.a1, euler.a2, euler.a3)
        if not math.isnan(angles[YAW_INDEX]):
            yaw = angles[YAW_INDEX]

    return pos, yaw


async def run_physical_trials(rpm_combo, trial_num, total_trials, robot: SPVVVECTR, tracker):
    """
    Handles 20 second trials, tracking, and user choice to save/retry trial.
    Returns (displacement, x, y, z, yaw_change).
    """

    while True:
        # pause to reset robot position before next trial
        await asyncio.get_event_loop().run_in_executor(
            None, input, f"\nTrial {trial_num}/{total_trials} | reset robot position, press enter to run rpm combo: {rpm_combo}..."
        )

        print(f"Starting Trial {trial_num}...")

        # get starting position — reassigned every attempt, so a retry can't reuse a stale origin
        start_pos, start_yaw = _unpack_pose(tracker.get_current_pos())
        if start_pos is None:
            print("NO INITIAL STARTING POSITION FOUND (QTM ISSUE??)")
        if not tracker.is_live():
            print("WARNING: QTM stream looks stale — data may be frozen.")

        await print_status(robot)
        await robot.set_speed(name="SPVVVECTR1", value=int(rpm_combo[0]))
        await robot.set_speed(name="SPVVVECTR2", value=int(rpm_combo[1]))
        await robot.set_speed(name="SPVVVECTR3", value=int(rpm_combo[2]))

        # run for 60 seconds
        for i in range(60):
            print(f"Running... {60-i} seconds left", end="\r")
            await asyncio.sleep(1)

        # stop motors
        await robot.stop_all()
        print("Motors Stopped                        ")

        # get final position & calculate displacement
        final_pos, final_yaw = _unpack_pose(tracker.get_current_pos())
        if final_pos is None:
            print("No final position data found")

        if start_pos is not None and final_pos is not None:
            x_displacement = final_pos.x - start_pos.x
            y_displacement = final_pos.y - start_pos.y
            z_displacement = final_pos.z - start_pos.z
            displacement = math.hypot(x_displacement, y_displacement)

            # yaw change, normalized to [-180, 180)
            if start_yaw is not None and final_yaw is not None:
                yaw_displacement = (final_yaw - start_yaw + 180) % 360 - 180
            else:
                yaw_displacement = NAN
                print("Yaw unavailable for this trial.")
        else:
            displacement = 0.0
            x_displacement = y_displacement = z_displacement = yaw_displacement = NAN
            print("Tracking issue. Displacement not found, set to 0.0 by default")

        print(f"Displacement: {displacement:.2f} mm  "
              f"(x {x_displacement:.2f}, y {y_displacement:.2f}, z {z_displacement:.2f}, "
              f"yaw {yaw_displacement:.2f} deg)")

        await print_status(robot)

        decision = await asyncio.get_event_loop().run_in_executor(
            None, input, "Press 's' to SAVE and CONTINUE; Press 'r' to RETRY this trial: "
        )

        if decision.lower().strip() == 's':
            return displacement, x_displacement, y_displacement, z_displacement, yaw_displacement

        else:
            print("Discarding and trying again.")


async def print_status(robot):
    # start motors on spvvvectrxs
    print("getting status of struts...")
    for i in range(1, 4):
        strut = f"SPVVVECTR{i}"
        status = await robot.get_status(strut)
        if status == "OFFLINE":
            try:
                await robot.connect_strut(strut)
            except Exception as E:
                pass
        status = await robot.get_status(strut)
        print(f"{strut} is {status}")


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
        writer.writerow(["Trial_Number", "Phase", "RPM_1", "RPM_2", "RPM_3"]
                        + [f"{base}_1" for base in REPLICATE_COLS])

    print(f"Saving data to: {csv_filename}")

    # connect hardware (need async)
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2)

    # noise_variance = 3799.32 # previous testing, not used anymore.

    gp = GaussianProcessRegressor(
        kernel=Matern(nu=2.5),  # the smoothness of curve
        # alpha=noise_variance,
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

    def write_trial(trial, phase, rpm, results):
        displacement, x_d, y_d, z_d, yaw_d = results
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([trial, phase, int(rpm[0]), int(rpm[1]), int(rpm[2]),
                             round(displacement, 2), round(x_d, 2), round(y_d, 2),
                             round(z_d, 2), round(yaw_d, 2)])

    if method == "random priors" or method == "lhs priors":
        print(f"Prior inputs (method: {method}): {initial_points_x}")
        for rpm_combo in initial_points_x:
            results = await run_physical_trials(rpm_combo, current_trial, total_trials, robot, tracker)
            # Force the values into standard Python integers so skopt never complains
            clean_rpm = [int(rpm_combo[0]), int(rpm_combo[1]), int(rpm_combo[2])]
            opt.tell(clean_rpm, -results[0])  # negative for max

            write_trial(current_trial, "Prior", clean_rpm, results)
            current_trial += 1

        print("Done with priors...")

    for i in range(optimize_trials):
        next_rpm = opt.ask()
        results = await run_physical_trials(next_rpm, current_trial, total_trials, robot, tracker)
        opt.tell(next_rpm, -results[0])

        write_trial(current_trial, "Optimization", next_rpm, results)
        current_trial += 1

    print("Bayesian Optimization Complete!")
    print(f"All results fully saved to {csv_filename}")

    # saving the ml model
    res = opt.get_result()
    pkl_filename = f"bo_model_{timestamp}.pkl"
    dump(res, pkl_filename)
    print(f"Gaussian Process model now dumped into {pkl_filename}")


def _next_replicate_columns(headers):
    """Return (headers + new columns, new column names, replicate index)."""
    headers = [h.strip() for h in headers]

    # tolerate the old un-numbered column from earlier runs
    if "Displacement_mm" in headers:
        headers[headers.index("Displacement_mm")] = "Displacement_mm_1"

    used = [int(h.rsplit("_", 1)[1]) for h in headers
            if h.startswith("Displacement_mm_") and h.rsplit("_", 1)[1].isdigit()]
    if not used:
        raise ValueError(f"No displacement column found in headers: {headers}")

    d_i = max(used) + 1
    new_cols = [f"{base}_{d_i}" for base in REPLICATE_COLS]
    return headers + new_cols, new_cols, d_i


async def append_displacements(csv_filename):
    """
    rerun every rpm combo in existing csv and append the results
    as a new set of {metric}_{i} columns.
    """

    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        rows = list(reader)

    headers, new_cols, d_i = _next_replicate_columns(headers)
    for row in rows:
        if "Displacement_mm" in row:
            row["Displacement_mm_1"] = row.pop("Displacement_mm")
        for col in new_cols:
            row[col] = ""

    stem, ext = os.path.splitext(csv_filename)
    stem = re.sub(r"_r\d+$", "", stem)
    out_filename = f"{stem}_r{d_i}{ext}"

    if os.path.exists(out_filename):
        raise FileExistsError(f"{out_filename} already exists — pass the latest file, not the original.")

    def flush():
        with open(out_filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, headers, restval="", extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)

    flush()
    print(f"Replicate {d_i} of {len(rows)} combos -> {out_filename}")

    print("Starting Robot & Tracker...")
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2)

    for n, row in enumerate(rows, start=1):
        rpm_combo = [int(row["RPM_1"]), int(row["RPM_2"]), int(row["RPM_3"])]
        print(f"Re-running combo {n}/{len(rows)}: {rpm_combo}")
        results = await run_physical_trials(rpm_combo, n, len(rows), robot, tracker)
        for col, value in zip(new_cols, results):
            row[col] = round(value, 2)
        flush()

    print(f"Replicate {d_i} complete. Results saved to {out_filename}")


def add_mean_column(csv_filename, num_replicates=3):
    """
    Add a {metric}_mean column for every metric that has all replicate columns present.
    Writes to {stem}_mean.csv.
    """
    with open(csv_filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        headers = [h.strip() for h in reader.fieldnames]
        rows = list(reader)

    means = []  # (new_col, [source cols])
    for base in REPLICATE_COLS:
        cols = [f"{base}_{i}" for i in range(1, num_replicates + 1)]
        if all(c in headers for c in cols):
            means.append((f"{base}_mean", cols))

    if not means:
        raise ValueError(f"No complete replicate set found in: {headers}")

    headers = headers + [new_col for new_col, _ in means]

    for n, row in enumerate(rows, start=1):
        for new_col, cols in means:
            try:
                values = [float(row[c]) for c in cols]
            except (TypeError, ValueError):
                raise ValueError(f"Row {n} has a blank or non-numeric value in {cols}: "
                                 f"{[row[c] for c in cols]}")
            row[new_col] = round(sum(values) / len(values), 2)

    stem, ext = os.path.splitext(csv_filename)
    out_filename = f"{stem}_mean{ext}"
    with open(out_filename, 'w', newline='') as file:
        writer = csv.DictWriter(file, headers, restval="", extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Mean columns {[c for c, _ in means]} added for {len(rows)} rows -> {out_filename}")
    return out_filename


async def main():

    """ experiment 1 """
    # await bayesian_optimization("random priors")
    # await append_displacements("./bo_spvvvectr-1b-randoms.csv")
    # add_mean_column("./bo_spvvvectr-1b-randoms_r3.csv")

    """ experiment 2 """
    await bayesian_optimization("lhs priors")

    """ experiment 3 """
    # await bayesian_optimization("no priors")


if __name__ == "__main__":
    asyncio.run(main())