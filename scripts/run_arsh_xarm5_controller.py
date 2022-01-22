#!/usr/bin/env python3

from mycelium import ARSHXarm5Controller
from mycelium_utils import Scripter

class ScripterExt(Scripter):

    def run_main(self):
        self.arm_controller = ARSHXarm5Controller()
        self.arm_controller.start()

    def _sigint_handler(self, sig, frame):
        self.arm_controller.exit_threads = True

    def _sigterm_handler(self, sig, frame):
        self.arm_controller.exit_threads = True
        self.exit_code = 0

    def close_script(self):
        try:
            self.arm_controller.stop()
        except:
            pass


scripter = ScripterExt(log_source="run_arsh_xarm5_controller")
scripter.run()