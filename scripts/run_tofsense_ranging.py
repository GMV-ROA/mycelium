#!/usr/bin/env python3

from mycelium import TOFSenseRanging
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        self.ranging_sensor = TOFSenseRanging()
        self.ranging_sensor.start()

    def _sigint_handler(self, sig, frame):
        self.ranging_sensor.exit_threads = True

    def _sigterm_handler(self, sig, frame):
        self.ranging_sensor.exit_threads = True
        self.exit_code = 0

    def close_script(self):
        try:
            self.ranging_sensor.stop()
        except:
            pass


scripter = ScripterExt(log_source="run_tofsense_ranging")
scripter.run()