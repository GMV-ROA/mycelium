#!/usr/bin/env python3
"""Deivce Driver for interfacing with the WaveShare/NoopLoop TOFSense Laser Range Finder sensor.

This Device Driver implements a simple UART interface to communicate with the TOFSense sensor 
using the "inquire output" method, with the sensor in "inquire mode", as a request-response pattern.

The example given at https://www.waveshare.com/wiki/TOF_Laser_Range_Sensor, was used as the basis for this code.

"""

import serial 
import time

# __author__ = “Steven Kay”
# __copyright__ = “Copyright 2022, GMV NSL Limited”
# __credits__ = [“Steven Kay”]
# __license__ = “TBC”
# __version__ = “0.1.0”
# __maintainer__ = “Steven Kay”
# __email__ = “skay@gmvnsl.com”
# __status__ = “development”


class TOFSenseLaserRangeFinder:

    TOF_LENGTH=16
    TOF_HEADER=(87,0,255)
    TOF_REQUEST=b'\x57\x10\xff\xff\x00\xff\xff\x63'


    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)
        self.ser.flushInput()

        self.TOF_data=[]

        # Dictionary structure to store TOFSense response
        self._tof_return={  'id': -1, 
                            'sys_time': -1, 
                            'distance': -1, 
                            'status': -1, 
                            'signal': -1}


    def get_distance_data(self):
        try:
            self.TOF_data.clear()

            # Send request frame to TOFSense to trigger getting new sensor reading
            self.ser.write(self.TOF_REQUEST)

            # Read and parse received NLink_TOF_Sense_Read_Frame0 frame
            if self.ser.inWaiting() ==16:
                for i in range(0,16):
                    self.TOF_data.append(ord(self.ser.read(1)))

                # If frame length if not correct, return empty tof_return
                if(len(self.TOF_data) != 16):
                    print('NLink_TOF_Sense_Read_Frame0 frame length error')
                    return self._getNewToFReturn()

                # Check validity of frame  - header and CheckSum
                if(self.TOF_data[0]==self.TOF_HEADER[0] and self.TOF_data[1]==self.TOF_HEADER[1] and self.TOF_data[2]==self.TOF_HEADER[2] and self._verifyCheckSum(self.TOF_data, self.TOF_LENGTH)):
                        if(((self.TOF_data[12]) | (self.TOF_data[13]<<8) )==0):
                            print("Signal out of range!")
                            return self._getNewToFReturn()
                        else :
                            tof_return = self._getNewToFReturn()
                            TOF_id = self.TOF_data[3]                        
                            TOF_system_time = (self.TOF_data[4] | (self.TOF_data[5]<<8 )| (self.TOF_data[6]<<16) | (self.TOF_data[7]<<24))
                            TOF_distance = (self.TOF_data[8]) | (self.TOF_data[9]<<8) | (self.TOF_data[10]<<16)
                            TOF_status = self.TOF_data[11]
                            TOF_signal = self.TOF_data[12] | self.TOF_data[13]<<8

                            tof_return['id'] = TOF_id
                            tof_return['sys_time'] = TOF_system_time
                            tof_return['distance'] = TOF_distance
                            tof_return['status'] = TOF_status
                            tof_return['signal'] = TOF_signal

                            return tof_return

        except Exception as e:
            print("Exception: %s" % e)
            return self._getNewToFReturn()


    def _verifyCheckSum(self, data, len):
        TOF_check = 0
        for  k in range(0,len-1):
            TOF_check += data[k]
        TOF_check=TOF_check%256
        
        if(TOF_check == data[len-1]):
            return 1    
        else:
            return 0  


    def _getNewToFReturn(self):
        return dict(self._tof_return)


if __name__ == "__main__":
    sensor = TOFSenseLaserRangeFinder('/dev/ttyUSB0', 115200)
    while True:
        result = sensor.get_distance_data()
        print(result)
        time.sleep(0.1)
