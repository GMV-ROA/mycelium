#!/usr/bin/env python3
# -*- coding: utf-8 -*-

######################################################
##  Sending control commands to AP via MAVLink      ##
##  Based on set_attitude_target.py: https://github.com/dronekit/dronekit-python/blob/master/examples/set_attitude_target/set_attitude_target.py
######################################################

from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
from pymavlink import mavutil # Needed for command message definitions
import time
import math

# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"

import sys

#######################################
# Parameters
#######################################

rc_control_channel = 6     # Channel to check value, start at 0 == chan1_raw
rc_control_thres = 2000    # Values to check

#######################################
# Global variables
#######################################

rc_channel_value = 0
vehicle = None

#######################################
# User input
#######################################

# Set up option parsing to get connection string
import argparse  
parser = argparse.ArgumentParser(description='Example showing how to set and clear vehicle channel-override information.')
parser.add_argument('--connect', 
                   help="vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

#######################################
# Functions
#######################################

connection_string = args.connect

print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True, source_system=1, source_component=0)

@vehicle.on_message('RC_CHANNELS')
def RC_CHANNEL_listener(vehicle, name, message):
    global rc_channel_value, rc_control_channel
    
    # TO-DO: find a less hard-coded solution
    curr_channels_values = [message.chan1_raw, message.chan2_raw, message.chan3_raw, message.chan4_raw, message.chan5_raw, message.chan6_raw, message.chan7_raw, message.chan8_raw]

    rc_channel_value = curr_channels_values[rc_control_channel]

    # # Print out the values to debug
    # print('%s attribute is: %s' % (name, message)) # Print all info from the messages
    # os.system('clear') # This helps in displaying the messages to be more readable
    # for channel in range(8):
    #     print("Number of RC channels: ", message.chancount, ". Individual RC channel value:")
    #     print(" CH", channel, curr_channels_values[channel])


def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    """
    Move vehicle in direction based on specified velocity vectors.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111000111, # type_mask (only speeds enabled)
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # x, y, z velocity in m/s
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)


    # send command to vehicle on 1 Hz cycle
    for x in range(0,duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)


def goto_position_target_local_ned(north, east, down):
    """
    Send SET_POSITION_TARGET_LOCAL_NED command to request the vehicle fly to a specified
    location in the North, East, Down frame.
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, # frame
        0b0000111111111000, # type_mask (only positions enabled)
        north, east, down,
        0, 0, 0, # x, y, z velocity in m/s  (not used)
        0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
    # send command to vehicle
    vehicle.send_mavlink(msg)


"""
Convenience functions for sending immediate/guided mode commands to control the Copter.
The set of commands demonstrated here include:
* MAV_CMD_CONDITION_YAW - set direction of the front of the Copter (latitude, longitude)
* MAV_CMD_DO_SET_ROI - set direction where the camera gimbal is aimed (latitude, longitude, altitude)
* MAV_CMD_DO_CHANGE_SPEED - set target speed in metres/second.
The full set of available commands are listed here:
http://dev.ardupilot.com/wiki/copter-commands-in-guided-mode/
"""

