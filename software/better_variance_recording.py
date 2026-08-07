import asyncio
import math
import csv
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
import bo_skopt

async def variance_recording(rpm, num_trials):
    print("Initializing Robot and Tracker...")

    # connect to robot/qualisys
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2) 

    # initialize csv file
    csv_filename = f"variance_results_{rpm}.csv"
    with open(csv_filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Trial_Number", "Displacement_mm"])

    for i in range(num_trials):
        displacement = await bo_skopt.run_physical_trials(rpm, i + 1, num_trials, robot, tracker)

        # append to csv
        with open(csv_filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([i + 1, f'{displacement:.2f}'])

        print(f"Appended to {csv_filename}")

async def main():
    # top 3 best observed trials from spvvvectr-1b BO w/ LHS priors; means of 3 trials each
    rpm = [1000, 1000, 1000]
    #rpm1 = [886, -24, 479]
    #line_gait = [982, 414, -301]
    #rpm2 = [907, 136, 532]
    #rpm3 = [879, 41, 523]
    num_trials = 20
    
    await variance_recording(rpm, num_trials)


if __name__ == "__main__":
    asyncio.run(main())



        
        
    

