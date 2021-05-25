#!/usr/bin/env python3

from picamera import PiCamera
import time
import datetime
import os

class PicamImpl:

    # Capture modes
    RAW_BAYER = 1
    MAX_RES = 2
    CONSISTENT = 3
    CUSTOM = 4

    def __init__(self, capture_mode=RAW_BAYER, root_dir='data', res_w=4056, res_h=3040, framerate=30, iso=100):
        self.capture_mode = capture_mode
        self.camera = PiCamera()
        self._init_parameters(res_w=res_w, res_h=res_h, framerate=framerate, iso=iso)
        self.set_save_directory(root_dir=root_dir)
        time.sleep(2)
        print("Camera ready")

    def _init_parameters(self, override=False, **params):
        self.camera.resolution = (4056, 3040)
        self.camera.framerate = 30
        self.camera.iso = 100

        if self.capture_mode == self.CUSTOM or override:
            if 'res_w' in params.keys() and 'res_h' in params.keys():
                self.camera.resolution = (params['res_w'], params['res_h'])
            if 'framerate' in params.keys():
                self.camera.framerate = params['framerate']
            if 'iso' in params.keys():
                self.camera.iso = params['iso']
        
        if self.capture_mode == self.RAW_BAYER:
            self.bayer = True
        else: 
            self.bayer = False

        if self.capture_mode == self.CONSISTENT:
            self.camera.shutter_speed = self.camera.exposure_speed
            self.camera.exposure_mode = 'off'
            g = self.camera.awb_gains
            self.camera.awb_mode = 'off'
            self.camera.awb_gains = g
    
    def set_save_directory(self, *dir_levels, root_dir='data'):
        dir_path = os.environ['PICAMERA_ROOT']
        datestamp = datetime.datetime.now().strftime("%Y_%m_%d")
        self.save_dir = os.path.join(dir_path, root_dir, datestamp) + '/'
        if len(dir_levels) > 0:
            self.save_dir += '/'.join(dir_levels)+'/'
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        print("Setting save directory to %s" % self.save_dir)

    def capture_continuous(self):
        break_capture = False
        for filename in self.camera.capture_continuous(self.save_dir+'{timestamp:%Y-%m-%d-%H-%M-%f}.jpg'):
            print("Captured %s" % filename)
            if break_capture:
                break

    def capture_single(self, root=None):
        datestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%f")
        if root is not None:
            datestamp = str(root)+"_"+datestamp
        self.camera.capture(self.save_dir+datestamp+'.jpg', bayer=self.bayer)
        return datestamp
    
    def _filename_generator(self, duration):
        start = time.time()
        end = start+float(duration)
        cur = time.time()
        while cur < end:
            datestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%f")
            yield self.save_dir+datestamp+'.jpg'
            cur = time.time()

    def capture_burst(self, duration):
        self._init_parameters(res_w=800, res_h=600, override=True)
        self.camera.capture_sequence(self._filename_generator(duration), use_video_port=True)
        self._init_parameters()

    def disconnect(self):
        self.camera.close()