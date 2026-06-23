import asyncio
import copy
from Strut_Class import Strut
import csv
from datetime import datetime
import os

class SPVVVECTR():
    '''
    Class representing a single SPVVVECTR Tensegrity Robot.
    Including three ESP32 Strut PCBs, with overall robot control.
    '''

    MAX_SPEED = 1000  #Change this if needed

    BOARDS_CONFIG = {
        "SPVVVECTR1": {"address": "8C:94:DF:2B:28:E6", 
                           "service": "afcdeba4-f8a9-4ca1-baa5-021afe634998", 
                           "char": "83147421-2684-43ec-af39-58533d866c8e"},
        "SPVVVECTR2": {"address": "8C:94:DF:2B:29:22", "service": 
                           "8aaba9c2-7f68-49d6-97cb-b9783ea29fd6", 
                           "char": "2a612f78-13b2-4b3a-bab8-50b00d2f003f"},
        "SPVVVECTR3": {"address": "8C:94:DF:2B:28:F2", 
                           "service": "e132a2ee-a68a-4b4b-98fa-29ef8bbc0be2", 
                           "char": "ccba8d13-8743-45f7-9fd9-69a20a9acddc"}
    }
    '''
    Configuration of the microcontrollers used on active struts,\n
    including its name, MAC address, service and characteristic
    UUIDs.
    '''

    struts_data = {}
    '''Used to store the data from each strut'''
    
    '========================================================================='
    '=========================Initialization==========================='
    def __init__(self):
        '''
        Initializes the SPVVVECTR class by creating Strut instances for each\n 
        configured board and setting up a data structure to store their data.
        '''
        self.config = self.BOARDS_CONFIG
        self.struts = {name: Strut(name, cfg) for name, cfg in self.config.items()}
        self.struts_data = {name: None for name in self.config}
        self.struts_status = {name: "OFFLINE" for name in self.config}
        self.is_recording = False
        self.record_task = None
    
    '========================================================================='
    '===============================BLE Connection============================'
    async def connect_strut(self, name: str):
        '''
        Connect to a specific strut by name
        and update its data upon successful connection.\n
        @param: name: The name of the strut to connect to (e.g., "SPVVVECTR1").
        '''
        if name in self.struts:
            await self.struts[name].connect()
        if self.struts[name].status == "ONLINE":
            self.struts_data[name] = self.struts[name].get_ordered_data()
            self.struts_status[name] = "ONLINE"
        else:
            self.struts_status[name] = "OFFLINE"
            print(f"Failed to connect to {name}.")

    async def connect_all(self):
        '''
        Connect to all struts in BOARD_CONFIG.
        '''
        tasks = [self.connect_strut(name) for name in self.struts]
        await asyncio.gather(*tasks)
    
    async def disconnect_strut(self, name: str):
        '''
        Disconnect from a specific strut by name.\n
        @param: name: The name of the strut to disconnect from.
        '''
        if name in self.struts:
            await self.struts[name].disconnect()
            self.struts_status[name] = "OFFLINE"
            print(f"Disconnected from {name}.")

    async def disconnect_all(self):
        '''
        Disconnect from all struts in BOARD_CONFIG.
        '''
        tasks = [self.disconnect_strut(name) for name in self.struts]
        await asyncio.gather(*tasks)

    '========================================================================='
    '===============================Motor Control============================='
    async def set_speed(self, name: str, value: int):
        '''
        Set the speed to a specific strut by name and value.\n
        @param:
        - name: The name of the strut to set the speed for.
        - value: An int with the absolute value less than MAX_SPEED.
        '''
        for strut_name, strut in self.struts.items():
            if strut_name == name and strut.status == "ONLINE":
                try:
                    await strut.set_target_rpm(value)
                    self.struts_data[name] = strut.get_ordered_data()
                except Exception as e:
                    print(f"Error setting speed for {name}: {e}")
                break

    async def stop(self, name: str):
        '''
        Stop a specific strut by name.\n
        @param: name: The name of the strut to stop.
        '''
        await self.set_speed(name, 0)

    async def set_speed_all(self, value: int):
        '''
        Set all struts to the same speed by value.\n
        @param: value: An int with the absolute value less than MAX_SPEED.
        '''
        tasks = []
        for strut in self.struts.values():
            tasks.append(self.set_speed(strut.name, value))
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        '''
        Stop all struts.
        '''
        await self.set_speed_all(0)
    
    async def calibrate(self, name: str):
        '''
        Calibrate the MPU6050 IMU of a specific strut by name.\n
        @param: name: The name of the strut to calibrate.
        '''
        if name in self.struts and self.struts[name].status == "ONLINE":
            await self.struts[name].mpu_calibrate()

    '========================================================================='
    '=======================Receiving data and Parsing========================'
    async def get_status(self, name: str) -> str:
        '''
        Get the current status of a specific strut by name.\n
        @param: name: The name of the strut to get the status for.\n
        @return: "ONLINE" if connected, "OFFLINE" otherwise.
        '''
        if name in self.struts:
            return self.struts_status[name]
        else:
            return None
    
    async def get_all_status(self):
        '''
        Get the current status of all struts.\n
        @return: A copy of the dictionary containing the status of all struts.
        '''
        return copy.copy(self.struts_status)


    async def update_strut_data(self, name: str):
        '''
        Update data of a specific strut by name.\n
        @param: name: The name of the strut to update data for.
        '''
        if name in self.struts:
            try:
                self.struts_data[name] = self.struts[name].get_ordered_data()
            except Exception as e:
                print(f"Error updating data for {name}: {e}")
        else:
            print(f"Strut {name} not found.")

    async def update_all_strut_data(self):
        '''
        Update data for all struts.
        '''
        tasks = [self.update_strut_data(name) for name in self.struts]
        await asyncio.gather(*tasks)
    
    async def get_strut_data(self, name: str):
        '''
        Get data of a specific strut by name.\n
        @param: name: The name of the strut to get data for.\n
        @return: An ordered list of the strut's data, or None if not found.\n
        [Target_RPM, Actual_RPM, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z]
        '''
        await self.update_strut_data(name)
        if name in self.struts_data:
            try:
                return self.struts_data[name]
            except Exception as e:
                print(f"Error retrieving data for {name}: {e}")
                return None
        else:
            print(f"Strut {name} not found.")
            return None
    
    async def get_all_strut_data(self):
        '''
        Get data for all struts.\n
        @return: A copy of the dictionary containing all strut data.
        '''
        await asyncio.sleep(0.2)
        await self.update_all_strut_data()
        return copy.copy(self.struts_data)
    

    '========================================================================='
    '=======================Recording data to CSV File========================'

    async def choose_working_directory(self, directory: str):
        '''
        Set the working directory for saving CSV files.\n
        @param: directory: The path to the desired working directory.
        '''
        if os.path.isdir(directory):
            os.chdir(directory)
            print(f"Working directory set to: {directory}")
        else:
            print(f"Invalid directory: {directory}")

    async def start_record(self):
        if not self.is_recording and self.record_task is None:
            self.is_recording = True
            self.record_task = asyncio.create_task(self.record())
    
    async def stop_record(self):
        self.is_recording = False
        self.record_task = None
    
    async def record(self):
        csv_file = f"SPVVVECTR_data_{datetime.now().strftime('%m%d%Y_%H%M%S')}.csv"
        headers = []
        for name in self.struts:
            headers.extend([f"{name}_timestamp",
                            "Target_RPM",
                            "Actual_RPM", 
                            "Accel_X", 
                            "Accel_Y", 
                            "Accel_Z", 
                            "Gyro_X", 
                            "Gyro_Y", 
                            "Gyro_Z",
                            " " ]) #Blank column for separation
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

        while self.is_recording:
            if any(status == "ONLINE" for status in self.struts_status.values()):
                await self.update_all_strut_data()
                row = []
                for name in self.struts:
                    if self.struts_status[name] == "ONLINE":
                        data = self.struts_data[name]
                        timestamp = f'="{datetime.now().strftime("%H:%M:%S.%f")[:-3]}"'
                        row.extend([timestamp] + data + [" "])  
                    else:
                        row.extend(["OFFLINE"] + ["N/A"] * 8 + [" "])
                with open(csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(row)
            if not self.is_recording:
                break
            await asyncio.sleep(0.1)


'========================================================================='
'=================================Testing================================='
if __name__ == "__main__":
    async def test_1():
        '''Unit testing of the SPVVVECTR class - only SPVVVECTR1 for now.'''
        robot = SPVVVECTR()
        print (await robot.get_all_strut_data())

        init = input("Press Enter to connect to SPVVVECTR1...")
        #Connect to SPVVVECTR1 for now.
        await robot.connect_strut("SPVVVECTR1")
        print (await robot.get_status("SPVVVECTR1"))

        while True:
            speed = input("Target RPM: ")
            try:
                await robot.set_speed("SPVVVECTR1", int(speed))
            except ValueError:
                print ("Set Speed Error.")
            print (await robot.get_all_strut_data())

            stop_trig = input("Stop? (y/n): ")
            if stop_trig.lower() == 'y':
                await robot.stop("SPVVVECTR1")
                print (await robot.get_all_strut_data())
                break
            await asyncio.sleep(1) 
        await robot.disconnect_strut("SPVVVECTR1")
        print (await robot.get_status("SPVVVECTR1"))

    async def test_2():
        '''Unit testing of the SPVVVECTR class - connecting to all struts.'''

        robot = SPVVVECTR()
        print ("Robot initialized.")

        work_dir = input("Enter working directory for CSV files: ")
        await robot.choose_working_directory(work_dir)

        while True:
            user_input = input("Choose a number:\n"
                               "1. Connect All\n2. Disconnect All\n" 
                               "3. Set Speed All\n4. Stop All\n" 
                               "5. Calibrate All\n6. Get Data All\n"
                               "7. Start Recording\n8. Stop Recording\n"
                               "9. Exit\n")
            match user_input:
                case "1":
                    await robot.connect_all()
                    print (await robot.get_all_status())
                case "2":
                    await robot.disconnect_all()
                    print (await robot.get_all_status())
                case "3":
                    speed = input("Target RPM: ")
                    try:
                        await robot.set_speed_all(int(speed))
                    except ValueError:
                        print ("Set Speed Error.")
                case "4":
                    await robot.stop_all()
                case "5":
                    for name in robot.struts:
                        await robot.calibrate(name)
                case "6":
                    print (await robot.get_all_strut_data())
                case "7":
                    await robot.start_record()
                case "8":
                    await robot.stop_record()
                case "9":
                    break
                case _:
                    print ("Invalid input. Please try again.")
            await asyncio.sleep(0.5)
        
        await robot.disconnect_all()
        print("Test completed.")

    asyncio.run(test_2())