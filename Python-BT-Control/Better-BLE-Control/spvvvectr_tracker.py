import asyncio
import qtm_rt
import math

class QtmTracker():
    def __init__(self, ip, loop=None):
        self.ip = ip
        self.connection = None
        self.latest_position = None
        
        # Start the async loop in the background
        self.loop = loop or asyncio.get_event_loop()
        self.loop.create_task(self._run_tracker())

    async def _run_tracker(self):
        """Background task to maintain connection and continuous stream."""
        await self._connect_to_qtm()
        if self.connection:
            print("Im connected to qtm W!")
            # Stream continuously, pushing data to the callback
            await self.connection.stream_frames(components=["6d"], on_packet=self._on_packet)

    async def _connect_to_qtm(self):
            """Attempts to connect to QTM until successful."""
            while self.connection is None:
                print(f"Attempting to connect to {self.ip}...")
                try:
                    # Force a 5-second timeout on the connection attempt
                    self.connection = await asyncio.wait_for(qtm_rt.connect(self.ip), timeout=5.0)
                    print("Connected to QTM W!")
                except asyncio.TimeoutError:
                    print("Connection timed out. The QTM desktop is ignoring us.")
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Connection failed: {e}. Retrying in 2s...")
                    await asyncio.sleep(2)

    def _on_packet(self, packet):
        """Callback fired by qtm_rt every time a frame arrives."""
        info, bodies = packet.get_6d_euler()    #Change to Euler for readability
        
        # Assuming you just want the first tracked body for now
        for index, position in enumerate(bodies):
            # Update the state continuously in the background
            self.latest_position = position

    def get_current_pos(self) -> tuple:
        """
        Non-blocking getter for the main thread to grab the latest data.
        Return: ((x, y, z), (yaw, pitch, roll))
        """
        return self.latest_position

# --- Main ---
async def main():
    tracker = QtmTracker("10.76.30.85")
    first_pos = ()
    last_pos = ()
    
    # Simulate your Bayesian Optimization loop
    for i in range(50):
        raw_data = tracker.get_current_pos()
        #print(f"Algorithm reading current position: {pos}")

        if raw_data is not None:
            # seperate position & rotation data 
            pos_data, rot_data = raw_data

            # get current coords
            current_x = pos_data.x
            current_y = pos_data.y
            current_z = pos_data.z
            current_yaw = rot_data.yaw

            print(f"X: {current_x:.2f}, Y: {current_y:.2f}, Z: {current_z:.2f}, Yaw: {current_yaw:.2f}")
        
        await asyncio.sleep(0.1)  # Read data ten times a second
    


if __name__ == "__main__":
    asyncio.run(main())
