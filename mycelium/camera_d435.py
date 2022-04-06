#!/usr/bin/env python3

import sys
sys.path.append("/usr/local/lib/")

import os
import time
from threading import Thread
import transformations as tf
import numpy as np
import math as m
import traceback

import pyrealsense2.pyrealsense2 as rs
import cv2
import csv

from mycelium.components import Camera, RedisBridge

class CameraD435(Camera):

    CFG_MODE_1 = 1 # Enable RGB and depth streams and don't save frames
    CFG_MODE_2 = 2 # Enable RGB and infrared stream and don't save frames
    CFG_MODE_3 = 3 # Enable only infrared stream and don't save frames
    CFG_MODE_4 = 4 # Custom

    # rs2_stream are types of data provided by RealSense device
    stream_type = {
        'depth': rs.stream.depth,
        'colour': rs.stream.color,
        'infrared': rs.stream.infrared
    }

    # rs2_format identifies how binary data is encoded within a frame
    stream_format = {
        'depth': rs.format.z16,
        'colour': rs.format.bgr8,
        'infrared': rs.format.y8
    }

    filters = {
        'decimation': rs.decimation_filter(),
        'threshold': rs.threshold_filter(),
        'depth_to_disparity': rs.disparity_transform(True),
        'spatial': rs.spatial_filter(),
        'temporal': rs.temporal_filter(),
        'hole_filling': rs.hole_filling_filter(),
        'disparity_to_depth': rs.disparity_transform(False)
    }

    DS5_product_ids = ["0AD1", "0AD2", "0AD3", "0AD4", "0AD5", "0AF6", "0AFE", "0AFF", "0B00", "0B01", "0B03", "0B07", "0B3A", "0B5C"]

    def __init__(self, 
        configuration_mode=1,
        enable_rgb_stream=True,
        enable_depth_stream=True,
        enable_infrared_stream=True,
        save_rgb_frames=False, 
        save_depth_frames=False, 
        save_infrared_frames=False):

        self._init_mode(configuration_mode, 
            enable_rgb_stream, 
            enable_depth_stream, 
            enable_infrared_stream, 
            save_rgb_frames, 
            save_depth_frames, 
            save_infrared_frames)

        super().__init__(Camera.TYPE_D435)
        self.logger.log_info("Starting camera in configuration mode %d" % configuration_mode)   
        self._setup_save_dir()
        self.colour_frame_process = None
        self.depth_frame_process = None
        self.ir1_frame_process = None
        self.ir2_frame_process = None

    def _init_mode(self,
        configuration_mode, 
        enable_rgb_stream, 
        enable_depth_stream, 
        enable_infrared_stream, 
        save_rgb_frames, 
        save_depth_frames, 
        save_infrared_frames):
        if configuration_mode == self.CFG_MODE_1:
            cfg = [True, True, False, False, False, False]
        elif configuration_mode == self.CFG_MODE_2:
           cfg = [True, False, True, False, False, False]
        elif configuration_mode == self.CFG_MODE_3:
            cfg = [False, False, True, False, False, False]
        else:
            cfg = [enable_rgb_stream, 
                enable_depth_stream, 
                enable_infrared_stream, 
                save_rgb_frames, 
                save_depth_frames, 
                save_infrared_frames]
        
        self.enable_rgb_stream = cfg[0]
        self.enable_depth_stream = cfg[1]
        self.enable_infrared_stream = cfg[2]
        self.save_rgb_frames = cfg[3]
        self.save_depth_frames = cfg[4]
        self.save_infrared_frames = cfg[5]        

    def _setup_parameters(self):
        self.depth_range_m = [self.cfg.d435['depth_min_m'], self.cfg.d435['depth_max_m']]
        
        if self.cfg.d435['filters']['threshold']:
            self.filters['threshold'].set_option(rs.option.min_distance, self.depth_range_m[0])
            self.filters['threshold'].set_option(rs.option.max_distance, self.depth_range_m[1])

        self.camera_facing_angle_degree = self.cfg.d435['camera_facing_angle_degree']
        self.device_id = None
        self.obstacle_line_height_ratio = self.cfg.d435['obstacle_line_height_ratio']
        self.obstacle_line_thickness_pixel = self.cfg.d435['obstacle_line_thickness_pixel']

        self.depth_scale = 0
        self.colorizer = rs.colorizer()
        self.depth_hfov_deg = None
        self.depth_vfov_deg = None

        self.stream_cfg = {
            'd_w': self.cfg.d435['depth_width'],
            'd_h': self.cfg.d435['depth_height'],
            'd_fps': self.cfg.d435['depth_fps'],
            'c_w': self.cfg.d435['color_width'],
            'c_h': self.cfg.d435['color_height'],
            'c_fps': self.cfg.d435['color_fps'],
            'i_w': self.cfg.d435['infrared_width'],
            'i_h': self.cfg.d435['infrared_height'],
            'i_fps': self.cfg.d435['infrared_fps']
        }

        self._initialize_compute_vars()
        # body offset - see initial script
        self.metadata = ['enable_rgb_stream', 'enable_infrared_stream', 'enable_depth_stream']

    def _initialize_compute_vars(self):
        self.vehicle_pitch_rad = None
        self.current_time_us = 0
        self.last_obstacle_distance_sent_ms = 0  # value of current_time_us when obstacle_distance last sent

        # Obstacle distances in front of the sensor, starting from the left in increment degrees to the right
        # See here: https://mavlink.io/en/messages/common.html#OBSTACLE_DISTANCE
        self.min_depth_cm = int(self.depth_range_m[0] * 100)  # In cm
        self.max_depth_cm = int(self.depth_range_m[1] * 100)  # In cm, should be a little conservative
        self.distances_array_length = 72
        self.angle_offset = None
        self.increment_f  = None
        self.distances = np.ones((self.distances_array_length,), dtype=np.uint16) * (self.max_depth_cm + 1)
        self.obstacle_distance_data = None

    def _find_device_that_supports_advanced_mode(self):
        ctx = rs.context()
        devices = ctx.query_devices()
        for dev in devices:
            if dev.supports(rs.camera_info.product_id) and str(dev.get_info(rs.camera_info.product_id)) in self.DS5_product_ids:
                name = rs.camera_info.name
                if dev.supports(name):
                    self.logger.log_info("Found device that supports advanced mode: %s" % dev.get_info(name))
                    self.device_id = dev.get_info(rs.camera_info.serial_number)
                    return dev

        raise Exception("No device that supports advanced mode was found")

    # Loop until we successfully enable advanced mode
    def _realsense_enable_advanced_mode(self, advnc_mode):
        while not advnc_mode.is_enabled():
            self.logger.log_info("Trying to enable advanced mode...")
            advnc_mode.toggle_advanced_mode(True)
            # At this point the device will disconnect and re-connect.
            self.logger.log_info("Sleeping for 5 seconds...")
            time.sleep(5)
            # The 'dev' object will become invalid and we need to initialize it again
            dev = self._find_device_that_supports_advanced_mode()
            advnc_mode = rs.rs400_advanced_mode(dev)
            self.logger.log_info("Advanced mode is %s" "enabled" if advnc_mode.is_enabled() else "disabled")

    # Load the settings stored in the JSON file
    def _realsense_load_settings_file(self, advnc_mode, setting_file):
        # Sanity checks
        if os.path.isfile(setting_file):
            self.logger.log_info("Setting file found: %s" % setting_file)
        else:
            self.logger.log_info("Cannot find setting file: %s" % setting_file)
            sys.exit()

        if advnc_mode.is_enabled():
            self.logger.log_info("Advanced mode is enabled")
        else:
            self.logger.log_info("Device does not support advanced mode")
            sys.exit()
        
        # Input for load_json() is the content of the json file, not the file path
        with open(setting_file, 'r') as file:
            json_text = file.read().strip()

        advnc_mode.load_json(json_text)

    def _realsense_configure_setting(self, setting_file):
        device = self._find_device_that_supports_advanced_mode()
        advnc_mode = rs.rs400_advanced_mode(device)
        self._realsense_enable_advanced_mode(advnc_mode)
        self._realsense_load_settings_file(advnc_mode, setting_file)

    def _enable_stream(self, stype, config):
        if stype not in ['depth', 'colour', 'infrared']:
            raise Exception("Stream type invalid")

        ix = stype[0]        
        if stype == 'infrared':
            config.enable_stream(self.stream_type[stype], 1, self.stream_cfg['%s_w'%ix], self.stream_cfg['%s_h'%ix], self.stream_format[stype], self.stream_cfg['%s_fps'%ix])
            config.enable_stream(self.stream_type[stype], 2, self.stream_cfg['%s_w'%ix], self.stream_cfg['%s_h'%ix], self.stream_format[stype], self.stream_cfg['%s_fps'%ix])
        else:
            config.enable_stream(self.stream_type[stype], self.stream_cfg['%s_w'%ix], self.stream_cfg['%s_h'%ix], self.stream_format[stype], self.stream_cfg['%s_fps'%ix])
        
        return config

    def _open_pipe(self):
        self.pipe = rs.pipeline()
        config = rs.config()
        # Configure image stream(s)
        if self.device_id:
            # connect to a specific device ID
            config.enable_device(self.device_id)
        
        if self.enable_rgb_stream:
            config = self._enable_stream('colour', config)
        if self.enable_depth_stream:
            config = self._enable_stream('depth', config)
        if self.enable_infrared_stream:
            config = self._enable_stream('infrared', config)
        
        # Start streaming with requested config
        profile = self.pipe.start(config)

        if self.enable_depth_stream:
            # Getting the depth sensor's depth scale (see rs-align example for explanation)
            depth_sensor = profile.get_device().first_depth_sensor()
            self.depth_scale = depth_sensor.get_depth_scale()
            self.logger.log_info("Depth scale is: %s" % self.depth_scale)
            
            self._set_obstacle_distance_params()

    # Setting parameters for the OBSTACLE_DISTANCE message based on actual camera's intrinsics and user-defined params
    def _set_obstacle_distance_params(self):        
        # Obtain the intrinsics from the camera itself
        profiles = self.pipe.get_active_profile()
        depth_intrinsics = profiles.get_stream(self.stream_type['depth']).as_video_stream_profile().intrinsics
        self.logger.log_info("Depth camera intrinsics: %s" % depth_intrinsics)
        
        # For forward facing camera with a horizontal wide view:
        #   HFOV=2*atan[w/(2.fx)],
        #   VFOV=2*atan[h/(2.fy)],
        #   DFOV=2*atan(Diag/2*f),
        #   Diag=sqrt(w^2 + h^2)
        self.depth_hfov_deg = m.degrees(2 * m.atan(self.stream_cfg['d_w'] / (2 * depth_intrinsics.fx)))
        self.depth_vfov_deg = m.degrees(2 * m.atan(self.stream_cfg['d_h'] / (2 * depth_intrinsics.fy)))
        self.logger.log_info("Depth camera HFOV: %0.2f degrees" % self.depth_hfov_deg)
        self.logger.log_info("Depth camera VFOV: %0.2f degrees" % self.depth_vfov_deg)

        self.angle_offset = self.camera_facing_angle_degree - (self.depth_hfov_deg / 2)
        self.increment_f = self.depth_hfov_deg / self.distances_array_length
        self.logger.log_info("OBSTACLE_DISTANCE angle_offset: %0.3f" % self.angle_offset)
        self.logger.log_info("OBSTACLE_DISTANCE increment_f: %0.3f" % self.increment_f)
        self.logger.log_info("OBSTACLE_DISTANCE coverage: from %0.3f to %0.3f degrees" %
            (self.angle_offset, self.angle_offset + self.increment_f * self.distances_array_length))

        # Sanity check for depth configuration
        if self.obstacle_line_height_ratio < 0 or self.obstacle_line_height_ratio > 1:
            self.logger.log_info("Please make sure the horizontal position is within [0-1]: %s"  % self.obstacle_line_height_ratio)
            sys.exit()

        if self.obstacle_line_thickness_pixel < 1 or self.obstacle_line_thickness_pixel > self.stream_cfg['d_h']:
            self.logger.log_info("Please make sure the thickness is within [0-depth_height]: %s" % self.obstacle_line_thickness_pixel)
            sys.exit()

    # Find the height of the horizontal line to calculate the obstacle distances
    #   - Basis: depth camera's vertical FOV, user's input
    #   - Compensation: vehicle's current pitch angle
    def _find_obstacle_line_height(self):
        # Basic position
        obstacle_line_height = self.stream_cfg['d_h'] * self.obstacle_line_height_ratio

        attitude = self.rb_r.get_key('ATTITUDE')
        if attitude is not None:
            self.vehicle_pitch_rad = attitude['pitch']

        # Compensate for the vehicle's pitch angle if data is available
        if self.vehicle_pitch_rad is not None and self.depth_vfov_deg is not None:
            delta_height = m.sin(self.vehicle_pitch_rad / 2) / m.sin(m.radians(self.depth_vfov_deg) / 2) * self.stream_cfg['d_h']
            obstacle_line_height += delta_height

        # Sanity check
        if obstacle_line_height < 0:
            obstacle_line_height = 0
        elif obstacle_line_height > self.stream_cfg['d_h']:
            obstacle_line_height = self.stream_cfg['d_h']
        
        return obstacle_line_height

    # Calculate the distances array by dividing the FOV (horizontal) into $distances_array_length rays,
    # then pick out the depth value at the pixel corresponding to each ray. Based on the definition of
    # the MAVLink messages, the invalid distance value (below MIN/above MAX) will be replaced with MAX+1.
    #    
    # [0]    [35]   [71]    <- Output: distances[72]
    #  |      |      |      <- step = width / 72
    #  ---------------      <- horizontal line, or height/2
    #  \      |      /
    #   \     |     /
    #    \    |    /
    #     \   |   /
    #      \  |  /
    #       \ | /           
    #       Camera          <- Input: depth_mat, obtained from depth image
    #
    # Note that we assume the input depth_mat is already processed by at least hole-filling filter.
    # Otherwise, the output array might not be stable from frame to frame.
    # @njit   # Uncomment to optimize for performance. This uses numba which requires llmvlite (see instruction at the top)
    def _distances_from_depth_image(self, obstacle_line_height, depth_mat):
        min_depth_m = self.depth_range_m[0]
        max_depth_m = self.depth_range_m[1]

        # Parameters for depth image
        depth_img_width  = depth_mat.shape[1]
        depth_img_height = depth_mat.shape[0]

        # Parameters for obstacle distance message
        step = depth_img_width / self.distances_array_length

        for i in range(self.distances_array_length):
            # Each range (left to right) is found from a set of rows within a column
            #  [ ] -> ignored
            #  [x] -> center + obstacle_line_thickness_pixel / 2
            #  [x] -> center = obstacle_line_height (moving up and down according to the vehicle's pitch angle)
            #  [x] -> center - obstacle_line_thickness_pixel / 2
            #  [ ] -> ignored
            #   ^ One of [distances_array_length] number of columns, from left to right in the image
            center_pixel = obstacle_line_height
            upper_pixel = center_pixel + self.obstacle_line_thickness_pixel / 2
            lower_pixel = center_pixel - self.obstacle_line_thickness_pixel / 2

            # Sanity checks
            if upper_pixel > depth_img_height:
                upper_pixel = depth_img_height
            elif upper_pixel < 1:
                upper_pixel = 1
            if lower_pixel > depth_img_height:
                lower_pixel = depth_img_height - 1
            elif lower_pixel < 0:
                lower_pixel = 0

            # Converting depth from uint16_t unit to metric unit. depth_scale is usually 1mm following ROS convention.
            # dist_m = depth_mat[int(obstacle_line_height), int(i * step)] * depth_scale
            min_point_in_scan = np.min(depth_mat[int(lower_pixel):int(upper_pixel), int(i * step)])
            dist_m = min_point_in_scan * self.depth_scale

            # Default value, unless overwritten: 
            #   A value of max_distance + 1 (cm) means no obstacle is present. 
            #   A value of UINT16_MAX (65535) for unknown/not used.
            self.distances[i] = 65535

            # Note that dist_m is in meter, while distances[] is in cm.
            if dist_m > min_depth_m and dist_m < max_depth_m:
                self.distances[i] = dist_m * 100

        if self.current_time_us == self.last_obstacle_distance_sent_ms:
            # no new frame
            return
        self.last_obstacle_distance_sent_ms = self.current_time_us
        if self.angle_offset is None or self.increment_f is None:
            self.logger.log_warn("Please call set_obstacle_distance_params before continuing")
        else:
            self.obstacle_distance_data = [
                self.current_time_us,       # us Timestamp (UNIX time or time since system boot)
                0,                          # sensor_type, defined here: https://mavlink.io/en/messages/common.html#MAV_DISTANCE_SENSOR
                self.distances.tolist(),    # distances,    uint16_t[72],   cm
                0,                          # increment,    uint8_t,        deg
                self.min_depth_cm,	        # min_distance, uint16_t,       cm
                self.max_depth_cm,          # max_distance, uint16_t,       cm
                self.increment_f,	        # increment_f,  float,          deg
                self.angle_offset,          # angle_offset, float,          deg
                12                          # MAV_FRAME, vehicle-front aligned: https://mavlink.io/en/messages/common.html#MAV_FRAME_BODY_FRD    
            ]
            self.logger.log_debug("Captured obstacle distance data: %s" % str(self.obstacle_distance_data))

    def _setup_threads(self):
        super()._setup_threads()
        if self.enable_depth_stream:
            self.threads.append(Thread(target=self._save_obstacle_distance))

        self.threads.append(Thread(target=self._check_save_data_flags))
        self.threads.append(Thread(target=self._save_rgb_frames))
        self.threads.append(Thread(target=self._save_depth_frames))
        self.threads.append(Thread(target=self._save_infrared_frames))       
        # self.threads.append(Thread(target=self._save_rgb_metadata))
        # self.threads.append(Thread(target=self._save_depth_metadata))
        # self.threads.append(Thread(target=self._save_ir_metadata))

    def _save_obstacle_distance(self):
        while not self.exit_threads:
            self.rb_i.add_key(self.obstacle_distance_data, self.camera_type, 'obstacle_distance', expiry=self.cfg.d435['save_redis_expiry'])

    def _save_distance_sensor(self): # (average or singles ?)
        return

    def _check_save_data_flags(self):
        # Initialise keys
        self.rb_i.add_key(int(self.save_rgb_frames), self.camera_type, 'save_rgb_frames')
        self.rb_i.add_key(int(self.save_depth_frames), self.camera_type, 'save_depth_frames')
        self.rb_i.add_key(int(self.save_infrared_frames), self.camera_type, 'save_infrared_frames')
        while not self.exit_threads:
            self.save_rgb_frames = bool(self.rb_i.get_key(self.camera_type, 'save_rgb_frames'))
            self.save_depth_frames = bool(self.rb_i.get_key(self.camera_type, 'save_depth_frames'))
            self.save_infrared_frames = bool(self.rb_i.get_key(self.camera_type, 'save_infrared_frames'))
            time.sleep(1)

    def _save_frame(self, csvwriter, frame, last_frame_time, ref=None, *prepend):
        try:
            profile = frame.get_profile()
            stype = profile.stream_name()
        except:
            return None     

        if ref is None:      
            ref = stype.lower()

        if frame:
            timestamp = frame.get_timestamp()
            if timestamp == last_frame_time:
                return timestamp
            try:
                if stype == 'stream.depth':
                    img = np.asanyarray(frame.as_frame().get_data())
                    img = cv2.convertScaleAbs(img, alpha=0.03)
                else:
                    img = np.asanyarray(frame.get_data())

                filename = "%s%s.%s.png" % (self.save_data_dir, str(timestamp), ref)
                cv2.imwrite(filename, img)
                self.logger.log_debug("Saved %s frame: %s" % (ref, filename))
                self._save_metadata(csvwriter, frame, ref, *prepend)
            except csv.Error:
                self.logger.log_warn("Could not write %s metadata" % ref)
                self.logger.log_debug(traceback.format_exc())
            except:
                self.logger.log_warn("Could not save %s frame" % ref)
                self.logger.log_debug(traceback.format_exc())
                
            return timestamp

        return None
    
    def _generate_csv_header(self, ir_stream=False):
        gps_header = [
            'gps_1_lat',
            'gps_1_lon',
            'gps_1_fix_type',
            'gps_2_lat',
            'gps_2_lon',
            'gps_2_fix_type'
        ]
        ir_header = ['ir_stream']

        if ir_stream:
            return ir_header + self.frame_metadata_values + gps_header
        
        return self.frame_metadata_values + gps_header


    def _save_metadata(self, csvwriter, frame, ref=None, *prepend):
        metadata = []
        if prepend:
            metadata = prepend + metadata

        for value in self.frame_metadata_values:
            if frame.supports_frame_metadata(value):
                data = frame.get_frame_metadata(value)
            else:
                data = ""
            metadata.append(data)

        csvwriter.writerow(metadata)

    def _save_rgb_frames(self):
        last_frame_time = None
        filename = self.save_data_dir + 'rgb_metadata.csv'
        file_exists = os.path.exists(filename)
        with open(filename, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = self._generate_csv_header()
                csvwriter.writerow(header)

            while not self.exit_threads:
                if self.colour_frame_process and self.save_rgb_frames:
                    last_frame_time = self._save_frame(csvwriter, self.colour_frame_process, last_frame_time)

    def _save_depth_frames(self):
        last_frame_time = None
        filename = self.save_data_dir + 'depth_metadata.csv'
        file_exists = os.path.exists(filename)
        with open(filename, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = self._generate_csv_header()
                csvwriter.writerow(header)

            while not self.exit_threads:
                if self.depth_frame_process and self.save_depth_frames:
                    last_frame_time = self._save_frame(csvwriter, self.depth_frame_process, last_frame_time)
            
    def _save_infrared_frames(self):
        last_frame_time_1 = None
        last_frame_time_2 = None
        filename = self.save_data_dir + 'infrared_metadata.csv'
        file_exists = os.path.exists(filename)
        with open(filename, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = self._generate_csv_header(ir_stream=True)
                csvwriter.writerow(header)

            while not self.exit_threads:
                if self.ir1_frame_process and self.save_infrared_frames:
                    last_frame_time_1 = self._save_frame(csvwriter, self.ir1_frame_process, last_frame_time_1, 1, ref="infrared1")
                if self.ir2_frame_process and self.save_infrared_frames:
                    last_frame_time_2 = self._save_frame(csvwriter, self.ir2_frame_process, last_frame_time_2, 2, ref="infrared2")

    def start(self):
        if self.cfg.d435['use_preset_file']:
            dir_path = os.environ['MYCELIUM_CFG_ROOT']
            preset_file = os.path.join(dir_path, self.cfg.d435['preset_file'])
            self._realsense_configure_setting(preset_file)
        
        for t in self.threads:
            t.start()

        self._open_pipe()        
        while not self.exit_threads:
            self._process_frames()

    def _process_frames(self):
        frames = self.pipe.wait_for_frames()
        color_frame = None
        depth_frame = None
        ir1_frame = None
        ir2_frame = None

        if self.enable_depth_stream:
            depth_frame = frames.get_depth_frame()
        if self.enable_rgb_stream:
            color_frame = frames.get_color_frame()
        if self.enable_infrared_stream:
            ir1_frame = frames.get_infrared_frame(1)
            ir2_frame = frames.get_infrared_frame(2)

        if color_frame:
            self.colour_frame_process = color_frame

        if ir1_frame:
            self.ir1_frame_process = ir1_frame

        if ir2_frame:
            self.ir2_frame_process = ir2_frame

        if depth_frame:
            # Store the timestamp for MAVLink messages
            self.current_time_us = int(round(time.time() * 1000000))

            # Apply the filters
            filtered_frame = depth_frame
            cfg_filters = self.cfg.d435['filters']
            for k, v in cfg_filters.items():
                if v:
                    filtered_frame = self.filters[k].process(filtered_frame)

            self.depth_frame_process = filtered_frame

            # Extract depth in matrix form
            depth_data = filtered_frame.as_frame().get_data()
            depth_mat = np.asanyarray(depth_data)

            # Create obstacle distance data from depth image
            obstacle_line_height = self._find_obstacle_line_height()
            self._distances_from_depth_image(obstacle_line_height, depth_mat)
        