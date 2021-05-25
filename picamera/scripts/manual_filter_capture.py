#!/usr/bin/env python3

import time
import sys
import signal
import argparse

from picam_lib import FilterCapture
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()
        pin = args.pin
        connection = args.connection
        connect_robot = args.connect_robot

        if pin is None:
            pin = 24

        if connection is None:
            conn_str = self.n_cfg.udp_ext['picam_1_to_robot']
        else:
            conn_str = connection

        if connect_robot is None:
            connect_robot = True
        else:
            try:
                connect_robot = bool(connect_robot)
            except:
                connect_robot = True

        self.fc = FilterCapture(filter_servo_pin=pin, connection_string=conn_str, connect_robot=True)
        self.logger.log_info("Running filter capture")
        if connect_robot:
            self.fc.run_once_gps_long()
        else:
            self.fc.run_once()
        self.logger.log_info("Finished filter capture")

    def close_script(self):
        try:
            self.fc.stop()
        except:
            pass


scripter = ScripterExt(log_source="picamera/manual_filter_capture")
args = {
    '--pin': 'Servo pin',
    '--connection': 'Dronekit connection string',
    '--connect_robot': 'Connect to robot'
}
scripter.init_arg_parser('Capture data with picamera and filter, manually triggered', args)
scripter.run()

