#!/usr/bin/env python3

import signal
import traceback
import sys
import argparse

from . import Logger, DefaultConfig, RedisConfig, NetworkConfig

class Scripter:

    def __init__(self, 
        log_dir=None, 
        log_level=Logger.INFO, 
        log_sysout_level=Logger.DEBUG,
        log_source=None, 
        **kwargs):

        print("CALLING HERE")

        self.logger = Logger(log_dir=log_dir, level=log_level, sysout_level=log_sysout_level, source=log_source)        
        self.cfg = DefaultConfig(**kwargs)
        self.rd_cfg = RedisConfig()
        self.n_cfg = NetworkConfig()
        
        self.exit_threads = False
        self.exit_code = 1        
        signal.signal(signal.SIGINT, self._sigint_handler)
        signal.signal(signal.SIGTERM, self._sigterm_handler)

    def init_arg_parser(self, description='', args={}):
        self.parser = argparse.ArgumentParser(description=description)
        try:
            args = args.items()
        except (AttributeError, TypeError):
            pass
        else:
            for arg, desc in args:
                self.parser.add_argument(arg, help=desc)

    def get_args(self):
        return self.parser.parse_args()

    def _sigint_handler(self, sig, frame):
        self.exit_threads = True

    def _sigterm_handler(self, sig, frame):
        self.exit_threads = True
        self.exit_code = 0

    def run(self, **kwargs):
        try:
            self.logger.log_info("Running script")
            self.run_main(**kwargs)
        except:
            self.logger.log_crit(traceback.format_exc())
        finally:
            self.logger.log_info("Closing script")
            self.close_script()
            signal.setitimer(signal.ITIMER_REAL, 5)  # seconds...
            sys.exit(self.exit_code)
    
    def run_main(self):
        raise NotImplementedError

    def close_script(self):
        raise NotImplementedError