#!/usr/bin/env python3

import time
import sys
import signal
import argparse

from picam_lib import WaypointMissionExec
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()
        connection = args.connection
        mode = args.mode

        if connection is None:
            conn_str = self.n_cfg.udp_ext['picam_1_to_robot']
        else:
            conn_str = connection

        if mode is not None:
            mode = int(mode)
        else:
            mode = WaypointMissionExec.NO_FILTER
            
        self.mexec = WaypointMissionExec(conn_str, 24, 12, mode=mode)
        self.mexec.start()

        while not self.exit_threads:
            time.sleep(1)
            if self.mexec.waypoint_capture and mode != WaypointMissionExec.NO_FILTER:
                self.logger.log_info("Stopping at waypoint, processing filter capture: %d" % self.mexec.filter.filter_id)
            elif self.mexec.waypoint_capture:
                self.logger.log_info("Stopping at waypoint, capturing images")
            
            if self.mexec.is_mission_complete():
                self.logger.log_info("Mission complete")
                break

        self.mexec.close_mission = True

    def close_script(self):
        try:
            self.mexec.stop()
        except:
            pass


scripter = ScripterExt(log_source="picamera/waypoint_capture")
args = {
    '--connection': 'Dronekit connection string',
    '--mode': 'Mission mode'
}
scripter.init_arg_parser('Capture data with picamera during mission', args)
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
