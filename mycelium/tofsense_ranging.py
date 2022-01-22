#!/usr/bin/env python3

import os
import time
from threading import Thread

from mycelium.components import RedisBridge, Base
from mycelium.components.arsh_xarm5_controller.ranging import TOFSenseRangingTask 

class TOFSenseRanging(Base):

    def __init__(self):
        super().__init__()
        self.logger.log_info("Initializing TOFSenseRannging")

        self.exit_threads = False

        self.rb_i = RedisBridge(db=self.rd_cfg.databases['instruments'])

        self._setup_parameters()

        self.tofsense_task = None


    def _setup_parameters(self):
        
        # TODO: add via cfg object
        # distance sensor parameters
        self.ranging_port = '/dev/ttyUSB0'
        self.ranging_baudrate = 115200
        self.sample_frequency = 10.0
        self.wakeup_frequency = 20.0 
        self.expiry = 1


    def start(self):
        self.logger.log_info("Starting TOFSenseRannging")
        self.tofsense_task = TOFSenseRangingTask( self.rb_i, "sensor0", self.ranging_port, self.ranging_baudrate, self.sample_frequency, self.wakeup_frequency, self.expiry)

        # Set state to Active to trigger sensor data capture
        self.tofsense_task.update_active(True)

        while not self.exit_threads:
            # print (self.sm.get_active_states())
            time.sleep(0.5)


    def stop(self):
        self.logger.log_info("Stopping TOFSenseRannging")
        self.exit_threads = True
        self.tofsense_task.stop()

    def __exit__(self):
        self.stop()
