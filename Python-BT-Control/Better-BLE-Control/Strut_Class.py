'''
    Class for the Tensegrity Strut PCB, which handles BLE communication,
    control of the strut's motor speed, and retrieval of encoder and
    IMU data.

    Methods:
    - connect()
    - disconnect()
    - notification_handler(sender, data)
    - set_target_rpm(rpm)
    - get_status()
    - get_target_rpm()
    - get_actual_rpm()
    - get_imu_data()
    - get_ordered_data()n


    @author: Duy Hung Dang
    June 2026
    Union Evolutionary Robotics Lab

'''

import asyncio
import platform
import re
from bleak import BleakClient, BleakScanner

class Strut:
    '''
    Class representing a single Tensegrity Strut PCB.
    Including: ESP32 BLE communication, N20 Motor Control with Encoder,
    data from MPU6050 IMU.
    '''


    '=================================================================='
    '=========================Initialization==========================='
    def __init__(self, board_name: str, board_config: dict):
        '''
        Initializes the Strut object with default values 
        and sets up BLE communication parameters.\n
        @param:
        - board_name: String representation of the board name.
        - board_config: Dictionary containing BLE address, 
        service UUID, and characteristic UUID in that order.
        '''

        self.Target_RPM = 0
        self.Actual_RPM = 0
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.acc_z = 0.0
        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0
        self.name = board_name
        self.config = board_config
        self.status = "OFFLINE"
        self.client = None

    
    '========================================================================='
    '=============================BLE Communication==========================='
    @staticmethod
    def _is_mac_address(device_id: str) -> bool:
        return bool(re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", device_id))

    async def connect(self) -> bool:
        '''
        Connects to the BLE device and starts notifications.\n
        @return: True if connection is successful, False otherwise.
        '''
        try:
            device_id = self.config.get("identifier", self.config["address"])
            if platform.system() == "Darwin" and self._is_mac_address(device_id):
                # macOS does not expose BLE MAC addresses; resolve by advertised name.
                scan_timeout = float(self.config.get("scan_timeout", 8.0))
                device = await BleakScanner.find_device_by_filter(
                    lambda d, ad: d.name == self.name or ad.local_name == self.name,
                    timeout=scan_timeout
                )
                if device is None:
                    raise RuntimeError(
                        f"Device '{self.name}' not found on macOS scan. "
                        "Set config['identifier'] to the macOS BLE UUID for stable pairing."
                    )
                self.client = BleakClient(device)
            else:
                self.client = BleakClient(device_id)

            await self.client.connect()
            _ = self.client.services
            if self.client.is_connected:
                self.status = "ONLINE"
                await self.client.start_notify(self.config["char"], 
                                               self.notification_handler)
                return True
        except Exception as e:
            print(f"OFFLINE: {self.name} ({e})")
        return False

    async def disconnect(self):
        '''
        Disconnects from the BLE device and stops notifications.
        '''
        if self.client and self.client.is_connected:
            await self.client.stop_notify(self.config["char"])
            await self.client.disconnect()
            self.status = "OFFLINE"
            self.client = None

    def notification_handler(self, sender: str, data: bytes):
        '''
        Handler for incoming BLE notifications. 
        Parses the data and updates the strut's data.\n
        @param:
        - sender: The BLE characteristic that sent the notification.
        - data: The raw data received from the BLE device.
        '''
        try:
            message = data.decode('utf-8', errors='strict').strip()
        except UnicodeDecodeError:
            print("Decode error from", sender)
            return
        
        parts = [p.strip() for p in message.split(',')]

        try:
            self.Target_RPM = int(float(parts[0]))
            self.Actual_RPM = int(float(parts[1]))
            self.acc_x = float(parts[2])
            self.acc_y = float(parts[3])
            self.acc_z = float(parts[4])
            self.gyro_x = float(parts[5])
            self.gyro_y = float(parts[6])
            self.gyro_z = float(parts[7])
        except ValueError as e:
            print("Parse error:", e)


    '========================================================================='
    '============================Sending BLE CMD=============================='
    async def set_target_rpm(self, rpm: int):
        '''
        Sets the target RPM for the strut's motor and sends the command via BLE.
        @param:
        - rpm: An int, in the speed range of the motor (e.g., -700 to 700).
        '''
        self.Target_RPM = rpm
        if self.client and self.client.is_connected:
            asyncio.create_task(
                self.client.write_gatt_char(self.config["char"], 
                                            str(rpm).encode(), 
                                            response=False))
    
    async def mpu_calibrate(self):
        '''
        Sends a command to calibrate the MPU6050 IMU.
        '''
        if self.client and self.client.is_connected:
            asyncio.create_task(
                self.client.write_gatt_char(self.config["char"], 
                                            'calibrate'.encode(), 
                                            response=False))


    '========================================================================='
    '=======================Receiving data and Parsing========================'
    def get_status(self) -> str:
        '''
        Returns the current status of the strut.\n
        @return: "ONLINE" if connected, "OFFLINE" otherwise.
        '''
        return self.status

    def get_target_rpm(self) -> int:
        '''
        Returns the target RPM of the strut's motor.
        '''
        return self.Target_RPM
    
    def get_actual_rpm(self) -> int:
        '''
        Returns the actual RPM of the strut's motor.
        '''
        return self.Actual_RPM

    def get_imu_data(self) -> tuple:
        '''
        Returns the current IMU data as a tuple 
        (acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z).
        '''
        return (self.acc_x, self.acc_y, self.acc_z, 
                self.gyro_x, self.gyro_y, self.gyro_z)
    
    def get_ordered_data(self) -> list:
        '''
        Returns all strut's data in an ordered list for easier processing.\n
        [Target_RPM, Actual_RPM, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z]
        '''
        return [self.Target_RPM, self.Actual_RPM, 
                self.acc_x, self.acc_y, self.acc_z, 
                self.gyro_x, self.gyro_y, self.gyro_z]


if __name__ == "__main__":
    async def main():
        '''
        Unit testing of the Strut Class
        '''
        strut = Strut("SPVVVECTR1", 
                    {"address": "8C:94:DF:2B:28:E6", 
                    "service": "afcdeba4-f8a9-4ca1-baa5-021afe634998", 
                    "char": "83147421-2684-43ec-af39-58533d866c8e"})
        await strut.connect()
        print (f"Strut Status: {strut.get_status()}")
        while True:
            speed = input("Target RPM: ")
            try:
                await strut.set_target_rpm(int(speed))
            except ValueError:
                print("Invalid RPM value. Please enter an integer.")
            
            await asyncio.sleep(1)  # Wait a bit to receive updates
            
            user_cont = input("Continue? (y/n): ")
            if user_cont.lower() != 'y':
                print (strut.get_ordered_data())
                await strut.set_target_rpm(0)
                await asyncio.sleep(2)
                await strut.disconnect()
                break
                
            calibrate = input("Calibrate IMU? (y/n): ")
            if calibrate.lower() == 'y':
                await strut.mpu_calibrate()
                print("Calibration command sent.")
                await asyncio.sleep(1)  # Wait a bit to receive updates
            print (strut.get_ordered_data())
        try:
            await strut.set_target_rpm(0)
            await strut.disconnect()
        except Exception as e:
            pass
        print(strut.get_status())

    asyncio.run(main())