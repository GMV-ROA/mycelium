#!/usr/bin/env python3

from mycelium import CameraD435
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        self.camera = CameraD435(
            configuration_mode=self.cfg.d435['configuration_mode'],
            enable_rgb_stream=self.cfg.d435['enable_rgb_stream'],
            enable_depth_stream=self.cfg.d435['enable_depth_stream'],
            enable_infrared_stream=self.cfg.d435['enable_infrared_stream'],
            save_rgb_frames=self.cfg.d435['save_rgb_frames'], 
            save_depth_frames=self.cfg.d435['save_depth_frames'], 
            save_infrared_frames=self.cfg.d435['save_infrared_frames'])
        
        self.camera.start()

    def _sigint_handler(self, sig, frame):
        self.camera.exit_threads = True

    def _sigterm_handler(self, sig, frame):
        self.camera.exit_threads = True
        self.exit_code = 0

    def close_script(self):
        try:
            self.camera.stop()
        except:
            pass


scripter = ScripterExt(log_source="run_d435")
scripter.run()
