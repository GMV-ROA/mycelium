#!/usr/bin/env python3

from re import S
import sys

from torch import set_num_threads
sys.path.append("/usr/local/lib/")

import os
import time
from threading import Thread
import transformations as tf
import numpy as np
import math as m
import traceback
import smach


from mycelium.components import RedisBridge, Base
from mycelium.components.arsh_xarm5_controller import StowedState, HomeState, DeployProbeState, SampleSoilState

class ARSHXarm5Controller(Base):

    def __init__(self):
        super().__init__()
        self.logger.log_info("Initializing ARSHXarm5Controller")

        self.exit_threads = False

        self._setup_parameters()
        self._setup_sm()

    def _setup_parameters(self):
        
        # distance sensor parameters
        self.sample_period = 1.0 

    def _setup_sm(self):
        self.sm = smach.StateMachine(outcomes=['exit'])

        with self.sm:
            smach.StateMachine.add("STOWED", StowedState(), transitions={   'deploy':'HOME', 
                                                                            'exit': 'exit'})
            smach.StateMachine.add("HOME", HomeState(), transitions={   'stow':'STOWED',
                                                                        'start_sample_acq':'exit'})

        # Attach SMACH tree in thread so that we can kill (ctrl-c) the controller
        self.sm_thread = Thread(target=self.sm.execute)


    def start(self):
        self.logger.log_info("Starting ARSHXarm5Controller")
        self.sm_thread.start()

        while not self.exit_threads:
            time.sleep(0.5)
            self.logger.log_debug("Still running...")

        self.logger.log_error("TIME TO EXIT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def stop(self):
        self.logger.log_info("Stopping ARSHXarm5Controller")
        self.exit_threads = True
        
        try:
            self.sm.request_preempt()
            self.sm_thread.join()

        except:
            self.logger.log_warn("Thread failed to join")


    def __exit__(self):
        self.stop()
