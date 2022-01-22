#!/usr/bin/env python3

import smach
import time

class StowedState(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['exit', 'deploy'])

    def execute(self, userdata):
        print("Executing \"STOWED\" state")
        time.sleep(1)
        return 'deploy'

    def request_preempt(self):
        print("Preempt requested")

class HomeState(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['stow', 'start_sample_acq'])
        self.counter = 0

    def execute(self, userdata):
        print("Executing \"HOME\" state")
        time.sleep(1)
        self.counter = self.counter + 1
        if self.counter < 15:
            return 'stow'
        else:
            return 'start_sample_acq'

    def request_preempt(self):
        print("Preempt requested")


class DeployProbeState(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['deploy_fail', 'deploy_success'])

    def execute(self, userdata):
        print("Executing \"DEPLOY_PROBE\" state")
        return 'deploy_success'


class SampleSoilState(smach.State):
    def __init__(self):
        smach.State.__init__(self,outcomes=['sample_acq_finished'])

    def execute(self, userdata):
        print("Executing \"STOWED\" state")
        return 'sample_acq_finished'
