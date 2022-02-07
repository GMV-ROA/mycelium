#!/usr/bin/env python3

import os

from mycelium.components import Logger, DefaultConfig, RedisConfig, NetworkConfig

class Base:

    def __init__(self):
        self.cfg = DefaultConfig()
        self.rd_cfg = RedisConfig()

        if self.cfg.has_key('log_dir'):
            log_dir = self.cfg.log_dir
        else:
            log_dir = None
            
        self.logger = Logger(log_dir, level=int(self.cfg.log_level), sysout_level=int(self.cfg.sysout_level))
        

    def get_redis_connection(self):

        host = self.cfg.network['default_redis_host']
        port = self.cfg.network['default_redis_port']

        if "REDIS_HOST_IP" in os.environ:
            host = os.environ['REDIS_HOST_IP']
            self.logger.log_info(f"Using User-Defined Redis Host IP: {host}")
        else:
            self.logger.log_info(f"Using Default Redis Host IP: {host}")

        if "REDIS_HOST_PORT" in os.environ:
            port = os.environ['REDIS_HOST_PORT']
            self.logger.log_info(f"Using User-Defined Redis Host Port: {port}")
        else:
            self.logger.log_info(f"Using Default Redis Host Port: {port}")

        return (host,port)