def condition_yaw(heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).
    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.
    By default the yaw of the vehicle will follow the direction of travel. After setting 
    the yaw using this function there is no way to return to the default yaw "follow direction 
    of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)
    For more information see: 
    http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
    """
    if relative:
        is_relative = 1 #yaw relative to direction of travel
    else:
        is_relative = 0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)


def pos_control_align_north_and_move_square():

    print("SQUARE path using SET_POSITION_TARGET_LOCAL_NED and position parameters")
    DURATION_SEC = 2 #Set duration for each segment.
    HEIGHT_M = 2
    SIZE_M  = 2

    """
    Fly the vehicle in a SIZE_M meter square path, using the SET_POSITION_TARGET_LOCAL_NED command 
    and specifying a target position (rather than controlling movement using velocity vectors). 
    The command is called from goto_position_target_local_ned() (via `goto`).
    The position is specified in terms of the NED (North East Down) relative to the Home location.
    WARNING: The "D" in NED means "Down". Using a positive D value will drive the vehicle into the ground!
    The code sleeps for a time (DURATION_SEC) to give the vehicle time to reach each position (rather than 
    sending commands based on proximity).
    The code also sets the region of interest (MAV_CMD_DO_SET_ROI) via the `set_roi()` method. This points the 
    camera gimbal at the the selected location (in this case it aligns the whole vehicle to point at the ROI).
    """	

    print("Yaw 0 absolute (North)")
    condition_yaw(0)
    print("North (m): ", SIZE_M, ", East (m): 0m, Height (m):", HEIGHT_M," for", DURATION_SEC, "seconds")
    goto_position_target_local_ned(SIZE_M, 0, -HEIGHT_M)
    time.sleep(DURATION_SEC)

    print("Yaw 90 absolute (East)")
    condition_yaw(90)
    print("North (m): ", SIZE_M, ", East (m): ", SIZE_M, " Height (m):", HEIGHT_M," for", DURATION_SEC, "seconds")
    goto_position_target_local_ned(SIZE_M, SIZE_M, -HEIGHT_M)
    time.sleep(DURATION_SEC)

    print("Yaw 180 absolute (South)")
    condition_yaw(180)
    print("North (m): 0m, East (m): ", SIZE_M, ", Height (m):", HEIGHT_M," for", DURATION_SEC, "seconds")
    goto_position_target_local_ned(0, SIZE_M, -HEIGHT_M)
    time.sleep(DURATION_SEC)

    print("Yaw 270 absolute (West)")
    condition_yaw(270)
    print("North (m): 0m, East (m): 0m, Height (m):", HEIGHT_M," for", DURATION_SEC, "seconds")
    goto_position_target_local_ned(0, 0, -HEIGHT_M)
    time.sleep(DURATION_SEC)


def vel_control_align_north_and_move_square():
    """
    Fly the vehicle in a path using velocity vectors (the underlying code calls the 
    SET_POSITION_TARGET_LOCAL_NED command with the velocity parameters enabled).
    The thread sleeps for a time (DURATION) which defines the distance that will be travelled.
    The code also sets the yaw (MAV_CMD_CONDITION_YAW) using the `set_yaw()` method in each segment
    so that the front of the vehicle points in the direction of travel
    """
    #Set up velocity vector to map to each direction.
    # vx > 0 => fly North
    # vx < 0 => fly South
    NORTH = 0.5
    SOUTH = -0.5
    
    # Note for vy:
    # vy > 0 => fly East
    # vy < 0 => fly West
    EAST = 0.5
    WEST = -0.5

    # Note for vz: 
    # vz < 0 => ascend
    # vz > 0 => descend
    UP = -0.5
    DOWN = 0.5
    
    # Set duration for each segment.
    DURATION_NORTH_SEC = 4
    DURATION_SOUTH_SEC = 4
    DURATION_EAST_SEC = 4
    DURATION_WEST_SEC = 4

    # Control path using velocity commands
    print("Point the vehicle to a specific direction, then moves using SET_POSITION_TARGET_LOCAL_NED and velocity parameters")

    print("Yaw 0 absolute (North)")
    condition_yaw(0)
    send_ned_velocity(0, 0, 0, 1)
    print("Velocity North")
    send_ned_velocity(NORTH, 0, 0, DURATION_NORTH_SEC)
    send_ned_velocity(0, 0, 0, 1)

    print("Yaw 90 absolute (East)")
    condition_yaw(90)
    print("Velocity East")
    send_ned_velocity(0, EAST, 0, DURATION_EAST_SEC)
    send_ned_velocity(0, 0, 0, 1)

    print("Yaw 180 absolute (South)")
    condition_yaw(180)
    print("Velocity South")
    send_ned_velocity(SOUTH, 0, 0, DURATION_SOUTH_SEC)
    send_ned_velocity(0, 0, 0, 1)

    print("Yaw 270 absolute (West)")
    condition_yaw(270)
    print("Velocity West")
    send_ned_velocity(0, WEST, 0, DURATION_WEST_SEC)
    send_ned_velocity(0, 0, 0, 1)


#######################################
# Main program starts here
#######################################

try:    
    # Wait until the RC channel is turned on and the corresponding channel is switch
    print("Starting autonomous control...")
    while True:
        if (vehicle.mode.name == "LOITER") and (rc_channel_value > rc_control_thres):
            pos_control_align_north_and_move_square()
        elif (vehicle.mode.name == "GUIDED") and (rc_channel_value > rc_control_thres):
            vel_control_align_north_and_move_square()
        else:
            print("Checking rc channel:", rc_control_channel, ", current value:", rc_channel_value, ", threshold to start: ", rc_control_thres)
            time.sleep(1)
            
    # Close vehicle object before exiting script
    print("Close vehicle object")
    vehicle.close()
    print("Completed")

except KeyboardInterrupt:
    vehicle.close()
    print("Vehicle object closed.")
    sys.exit()