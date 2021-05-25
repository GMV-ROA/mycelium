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

from pymavlink import mavutil

cfg = DefaultConfig()
conn = mavutil.mavlink_connection(
    cfg.redis_to_ap,
    autoreconnect = True,
    source_system = 1,
    source_component = 93,
    baud=cfg.connection_baudrate,
    force_connected=True
)

sched = BackgroundScheduler()
logging.getLogger('apscheduler').setLevel(logging.ERROR)

sched.add_job(self.send_message, 
    'interval', 
    seconds=seconds, 
    args=[func, k],
    max_instances=1
)

def send_message(self, func, key):
    global conn
    try:
        value = [1616760391372787,0.0004967392887920141,0.0021482815500348806,-0.0015257337363436818,0.009654812127502384,0.0433527477725285,-0.0010235925618208314,[0.1,0,0,0,0,0,0.1,0,0,0,0,0.1,0,0,0,0.001,0,0,0.001,0,0.001],1]
        if value is not None:
            conn.mav.vision_position_estimate_send(value)
    except Exception as e:
        pass

