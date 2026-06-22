import asyncio
import copy
from PCB_Strut import Strut

class SPVVVECTR():
    '''
    Class representing a single SPVVVECTR Tensegrity Robot.
    Including three ESP32 Strut PCBs, with overall robot control.
    '''

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
        - value: An int between -700 and 700.
        '''
        for strut_name, strut in self.struts.items():
            if name in strut_name and strut.status == "ONLINE":
                await strut.set_target_rpm(value)

    async def stop(self, name: str):
        '''
        Stop a specific strut by name.\n
        @param: name: The name of the strut to stop.
        '''
        await self.set_speed(name, 0)

    async def set_speed_all(self, value: int):
        '''
        Set all struts to the same speed by value.\n
        @param: value: An int between -700 and 700.
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
        print (await robot.get_all_strut_data())

        init = input("Press Enter to connect to all struts...")
        await robot.connect_all()
        print (await robot.get_all_strut_data())

        while True:
            speed = input("Target RPM for all struts: ")
            try:
                await robot.set_speed_all(int(speed))
            except ValueError:
                print ("Set Speed Error.")
            print (await robot.get_all_strut_data())

            stop_trig = input("Stop all struts? (y/n): ")
            if stop_trig.lower() == 'y':
                await robot.stop_all()
                print (await robot.get_all_strut_data())
                break

            await asyncio.sleep(1) 
        await robot.disconnect_all()
        print (await robot.get_all_strut_data())

    asyncio.run(test_1())