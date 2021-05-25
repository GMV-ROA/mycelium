#!/usr/bin/env python3

import sys
sys.path.append("/usr/local/lib/")

import os
import time
from threading import Thread
import transformations as tf
import numpy as np
import math as m
import csv

import pyrealsense2 as rs
from mycelium.components import Camera, RedisBridge


class CameraT265(Camera):

    def __init__(self):
        self.enable_pose_stream = False
        super().__init__(Camera.TYPE_T265)        
        self._setup_save_dir()

    def _setup_parameters(self):
        self.scale_factor = self.cfg.t265['scale_factor']
        self.jump_threshold = self.cfg.t265['jump_threshold']
        self.jump_speed_threshold = self.cfg.t265['jump_speed_threshold']
        self.compass_enabled = self.cfg.t265['compass_enabled']
        self.heading_north_yaw = None
        self.rb_0 = RedisBridge(db=self.rd_cfg.databases['robot'])

        if self.compass_enabled:
            att = self.rb_0.get_key('ATTITUDE')
            if att is not None:
                self.heading_north_yaw = att['yaw']
            else:
                self.compass_enabled = False
                self.logger.log_warn("Failed to enable compass, could not retrieve attitude yaw")
        
        self._initialize_compute_vars()
        # body offset - see initial script
        
        self.metadata = ['enable_pose_stream']

    def _initialize_compute_vars(self):
        self.prev_data = None
        self.reset_counter = 1
        self.current_confidence_level= None

        # Initialize with camera orientation
        self.H_aeroRef_T265Ref = np.array([[0,0,-1,0],[1,0,0,0],[0,-1,0,0],[0,0,0,1]])
        xr = m.radians(self.cfg.t265['camera_rot_x'])
        yr = m.radians(self.cfg.t265['camera_rot_y'])
        zr = m.radians(self.cfg.t265['camera_rot_z'])
        self.H_T265body_aeroBody = (tf.euler_matrix(xr, yr, zr)).dot(np.linalg.inv(self.H_aeroRef_T265Ref))
        self.H_aeroRef_aeroBody = None

        # V_aeroRef_aeroBody # vision speed estimate message
        # H_aeroRef_PrevAeroBody # vision position delta message

        self.frames = None
        self.pose_estimate_data = None

    def _setup_threads(self):
        super()._setup_threads()
        self.threads.append(Thread(target=self._save_pos_estimate))

    def _save_pos_estimate(self):
        csv_file = self.save_data_dir + 't265_pos_estimate.csv'
        file_exists = os.path.exists(csv_file)
        with open(csv_file, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = [
                    'current_time_us', 
                    'local_x_pos',
                    'local_y_pos',
                    'local_z_pos',
                    'roll_angle',
                    'pitch_angle',
                    'yaw_angle',
                    'covariance',
                    'reset_counter',
                    'gps_1_lat',
                    'gps_1_lon',
                    'gps_1_fix_type',
                    'gps_2_lat',
                    'gps_2_lon',
                    'gps_2_fix_type'
                ]
                csvwriter.writerow(header)        
                
            while not self.exit_threads:
                self.rb_i.add_key(self.pose_estimate_data, self.camera_type, 'vision_position_estimate', expiry=self.cfg.t265['save_redis_expiry'])
                self._save_csv(csvwriter, self.pose_estimate_data)

    def _save_csv(self, csvwriter, data):
        if data:
            try:
                data += self._get_gps_data()
                csvwriter.writerow(data)
            except Exception as e:
                self.logger.log_warn("Could not write pose data to csv: %s" % e)

    def _realsense_notification_callback(notif):
        self.logger.log_info(notif)

    def _open_pipe(self):
        self.pipe = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.pose)
        device = config.resolve(self.pipe).get_device()
        pose_sensor = device.first_pose_sensor()
        pose_sensor.set_notifications_callback(self._realsense_notification_callback)
        self.enable_pose_stream = True
        self.pipe.start(config)

    def _process_frames(self):
        self.frames = self.pipe.wait_for_frames()
        pose = self.frames.get_pose_frame()
        if pose:
            # Pose data consists of translation and rotation
            data = pose.get_pose_data()
                
            # Confidence level value from T265: 0-3, remapped to 0 - 100: 0% - Failed / 33.3% - Low / 66.6% - Medium / 100% - High  
            self.current_confidence_level = float(data.tracker_confidence * 100 / 3)  

            # In transformations, Quaternions w+ix+jy+kz are represented as [w, x, y, z]!
            H_T265Ref_T265body = tf.quaternion_matrix([data.rotation.w, data.rotation.x, data.rotation.y, data.rotation.z]) 
            H_T265Ref_T265body[0][3] = data.translation.x * self.scale_factor
            H_T265Ref_T265body[1][3] = data.translation.y * self.scale_factor
            H_T265Ref_T265body[2][3] = data.translation.z * self.scale_factor

            # Transform to aeronautic coordinates (body AND reference frame!)
            self.H_aeroRef_aeroBody = self.H_aeroRef_T265Ref.dot(H_T265Ref_T265body.dot(self.H_T265body_aeroBody))
            
            # vision_speed_estimate_message
            # Calculate GLOBAL XYZ speed (speed from T265 is already GLOBAL)
            # V_aeroRef_aeroBody = tf.quaternion_matrix([1,0,0,0])
            # V_aeroRef_aeroBody[0][3] = data.velocity.x
            # V_aeroRef_aeroBody[1][3] = data.velocity.y
            # V_aeroRef_aeroBody[2][3] = data.velocity.z
            # V_aeroRef_aeroBody = H_aeroRef_T265Ref.dot(V_aeroRef_aeroBody)

            # Check for pose jump and increment reset_counter
            if self.prev_data is not None:
                delta_translation = [data.translation.x - self.prev_data.translation.x, data.translation.y - self.prev_data.translation.y, data.translation.z - self.prev_data.translation.z]
                delta_velocity = [data.velocity.x - self.prev_data.velocity.x, data.velocity.y - self.prev_data.velocity.y, data.velocity.z - self.prev_data.velocity.z]
                position_displacement = np.linalg.norm(delta_translation)
                speed_delta = np.linalg.norm(delta_velocity)

                if (position_displacement > self.jump_threshold) or (speed_delta > self.jump_speed_threshold):
                    if position_displacement > self.jump_threshold:
                        self.logger.log_warn("Position jumped by: %s" % position_displacement)
                    elif speed_delta > self.jump_speed_threshold:
                        self.logger.log_warn("Speed jumped by: %s" % speed_delta)
                    self._increment_reset_counter()
                    
            self.prev_data = data

            # Take offsets from body's center of gravity (or IMU) to camera's origin into account
            # if self.body_offset_enabled == 1:
            #     H_body_camera = tf.euler_matrix(0, 0, 0, 'sxyz')
            #     H_body_camera[0][3] = body_offset_x
            #     H_body_camera[1][3] = body_offset_y
            #     H_body_camera[2][3] = body_offset_z
            #     H_camera_body = np.linalg.inv(H_body_camera)
            #     H_aeroRef_aeroBody = H_body_camera.dot(H_aeroRef_aeroBody.dot(H_camera_body))

            # Realign heading to face north using initial compass data
            if self.compass_enabled:
                self.H_aeroRef_aeroBody = self.H_aeroRef_aeroBody.dot( tf.euler_matrix(0, 0, self.heading_north_yaw, 'sxyz'))

            self._compute_pose_estimate(data)

    def _increment_reset_counter(self):
        if self.reset_counter >= 255:
            self.reset_counter = 1
        self.reset_counter += 1

    def _compute_pose_estimate(self, data):
        if self.H_aeroRef_aeroBody is not None:
            current_time_us = int(round(time.time() * 1000000))

            # Setup angle data
            rpy_rad = np.array( tf.euler_from_matrix(self.H_aeroRef_aeroBody, 'sxyz'))

            # Setup covariance data, which is the upper right triangle of the covariance matrix, see here: https://files.gitter.im/ArduPilot/VisionProjects/1DpU/image.png
            # Attemp #01: following this formula https://github.com/IntelRealSense/realsense-ros/blob/development/realsense2_camera/src/base_realsense_node.cpp#L1406-L1411
            cov_pose    = self.cfg.t265['linear_accel_cov'] * pow(10, 3 - int(data.tracker_confidence))
            cov_twist   = self.cfg.t265['angular_vel_cov']  * pow(10, 1 - int(data.tracker_confidence))
            covariance  = [cov_pose, 0, 0, 0, 0, 0,
                            cov_pose, 0, 0, 0, 0,
                                cov_pose, 0, 0, 0,
                                    cov_twist, 0, 0,
                                        cov_twist, 0,
                                            cov_twist]
            
            self.pose_estimate_data = [
                current_time_us,
                self.H_aeroRef_aeroBody[0][3],   # Local X position
                self.H_aeroRef_aeroBody[1][3],   # Local Y position
                self.H_aeroRef_aeroBody[2][3],   # Local Z position
                rpy_rad[0],	                # Roll angle
                rpy_rad[1],	                # Pitch angle
                rpy_rad[2],	                # Yaw angle
                covariance,                 # Row-major representation of pose 6x6 cross-covariance matrix
                self.reset_counter          # Estimate reset counter. Increment every time pose estimate jumps.
            ]
            self.logger.log_debug("Captured pose estimate data: %s" % str(self.pose_estimate_data))