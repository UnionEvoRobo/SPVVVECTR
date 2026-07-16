import asyncio
import math
from spvvvectr_tracker import QtmTracker
from SPVVVECTR_Class import SPVVVECTR  # Import your Bluetooth controller

async def main():
    print("Initializing Robot and Tracker...")
    
    # 1. Initialize and connect to the robot
    robot = SPVVVECTR()
    print("Connecting to struts via Bluetooth...")
    await robot.connect_all()
    print("✅ Robot connected!")
    print("Strut 1 Status:", await robot.get_status("SPVVVECTR1"))
    print("Strut 2 Status:", await robot.get_status("SPVVVECTR2"))
    print("Strut 3 Status:", await robot.get_status("SPVVVECTR3"))

    # 2. Initialize the Qualisys tracker (Make sure IP matches your lab setup)
    tracker = QtmTracker("10.76.30.85")
    await asyncio.sleep(2) # Give the stream a second to stabilize
    
    print("\n" + "="*40)
    print("   BASELINE VARIANCE TESTER READY")
    print("="*40)

    # ---------------------------------------------------------
    # CHANGE THIS ARRAY FOR EACH OF YOUR 3 TEST GAITS!
    test_rpm = [1000, 1000, 1000] 
    # ---------------------------------------------------------

    trial_number = 1

    # Loop exactly 10 times for the current gait
    while trial_number <= 10:
        
        # 1. Wait for human input 
        # (We use run_in_executor so the input() prompt doesn't freeze the Qualisys background stream)
        await asyncio.get_event_loop().run_in_executor(
            None, input, f"\n[Trial {trial_number}/10] Reset robot. Press ENTER to test {test_rpm}..."
        )
        
        # 2. Get Starting Position
        start_data = tracker.get_current_pos()
        start_pos = start_data[0] if start_data else None
        
        if not start_pos:
            print("❌ Error: No tracking data. Are the cameras blocked?")
            continue
            
        print(f"Tracking started at X: {start_pos.x:.1f}, Y: {start_pos.y:.1f}")
        print("Spinning up motors...")
        
        # 3. START MOTORS
        await robot.set_speed("SPVVVECTR1", test_rpm[0])
        await robot.set_speed("SPVVVECTR2", test_rpm[1])
        await robot.set_speed("SPVVVECTR3", test_rpm[2])
        
        # 4. Wait exactly 20 seconds
        for i in range(20):
            print(f"Running... {20-i} seconds left", end="\r")
            await asyncio.sleep(1)
            
        # 5. STOP MOTORS
        await robot.stop_all()
        print("Motors stopped.                    ") # Extra spaces to clear the countdown text
        
        # 6. Get Final Position
        final_data = tracker.get_current_pos()
        final_pos = final_data[0] if final_data else None
        
        if not final_pos:
            print("\n❌ Error: Tracking lost at the end of the trial.")
            continue

        # 7. Calculate Displacement
        displacement = math.sqrt((final_pos.x - start_pos.x)**2 + (final_pos.y - start_pos.y)**2)
        
        print(f"✅ Trial {trial_number} Complete!")
        print(f"📏 Total Displacement: {displacement:.2f} mm")
        print("-" * 40)
        
        trial_number += 1

    print("\n🎉 10 trials complete! Write down your numbers, change 'test_rpm' in the code, and run again for the next gait.")
    try:
        robot.stop_all()
    except Exception as e:
        pass
    

if __name__ == "__main__":
    asyncio.run(main())