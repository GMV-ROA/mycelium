#!/usr/bin/env python3

import os
import sys
import math
import time
import numpy as np
import quaternion

from scipy.spatial.transform import Rotation as R

from torch import is_grad_enabled

from xarm.wrapper import XArmAPI


def euler_to_axis_aa(order, euler, degrees=True):
    return R.from_euler(order, euler, degrees=degrees).as_rotvec()

arm = XArmAPI('192.168.1.244', is_radian=True)
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(0)

stow_pose_in_B_euler = [134, 0, 301, -180, 0, 0]
# home_pose_in_B_euler = [0, 300, 280, -172.3, -127.3, 0] 
home_pose_in_B_euler = [0, 300, 280, -180, 0, 0]

deploy_pose_in_B_euler = [0, 300, -280, -180, 0, 0]

# Convert attitude from euler to quaternion
stow_att_in_B_q = quaternion.from_euler_angles(R.from_euler('xyz', [stow_pose_in_B_euler[3], stow_pose_in_B_euler[4], stow_pose_in_B_euler[5]], degrees=True).as_quat())
# home_att_in_B_q = np.quaternion(R.from_euler('xyz', [home_pose_in_B_euler[3], home_pose_in_B_euler[4], home_pose_in_B_euler[5]], degrees=True).as_quat())

# print(stow_att_in_B_q)

stow_att_in_B_aa = euler_to_axis_aa('xyz', [stow_pose_in_B_euler[3], stow_pose_in_B_euler[4], stow_pose_in_B_euler[5]])
home_att_in_B_aa = euler_to_axis_aa('xyz', [home_pose_in_B_euler[3], home_pose_in_B_euler[4], home_pose_in_B_euler[5]])
deploy_att_in_B_aa = euler_to_axis_aa('xyz', [deploy_pose_in_B_euler[3], deploy_pose_in_B_euler[4], deploy_pose_in_B_euler[5]])


stow_pose_in_B_aa = list(np.concatenate((stow_pose_in_B_euler[0:3], stow_att_in_B_aa)))
home_pose_in_B_aa = list(np.concatenate((home_pose_in_B_euler[0:3], home_att_in_B_aa)))
deploy_pose_in_B_aa = list(np.concatenate((deploy_pose_in_B_euler[0:3], deploy_att_in_B_aa)))

# print(stow_pose_in_B_aa)

# arm.reset(wait=True)

# speed = 50
# print(arm.get_servo_angle(), arm.get_servo_angle(is_radian=False))
# arm.set_servo_angle(servo_id=1, angle=10, speed=speed, is_radian=False, wait=True)
# print(arm.get_servo_angle(), arm.get_servo_angle(is_radian=False))

# arm.reset(wait=True)

# print(type())


print("Current Position: %s" % str(arm.get_position_aa()))
print("Setting POSE=stow")
arm.set_position_aa(stow_pose_in_B_aa, is_radian=True, wait=True)
print("Current Position: %s" % str(arm.get_position_aa()))
time.sleep(5)

print("Setting POSE=home")
arm.set_position_aa(home_pose_in_B_aa, is_radian=True, wait=True)
print("Current Position: %s" % str(arm.get_position_aa()))
time.sleep(5)

print("Setting POSE=deploy")
arm.set_position_aa(deploy_pose_in_B_aa, is_radian=True, wait=True)
print("Current Position: %s" % str(arm.get_position_aa()))
time.sleep(5)

print("Setting POSE=home")
arm.set_position_aa(home_pose_in_B_aa, is_radian=True, wait=True)
print("Current Position: %s" % str(arm.get_position_aa()))
time.sleep(5)

print("Setting POSE=stow")
arm.set_position_aa(stow_pose_in_B_aa, is_radian=True, wait=True)
print("Current Position: %s" % str(arm.get_position_aa()))


# arm.get_inverse_kinematics()
arm.motion_enable(enable=False)
arm.disconnect()