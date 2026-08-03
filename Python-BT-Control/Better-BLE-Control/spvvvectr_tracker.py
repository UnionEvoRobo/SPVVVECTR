import asyncio
import qtm_rt
import math
import time


class QtmTracker():
    def __init__(self, ip, loop=None):
        self.ip = ip
        self.connection = None
        self.latest_position = None
        self.latest_frame = None
        self.last_update = None

        # Start the async loop in the background
        self.loop = loop or asyncio.get_event_loop()
        self.loop.create_task(self._run_tracker())

    async def _run_tracker(self):
        """Background task to maintain connection and continuous stream."""
        await self._connect_to_qtm()
        if self.connection:
            print("Im connected to qtm W!")
            # Stream continuously, pushing data to the callback
            await self.connection.stream_frames(components=["6deuler"], on_packet=self._on_packet)

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
        info, bodies = packet.get_6d_euler()

        # Assuming you just want the first tracked body for now
        for index, body in enumerate(bodies):
            # body is a (RT6DBodyPosition, RT6DBodyEuler) tuple
            self.latest_position = body

        self.latest_frame = packet.framenumber
        self.last_update = time.monotonic()

    def get_current_pos(self):
        """Non-blocking getter. Returns (RT6DBodyPosition, RT6DBodyEuler) or None."""
        return self.latest_position

    def seconds_since_update(self):
        """How stale the cached frame is. Returns None if nothing has arrived yet."""
        if self.last_update is None:
            return None
        return time.monotonic() - self.last_update

    def is_live(self, max_age=1.0):
        """False if the stream has stalled — the cache would otherwise look fine forever."""
        age = self.seconds_since_update()
        return age is not None and age < max_age


# --- Yaw identification helper ---
# Run this file directly, then slowly rotate the robot about the VERTICAL axis by hand.
# Whichever of a1/a2/a3 tracks that rotation is your yaw. Set YAW_INDEX in bo_skopt.py
# to 0, 1, or 2 accordingly (a1=0, a2=1, a3=2).
async def main():
    tracker = QtmTracker("10.76.30.85")

    for _ in range(30):
        raw_data = tracker.get_current_pos()

        if raw_data is not None:
            pos_data, rot_data = raw_data
            print(
                f"X: {pos_data.x:8.2f}  Y: {pos_data.y:8.2f}  Z: {pos_data.z:8.2f}   |   "
                f"a1: {rot_data.a1:8.2f}  a2: {rot_data.a2:8.2f}  a3: {rot_data.a3:8.2f}   "
                f"(age {tracker.seconds_since_update():.2f}s)"
            )
        else:
            print("No data yet...")

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())