#!/usr/bin/env python3

import os
import time
from threading import Thread
import transformations as tf
import numpy as np
import math as m
import traceback
import smach
# import rospy
# import smach_ros

from mycelium.components import RedisBridge, Base
from mycelium.components.arsh_xarm5_controller import *

class ARSHXarm5Controller(Base):

    def __init__(self):
        super().__init__()
        self.logger.log_info("Initializing ARSHXarm5Controller")

        self.exit_threads = False

        self.rb_a = RedisBridge(db=self.rd_cfg.databases['arsh_arm'])

        self._setup_parameters()
        self._setup_sm()

    def _setup_parameters(self):
        
        # distance sensor parameters
        self.sample_period = 1.0 

    def _setup_sm(self):

        # rospy.init_node('smach_example_state_machine')

        self.sm = smach.StateMachine(outcomes=['exit'])
        self.sm.userdata.sm_terminate = False
        self.sm.userdata.deploy_trigger = True
        self.sm.userdata.sample_trigger = False

        with self.sm:

            smach.StateMachine.add("GO_STOW", GoStowState(self.rb_a, "GO_STOW"),    transitions={'at_stow':'IDLE'},
                                                                                    remapping={'go_stow_state_terminate':'sm_terminate'})

            smach.StateMachine.add("IDLE", IdleState(self.rb_a, "IDLE"),    transitions={   'goto_home':'GO_HOME',
                                                                                            'idle_hold':'IDLE',
                                                                                            'exit': 'exit'},
                                                                            remapping={ 'idle_state_terminate':'sm_terminate',
                                                                                        'deploy_trigger':'deploy_trigger'})

            smach.StateMachine.add("GO_HOME", GoHomeState(self.rb_a, "GO_HOME"),    transitions={'at_home':'HOME'},
                                                                                    remapping={'go_home_state_terminate':'sm_terminate'})

            smach.StateMachine.add("HOME", HomeState(self.rb_a, "HOME"),    transitions={   'goto_stow':'GO_STOW',
                                                                                            'begin_sample_acq':'DEPLOY_PROBE',
                                                                                            'home_hold':'HOME',
                                                                                            'exit':'exit'},
                                                                            remapping={ 'home_state_terminate':'sm_terminate',
                                                                                        'sample_trigger':'sample_trigger'})
            
            smach.StateMachine.add("DEPLOY_PROBE", DeployProbeState(self.rb_a, "DEPLOY_PROBE"), transitions={   'deploy_success':'SAMPLE_SOIL',
                                                                                                                'deploy_abort':'GO_HOME'},
                                                                                                remapping={'deploy_probe_state_terminate':'sm_terminate'})

            smach.StateMachine.add("SAMPLE_SOIL", SampleSoilState(self.rb_a, "SAMPLE_SOIL"),    transitions={'sample_acq_end':'GO_HOME'},
                                                                                                remapping={'sample_soil_state_terminate':'sm_terminate'})

        # Attach SMACH tree in thread so that we can kill (ctrl-c) the controller
        self.sm_thread = Thread(target=self.sm.execute)


    # def _setup_ranging(self):
    #     # TODO: add ranging sensor


    def start(self):
        self.logger.log_info("Starting ARSHXarm5Controller")
        self.sm_thread.start()

        # TODO: try to get viewer working to get screenshot
        # sis = smach_ros.IntrospectionServer('server_name', self.sm, '/SM_ROOT')
        # sis.start()
        # rospy.spin()
        # sis.stop()

        while not self.exit_threads:
            # print (self.sm.get_active_states())
            time.sleep(0.5)


    def stop(self):
        self.logger.log_info("Stopping ARSHXarm5Controller")
        self.exit_threads = True
        self.sm.userdata.sm_terminate = True
        
        try:
            self.sm.request_preempt()
            self.sm_thread.join()

        except:
            self.logger.log_warn("Thread failed to join")


    def __exit__(self):
        self.stop()
