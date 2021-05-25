#!/usr/bin/env python3

import time
import sys
import signal
import argparse
import os
import threading

from picam_lib import PicamImpl
from mycelium_utils import DronekitConnector, Scripter
from mycelium_utils.utils import generate_dirname

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()
        connection = args.connection
        if connection is None:
            conn_str = self.n_cfg.udp_ext['picam_1_to_robot']
        else:
            conn_str = connection


        self.logger.log_info("Starting camera, connecting robot")
        self.camera = PicamImpl(PicamImpl.RAW_BAYER)
        self.dconn = DronekitConnector(conn_str)
        self.logger.log_info("Startup complete")

        dirname = 'sc_%d' % int(time.time())
        self.camera.set_save_directory(dirname)
        started = False

        self.logger.log_info("Start mission capture")
        while not self.exit_all_loops:
            if self.dconn.get_mode() == 'AUTO':
                started = True
                try:
                    self.camera.capture_single()
                except Exception as e:
                    self.logger.log_error("Could not capture frame: %s" % e)

            if started and self.dconn.get_mode() != 'AUTO':
                break

    def close_script(self):
        try:
            self.dconn.disconnect()
        except:
            pass


scripter = ScripterExt(log_source="picamera/mission_capture")
scripter.init_arg_parser('Capture data with picamera during mission',
    {'--connection': 'Dronekit connection string'})
scripter.run()




#### Setup

# parser = argparse.ArgumentParser(description='Capture data with picamera during mission')
# parser.add_argument('--connection',
#                     help="Dronekit connection string")                

# args = parser.parse_args()
# connection = args.connection

# if connection is None:
#     conn_str = 'udp:192.168.2.155:14577'
# else:
#     conn_str = connection

# print("Starting camera, connecting robot")
# camera = PicamImpl(PicamImpl.RAW_BAYER)
# dconn = DronekitConnector(conn_str)
# print("Startup complete")


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

# dirname = 'sc_%d' % int(time.time())
# camera.set_save_directory(dirname)
# started = False

# print("Start mission capture")
# try:
#     while True:
#         if dconn.get_mode() == 'AUTO':
#             started = True
#             camera.capture_single()

#         if started and dconn.get_mode() != 'AUTO' or exit_all_loops:
#             break
        
# except Exception as e:
#     print(e)

# finally:
#     print("Closing script...")
#     try:
#         dconn.disconnect()
#     except:
#         pass
    
#     signal.setitimer(signal.ITIMER_REAL, 5)
#     sys.exit(exit_code)
