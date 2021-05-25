#!/usr/bin/env python3

# Set MAVLink protocol to 2.
import os
os.environ["MAVLINK20"] = "1"

import time
import threading
import traceback
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from mycelium.components import RedisBridge, Connector
from mycelium_utils import Scripter, utils, DefaultConfig

class RedisToAPScripterExt:

    instance = None
    i=0
    def __init__(self, connection, **kwargs):
        if not RedisToAPScripterExt.instance:
            RedisToAPScripterExt.instance = RedisToAPScripterExt.__RedisToAPScripterExt(connection,**kwargs)
        
    def __getattr__(self, name):
        return getattr(self.instance, name)

    class __RedisToAPScripterExt(Scripter):

        def __init__(self, connection, **kwargs):
            super().__init__(**kwargs)
            self.rb = RedisBridge(db=self.rd_cfg.databases['instruments'])
            self.keys = self.rd_cfg.generate_flat_keys('instruments')
            self.conn = connection
            self.lock = threading.Lock()
            default_msg_hz = 30.0
            msg_hz = {
                'send_vision_position_estimate': 30.0,
                'send_obstacle_distance': 15.0
            }

            self.mavlink_thread = threading.Thread(target=self.mavlink_loop, args=[self.conn])
            self.mavlink_thread.start()
            self.sched = BackgroundScheduler()
            logging.getLogger('apscheduler').setLevel(logging.ERROR)

            self.data = {}
            for k, v in self.keys.items():
                try:
                    if v in msg_hz.keys():
                        seconds = 1.0/msg_hz[v]
                    else:
                        seconds = 1.0/default_msg_hz
                    
                    func = getattr(self.conn, v)
                    self.sched.add_job(self.send_message, 
                        'interval', 
                        seconds=seconds, 
                        args=[func, k],
                        max_instances=1
                    )
                except:
                    utils.progress(traceback)
                else:
                    self.data[k] = None

        def run_main(self):
            self.sched.start()
            while not self.exit_threads:
                with self.lock:
                    for k, _ in self.keys.items():
                        self.data[k] = self.rb.get_key_by_string(k)
                    time.sleep(0.3)
                    
                # self.conn.send_heartbeat()
                # m = self.conn.get_callbacks(['HEARTBEAT'])
                # if m is None:
                #     continue
                # self.logger.log_debug("Received callback: %s" % m)
                # # utils.progress(m)

        def mavlink_loop(self, conn, callbacks=['HEARTBEAT']):
            while not self.exit_threads:
                self.conn.send_heartbeat()
                m = self.conn.get_callbacks(callbacks)
                if m is None:
                    continue
                self.logger.log_debug("Received callback: %s" % m)

        def send_message(self, func, key):
            while not self.exit_threads:
                with self.lock:
                    try:
                        value = self.data[key]
                        if value is not None:
                            func(*value)
                    except Exception as e:
                        self.logger.log_error("Could not send %s"%e)

        def close_script(self):
            try:
                self.sched.shutdown()
                self.mavlink_thread.join()
                self.conn.disconnect()
            except:
                pass


cfg = DefaultConfig()
conn = Connector(cfg.redis_to_ap, cfg.connection_baudrate, cfg.default_source_component, cfg.camera_source_component)
scripter = RedisToAPScripterExt(connection=conn, log_source="redis_to_ap")
scripter.run()
