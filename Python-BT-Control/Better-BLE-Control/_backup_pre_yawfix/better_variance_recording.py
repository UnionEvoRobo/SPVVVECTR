import asyncio
import csv
import os
import bo_skopt
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR


async def variance_recording(rpm, num_trials):
    print("Initializing Robot and Tracker...")

    # connect to robot/qualisys
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2)

    # initialize csv file
    rpm_tag = "_".join(str(int(v)) for v in rpm)
    csv_filename = f"variance_results_{rpm_tag}.csv"

    if os.path.exists(csv_filename):
        raise FileExistsError(f"{csv_filename} already exists — move or rename it first.")

    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Trial_Number", "Linear_Displacement_mm", "x_change_mm",
                         "y_change_mm", "z_change_mm", "yaw_change_deg"])

    print(f"Saving data to: {csv_filename}")

    for i in range(num_trials):
        displacement, x_d, y_d, z_d, yaw_d = await bo_skopt.run_physical_trials(
            rpm, i + 1, num_trials, robot, tracker
        )

        # append to csv
        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([i + 1, f'{displacement:.2f}', f'{x_d:.2f}',
                             f'{y_d:.2f}', f'{z_d:.2f}', f'{yaw_d:.2f}'])

        print(f"Appended trial {i + 1} to {csv_filename}")


async def main():
    # top 3 best observed trials from spvvvectr-1b BO w/ LHS priors; means of 3 trials each
    rpm1 = [982, 414, -301]
    rpm2 = [1000, 417, -243]
    rpm3 = [-914, -379, 981]
    num_trials = 10

    await variance_recording(rpm1, num_trials)
    # await variance_recording(rpm2, num_trials)
    # await variance_recording(rpm3, num_trials)


if __name__ == "__main__":
    asyncio.run(main())