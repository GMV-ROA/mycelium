#!/usr/bin/env python3

from mycelium import CameraT265
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        self.camera = CameraT265()
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


scripter = ScripterExt(log_source="run_t265")
scripter.run()