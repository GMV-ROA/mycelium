#!/usr/bin/env python3

############################################
##          Ardupilot messenger           ##
############################################

# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"

import time
from pymavlink import mavutil
from mycelium_utils.utils import progress

class Connector():
    '''creates connection to Ardupilot via Mavlink for setting/getting parameters
    '''

    def __init__(self,
        connection_string, 
        connection_baudrate,
        source_system, 
        source_component):
        self.connection_string = connection_string
        self.connection_baudrate = connection_baudrate
        print("Using connection string: ", self.connection_string)
        self.source_system = source_system
        self.source_component = source_component
        self.conn = None
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)

    def __enter__(self):
        return self

    def __exit__(self):
        self.disconnect()

    def connect(self, connection_string, connection_baudrate, source_system, source_component):
        if self.conn is None:
            self.conn = mavutil.mavlink_connection(
                connection_string,
                autoreconnect = True,
                source_system = source_system,
                source_component = source_component,
                baud=connection_baudrate,
                force_connected=True
            )
        return self.conn

    def send_heartbeat(self):
        # self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                                    mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
                                    0,
                                    0,
                                    0)

    def get_callbacks(self, callbacks, timeout=1, blocking=True):
        return self.conn.recv_match(type=callbacks, timeout=timeout, blocking=blocking)

    def set_param(self, param, value):
        param_b = bytes(param, encoding='utf8')
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.param_set_send(
            self.conn.target_system,
            self.conn.target_component,
            param_b,
            value,
            mavutil.mavlink.MAV_PARAM_TYPE_INT8
        )

    def get_param(self, param, timeout=1):
        param_b = bytes(param, encoding='utf8')
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.param_fetch_one(param_b)
        m = None
        while m is None:
            m = self.get_callbacks(callbacks=param_b, timeout=timeout)
        return m

    def set_rc_channel_pwm(self, channel_id, pwm):
        rc_channel_values = [65535 for _ in range(18)]
        rc_channel_values[channel_id - 1] = pwm
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.rc_channels_override_send(
                self.conn.target_system,            # target_system
                self.conn.target_component,         # target_component
                *rc_channel_values                  # RC channel list, in microseconds.
            )       

    def send_msg_to_gcs(self, msg, severity=mavutil.mavlink.MAV_SEVERITY_INFO):
        # MAV_SEVERITY: 0=EMERGENCY 1=ALERT 2=CRITICAL 3=ERROR, 4=WARNING, 5=NOTICE, 6=INFO, 7=DEBUG, 8=ENUM_END
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.statustext_send(severity, msg.encode())

    # https://mavlink.io/en/messages/common.html#VISION_POSITION_ESTIMATE
    def send_vision_position_estimate(self, current_time_us, x, y, z, 
        roll, pitch, yaw, covariance, reset_counter):
        # self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.vision_position_estimate_send(
            current_time_us,        # us Timestamp (UNIX time or time since system boot)
            x,                      # Local X position
            y,                      # Local Y position
            z,                      # Local Z position
            roll,	                # Roll angle
            pitch,	                # Pitch angle
            yaw,	                # Yaw angle
            covariance,             # Row-major representation of pose 6x6 cross-covariance matrix
            reset_counter           # Estimate reset counter. Increment every time pose estimate jumps.
        )

    # def send_vision_position_delta_message(self, current_time_us, delta_time_us, delta_angle_rad, delta_position_m, current_confidence_level):
    #     conn.mav.vision_position_delta_send(
    #             current_time_us,    # us: Timestamp (UNIX time or time since system boot)
    #             delta_time_us,	    # us: Time since last reported camera frame
    #             delta_angle_rad,    # float[3] in radian: Defines a rotation vector in body frame that rotates the vehicle from the previous to the current orientation
    #             delta_position_m,   # float[3] in m: Change in position from previous to current frame rotated into body frame (0=forward, 1=right, 2=down)
    #             current_confidence_level # Normalized confidence value from 0 to 100. 
    #         )

    # def send_vision_speed_estimate(self, current):
    #     self.conn.mav.vision_speed_estimate_send(
    #         current_time_us,            # us Timestamp (UNIX time or time since system boot)
    #         V_aeroRef_aeroBody[0][3],   # Global X speed
    #         V_aeroRef_aeroBody[1][3],   # Global Y speed
    #         V_aeroRef_aeroBody[2][3],   # Global Z speed
    #         covariance,                 # covariance
    #         reset_counter               # Estimate reset counter. Increment every time pose estimate jumps.
    #     )
    
    # https://mavlink.io/en/messages/common.html#OBSTACLE_DISTANCE
    def send_obstacle_distance(self, current_time_us, sensor_type, distances, increment,
        min_distance, max_distance, increment_f, angle_offset, mav_frame):
        # self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.mav.obstacle_distance_send(
            current_time_us,    # us Timestamp (UNIX time or time since system boot)
            sensor_type,        # sensor_type, defined here: https://mavlink.io/en/messages/common.html#MAV_DISTANCE_SENSOR
            distances,          # distances,    uint16_t[72],   cm
            increment,          # increment,    uint8_t,        deg
            min_distance,	    # min_distance, uint16_t,       cm
            max_distance,       # max_distance, uint16_t,       cm
            increment_f,	    # increment_f,  float,          deg
            angle_offset,       # angle_offset, float,          deg
            mav_frame           # MAV_FRAME, vehicle-front aligned: https://mavlink.io/en/messages/common.html#MAV_FRAME_BODY_FRD    
        )
        
    # # https://mavlink.io/en/messages/common.html#DISTANCE_SENSOR
    # def send_single_distance_sensor_msg(distance, orientation):
    #     # Average out a portion of the centermost part
    #     conn.mav.distance_sensor_send(
    #         0,                  # ms Timestamp (UNIX time or time since system boot) (ignored)
    #         min_depth_cm,       # min_distance, uint16_t, cm
    #         max_depth_cm,       # min_distance, uint16_t, cm
    #         distance,           # current_distance,	uint16_t, cm	
    #         0,	                # type : 0 (ignored)
    #         0,                  # id : 0 (ignored)
    #         orientation,        # orientation
    #         0                   # covariance : 0 (ignored)
    #     )

    def set_relay(self, relay_pin, state):
        self.connect(self.connection_string, self.connection_baudrate, self.source_system, self.source_component)
        self.conn.set_relay(relay_pin, state)

    def disconnect(self):
        if self.conn:
            self.conn.close()


