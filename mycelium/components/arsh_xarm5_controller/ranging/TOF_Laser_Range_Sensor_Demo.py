#coding: UTF-8
import serial 
import time
import chardet
import sys

TOF_length = 16
TOF_header=(87,0,255)
TOF_system_time = 0
TOF_distance = 0
TOF_status = 0
TOF_signal = 0
TOF_check = 0

TOF_request=b'\x57\x10\xff\xff\x00\xff\xff\x63'

ser = serial.Serial('/dev/ttyUSB0',115200)
ser.flushInput()

def verifyCheckSum(data, len):
    print(data)
    TOF_check = 0
    for  k in range(0,len-1):
        TOF_check += data[k]
    TOF_check=TOF_check%256
    
    if(TOF_check == data[len-1]):
        print("TOF data is ok!")
        return 1    
    else:
        print("TOF data is error!")
        return 0  
  

while True:
    try:
        TOF_data=[]
        time.sleep(0.1)
        ser.write(TOF_request)

        if ser.inWaiting() ==16:
            for i in range(0,16):
                # TOF_data=TOF_data+(ord(ser.read(1)),ord(ser.read(1)))
                TOF_data.append(ord(ser.read(1)))
            print(TOF_data)
            if(len(TOF_data) != 16):
                print("Data not right length!")
                raise ValueError('NLink_TOF_Sense_Read_Frame0 frame length error')
            if(TOF_data[0]==TOF_header[0] and TOF_data[1]==TOF_header[1] and TOF_data[2]==TOF_header[2] and verifyCheckSum(TOF_data, TOF_length)):
                    if(((TOF_data[12]) | (TOF_data[13]<<8) )==0):
                        print("Out of range!")
                    else :
                        print("TOF id is: "+ str(TOF_data[3]))
                    

                        TOF_system_time = TOF_data[4] | TOF_data[5]<<8 | TOF_data[6]<<16 | TOF_data[7]<<24;
                        print("TOF system time is: "+str(TOF_system_time)+'ms')

                        TOF_distance = (TOF_data[8]) | (TOF_data[9]<<8) | (TOF_data[10]<<16);
                        print("TOF distance is: "+str(TOF_distance)+'mm')

                        TOF_status = TOF_data[11];
                        print("TOF status is: "+str(TOF_status))
                        TOF_signal = TOF_data[12] | TOF_data[13]<<8;
                        print("TOF signal is: "+str(TOF_signal))
    except Exception as e:
        print("Exception: %s" % e)
        continue



# while True:
#     TOF_data=()
#     time.sleep(0.5)
#     if ser.inWaiting() >=32:
#         for i in range(0,16):
#             TOF_data=TOF_data+(ord(ser.read(1)),ord(ser.read(1)))
#         print(TOF_data)
#         for j in range(0,16):
#             if( (TOF_data[j]==TOF_header[0] and TOF_data[j+1]==TOF_header[1] and TOF_data[j+2]==TOF_header[2]) and (verifyCheckSum(TOF_data[j:TOF_length],TOF_length))):
#                 if(((TOF_data[j+12]) | (TOF_data[j+13]<<8) )==0):
#                     print("Out of range!")
#                 else :
#                     print("TOF id is: "+ str(TOF_data[j+3]))
                

#                     TOF_system_time = TOF_data[j+4] | TOF_data[j+5]<<8 | TOF_data[j+6]<<16 | TOF_data[j+7]<<24;
#                     print("TOF system time is: "+str(TOF_system_time)+'ms')

#                     TOF_distance = (TOF_data[j+8]) | (TOF_data[j+9]<<8) | (TOF_data[j+10]<<16);
#                     print("TOF distance is: "+str(TOF_distance)+'mm')

#                     TOF_status = TOF_data[j+11];
#                     print("TOF status is: "+str(TOF_status))
#                     TOF_signal = TOF_data[j+12] | TOF_data[j+13]<<8;
#                     print("TOF signal is: "+str(TOF_signal))
             
            
#                 break
          
         
    
        
    





