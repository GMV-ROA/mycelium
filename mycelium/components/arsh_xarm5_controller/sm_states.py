#!/usr/bin/env python3

import sys
import time

import smach
 
from mycelium.components import RedisBridge

class BaseState(smach.State):
    def __init__(self, outcomes=[], input_keys=[], output_keys=[], rb_if=RedisBridge(), state_name=""):
        super().__init__(outcomes, input_keys, output_keys)
        self.rb_if = rb_if  
        self.name = state_name    

    def execute(self, userdata):
        print("Executing \"%s\" state" % self.name)
        self.rb_if.add_key(self.name, 'sm', 'state', expiry=5)

        # Call sub-class state execute logic
        return self.state_execute(userdata)


    def state_execute(self, userdata):
        raise NotImplementedError


    # def _set_state(self):


class GoStowState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['at_stow'], 
                            input_keys=['go_stow_state_terminate'], 
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        time.sleep(1)

        # TODO: move xarm5 from current pose --> stow pose

        # Wait until in stow pose before returning, exit via IDLE state
        if userdata.go_stow_state_terminate:
            print("Ignoring go_stow state Terminate!")
        
        return 'at_stow'


class IdleState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['goto_home', 'idle_hold', 'exit'], 
                            input_keys=['idle_state_terminate', 'deploy_trigger'],
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        time.sleep(1)

        if userdata.idle_state_terminate:
            print("IDLE Terminate!")
            return 'exit'
        elif userdata.deploy_trigger:
            return 'goto_home'
        else:
            return 'idle_hold'


class GoHomeState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['at_home'], 
                            input_keys=['go_home_state_terminate'], 
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        time.sleep(1)

        # TODO: move xarm5 from current pose --> home pose

        # Wait until in home pose before returning, exit via HOME state
        if userdata.go_home_state_terminate:
            print("Ignoring go_home state Terminate!")
        
        return 'at_home'



class HomeState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['goto_stow', 'begin_sample_acq', 'home_hold', 'exit'], 
                            input_keys=['home_state_terminate', 'sample_trigger'],
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        time.sleep(1)

        if userdata.home_state_terminate:
            print("HOME Terminate!")
            return 'exit'
        elif userdata.sample_trigger:
            return 'begin_sample_acq'
        else:
            return 'home_hold'


class DeployProbeState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['deploy_success', 'deploy_abort'],
                            input_keys=['deploy_probe_state_terminate'], 
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        # TODO: move xarm5 from current pose --> deploy pose

        deploy_fail = False

        # If terminated or deployment fails, return to HOME state, via GOTO_HOME state
        if userdata.deploy_probe_state_terminate or deploy_fail:
            return 'deploy_abort'
        else:
            return 'deploy_success'


class SampleSoilState(BaseState):
    def __init__(self, rb_if, state_name):
        super().__init__(   outcomes=['sample_acq_end'],
                            input_keys=['sample_soil_state_terminate'], 
                            rb_if=rb_if,
                            state_name=state_name)

    def state_execute(self, userdata):
        time.sleep(1)

        # TODO: perform sampling

        # Wait until in home pose before returning, exit via HOME state
        if userdata.deploy_probe_state_terminate:
            print("Ignoring sample_soil state Terminate!")
        
        return 'sample_acq_end'
