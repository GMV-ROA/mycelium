#!/usr/bin/env python3

import time
import sys
import signal
import argparse

from picam_lib import FilterMissionExec
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()
        connection = args.connection

        if connection is None:
            conn_str = 'udp:192.168.2.155:14577'
        else:
            conn_str = connection            
            
        self.mexec = FilterMissionExec(24, 12, conn_str)
        self.mexec.start()

        while not self.exit_all_loops:
            time.sleep(1)
            if self.mexec.filter_capture:
                self.logger.log_info("Stopping at waypoint, processing filter capture: %d" % self.mexec.filter.filter_id)
            else:
                self.logger.log_info("Single capture")
            
            if self.mexec.is_mission_complete():
                self.logger.log_info("Mission complete")
                break

    def close_script(self):
        try:
            self.mexec.stop()
        except:
            pass


scripter = ScripterExt(log_source="picamera/filter_capture")
scripter.init_arg_parser('Capture filter data with picamera during mission',
    {'--connection': 'Dronekit connection string'})
scripter.run()




#### Setup

# parser = argparse.ArgumentParser(description='Capture data with picamera during mission')
# parser.add_argument('--connection',
#                     help="Dronekit connection string")                

# args = parser.parse_args()
# connection = args.connection

# mexec = MissionExec(24, 12, connection)


# #### Functions

# exit_all_loops = False
# exit_code = 1

# def _sigint_handler(sig, frame):
#     global exit_all_loops
#     exit_all_loops = True

# def _sigterm_handler(sig, frame):
#     global exit_all_loops, exit_code
#     exit_all_loops = True
#     exit_code = 0

# signal.signal(signal.SIGINT, _sigint_handler)
# signal.signal(signal.SIGTERM, _sigterm_handler)


# #### Start capture

# print("Start mission capture")
# try:
#     mexec.start()
#     while not exit_all_loops:
#         time.sleep(1)
#         if mexec.filter_capture:
#             print("Stopping at waypoint, processing filter capture: %d"%mexec.filter.filter_id)
#         else:
#             print("Single capture")
        
#         if mexec.is_mission_complete():
#             print("Mission complete")
#             break

                
# except Exception as e:
#     print(e)

# finally:
#     print("Closing script...")
#     try:
#         mexec.stop()
#     except:
#         pass
    
#     signal.setitimer(signal.ITIMER_REAL, 5)
#     sys.exit(exit_code)
