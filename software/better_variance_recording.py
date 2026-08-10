import asyncio
import csv
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR
import bo_skopt

STRUTS = ["SPVVVECTR1", "SPVVVECTR2", "SPVVVECTR3"]


async def keep_struts_connected(robot, poll_seconds=1):
    """
    Background watchdog: if a strut drops off BLE mid-run, reconnect it.
    Cancel this task when the run finishes.
    """
    while True:
        for strut in STRUTS:
            try:
                if await robot.get_status(strut) != "ONLINE":
                    print(f"{strut} is not online! Attempting to reconnect...")
                    await robot.connect_strut(strut)
            except Exception as e:
                print(f"Reconnect attempt for {strut} failed: {e}")
        await asyncio.sleep(poll_seconds)


async def variance_recording(rpm, num_trials):
    print("Initializing Robot and Tracker...")

    # connect to robot/qualisys
    robot = SPVVVECTR()
    await robot.connect_all()
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2)

    for strut in STRUTS:
        print(f"{strut} status:", await robot.get_status(strut))

    # initialize csv file
    csv_filename = f"variance_results_{rpm}.csv"
    with open(csv_filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Trial_Number", "M1", "M2", "M3",
                         "Displacement_mm", "Yaw_rotation_deg"])

    watchdog = asyncio.create_task(keep_struts_connected(robot))

    try:
        for i in range(num_trials):
            displacement, x_diff, y_diff, z_diff, yaw_rotation = \
                await bo_skopt.run_physical_trials(rpm, i + 1, num_trials, robot, tracker)

            # append to csv
            with open(csv_filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([i + 1, rpm[0], rpm[1], rpm[2],
                                 f'{displacement:.2f}', f'{yaw_rotation:.2f}'])

            print(f"Appended to {csv_filename}")
    finally:
        watchdog.cancel()
        try:
            await watchdog
        except asyncio.CancelledError:
            pass
        await robot.stop_all()

    print(f"\n{num_trials} trials complete. Results in {csv_filename}")


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
