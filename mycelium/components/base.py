#!/usr/bin/env python3

from mycelium.components import Logger, DefaultConfig, RedisConfig

class Base:

    def __init__(self):
        self.cfg = DefaultConfig()
        self.rd_cfg = RedisConfig()

        if self.cfg.has_key('log_dir'):
            log_dir = self.cfg.log_dir
        else:
            log_dir = None
            
        self.logger = Logger(log_dir, level=int(self.cfg.log_level), sysout_level=int(self.cfg.sysout_level))
        