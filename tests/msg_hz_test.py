#!/usr/bin/env python3

# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"

import time
import threading
import traceback
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from mycelium.components import RedisBridge, Connector
from mycelium_utils import Scripter, utils, DefaultConfig

from pymavlink import mavutil

class RedisToAPScripterExt:

    instance = None
    i=0
    def __init__(self, **kwargs):
        if not RedisToAPScripterExt.instance:
            RedisToAPScripterExt.instance = RedisToAPScripterExt.__RedisToAPScripterExt(**kwargs)
        
    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __RedisToAPScripterExt(Scripter):

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            self.rb = RedisBridge(db=self.rd_cfg.databases['instruments'])
            self.keys = self.rd_cfg.generate_flat_keys('instruments')
            self.conn = mavutil.mavlink_connection(
                self.cfg.redis_to_ap,
                autoreconnect = True,
                source_system = 1,
                source_component = 93,
                baud=self.cfg.connection_baudrate,
                force_connected=True
            )

            self.lock = threading.Lock()
            default_msg_hz = 30.0
            msg_hz = {
                'send_vision_position_estimate': 30.0,
                'send_obstacle_distance': 15.0
            }

            self.mavlink_thread = threading.Thread(target=self.mavlink_loop, args=[self.conn])
            self.mavlink_thread.start()
            self.sched = BackgroundScheduler()
            logging.getLogger('apscheduler').setLevel(logging.ERROR)

            self.data = {}
            for k, v in self.keys.items():
                try:
                    if v in msg_hz.keys():
                        seconds = 1.0/msg_hz[v]
                    else:
                        seconds = 1.0/default_msg_hz
                    
                    func = getattr(self, v)
                    self.sched.add_job(self.send_message, 
                        'interval', 
                        seconds=seconds, 
                        args=[func, k],
                        max_instances=1
                    )
                except:
                    utils.progress(traceback)
                else:
                    self.data[k] = None

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

        def run_main(self):
            self.sched.start()
            while not self.exit_threads:
                with self.lock:
                    for k, _ in self.keys.items():
                        self.data[k] = self.rb.get_key_by_string(k)
                    # time.sleep(0.3)
                    
                # self.conn.send_heartbeat()
                # m = self.conn.get_callbacks(['HEARTBEAT'])
                # if m is None:
                #     continue
                # self.logger.log_debug("Received callback: %s" % m)
                # # utils.progress(m)

        def mavlink_loop(self, conn, callbacks=['HEARTBEAT']):
            while not self.exit_threads:
                self.conn.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
                                    mavutil.mavlink.MAV_AUTOPILOT_GENERIC,
                                    0,
                                    0,
                                    0)
                m = self.conn.recv_match(type=callbacks, timeout=1, blocking=True)
                if m is None:
                    continue
                self.logger.log_debug("Received callback: %s" % m)

        def send_message(self, func, key):
            while not self.exit_threads:
                with self.lock:
                    try:
                        value = self.data[key]
                        if value is not None:
                            func(*value)
                    except Exception as e:
                        self.logger.log_error("Could not send %s"%e)

        def close_script(self):
            try:
                self.sched.shutdown()
                self.mavlink_thread.join()
                self.conn.close()
            except:
                pass


scripter = RedisToAPScripterExt(log_source="redis_to_ap")
scripter.run()
