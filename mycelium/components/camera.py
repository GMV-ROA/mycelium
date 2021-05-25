#!/usr/bin/env python3

import sys
sys.path.append("/usr/local/lib/")

import os
from os.path import dirname, realpath
from threading import Thread
import datetime

import pyrealsense2 as rs
from mycelium.components import RedisBridge, Base

class Camera(Base):

    TYPE_T265 = 't265'
    TYPE_D435 = 'd435'

    ALIVE_FLAG = 'alive'

    def __init__(self, camera_type):
        super().__init__()
        if camera_type != self.TYPE_T265 and camera_type != self.TYPE_D435:
            raise Exception("Camera type invalid")
        self.camera_type = camera_type
        self.pipe = None
        self.metadata = {}
        self.threads = []
        self.exit_threads = False
        self.rb_i = RedisBridge(db=self.rd_cfg.databases['instruments'])
        self.rb_r = RedisBridge(db=self.rd_cfg.databases['robot'])
        self._init_frame_metadata_values()
        self._setup_parameters()
        self._setup_threads()

    def start(self):
        for t in self.threads:
            t.start()
            
        self._open_pipe()
        while not self.exit_threads:
            self._process_frames()

    def stop(self):
        self.exit_threads = True
        try:
            self.pipe.stop()
        except:
            self.logger.log_error("Pipe closing")

        for t in self.threads:
            try:
                t.join()
            except:
                self.logger.log_warn("Thread failed to join")
                
    def __enter__(self):
        return self

    def __exit__(self):
        self.stop()

    def _setup_parameters(self):
        # Setup sensor-specific parameters
        raise NotImplementedError

    def _setup_threads(self):
        self.threads = [Thread(target=self._send_metadata)]

    def _send_metadata(self):
        while not self.exit_threads:
            try:
                for key in self.metadata:
                    value = getattr(self, key)
                    self.rb_i.add_key(value, self.camera_type, key, expiry=5)
            except Exception as e:
                self.logger.log_error("Invalid redis metadata: %s" % str(e))

    def _setup_save_dir(self):
        try:
            dir_path = dirname(dirname(dirname(realpath(__file__))))
            datestamp = datetime.datetime.now().strftime("%Y_%m_%d")
            self.save_data_dir = dir_path + "/" + self.cfg.save_data_dir + "/" + datestamp + "/"
            if not os.path.exists(self.save_data_dir):
                os.makedirs(self.save_data_dir)
        except:
            self.logger.log_error("Could not create directory: %s" % self.save_data_dir)

    def _open_pipe(self):    
        raise NotImplementedError

    def _process_frames(self):
        # Process frames from pipe
        raise NotImplementedError

    def _init_frame_metadata_values(self):
        self.frame_metadata_values = []
        for k,v in rs.frame_metadata_value.__dict__.items():
            if k.startswith('__') or k == 'name':
                continue
            self.frame_metadata_values.append(v)

    def _get_gps_data(self):
        gps_data_1 = self.rb_0.get_key('GPS_RAW_INT')
        gps_data_2 = self.rb_0.get_key('GPS2_RAW')
        gps = [None, None, None, None, None, None]

        if gps_data_1 is not None:
            # Use 1
            gps[0] = gps_data_1['lat']
            gps[1] = gps_data_1['lon']
            gps[2] = gps_data_1['fix_type']

        if gps_data_2 is not None:
            # Use 2
            gps[3] = gps_data_2['lat']
            gps[4] = gps_data_2['lon']
            gps[5] = gps_data_2['fix_type']

        return gps

    