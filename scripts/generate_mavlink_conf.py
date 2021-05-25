#!/usr/bin/env python3

import sys
import os

from mycelium_utils import DefaultConfig, NetworkConfig

cfg = DefaultConfig()
ncfg = NetworkConfig()

def generate_conf():
    conf = """
# Mavlink Router configuration

[General]
MavlinkDialect=ardupilotmega
TcpServerPort=5760
DebugLogLevel=info
StatsFilePath=/tmp/cmavnode-links.txt

###################################
#       AutoPilot Endpoint        #
###################################
[UartEndpoint to_fc]
"""

    conf += "Device = "+cfg.ardupilot_device_port+"\n"
    conf += "Baud = "+str(cfg.connection_baudrate)+"\n"
    
    conf += """
###################################
#        Local Endpoints          #
###################################
[UdpEndpoint to_mavproxy]
Mode = Normal
Address = 127.0.0.1
Port = 14655
PortLock = 1

[UdpEndpoint to_dflogger]
Mode = Eavesdropping
Address = 127.0.0.1
Port = 14556

[UdpEndpoint to_MissionPlanner]
Mode = Normal
Address = 192.168.1.150
Port = 14567
"""

    endpoints = {
        'mavlink_msg_direct': cfg.mavlink_msg_direct,
        't265': cfg.t265_connection,
        'd435': cfg.d435_connection,
        'redis_to_ap': cfg.redis_to_ap,
        'ap_to_redis': cfg.ap_to_redis
    }

    # if ncfg.has_key('_picam_1') and ncfg.has_key('picam_1'):
    #     endpoints['picam_1'] = ncfg.picam_1+':'+ncfg._picam_1

    # if ncfg.has_key('_picam_2') and ncfg.has_key('picam_2'):
    #     endpoints['picam_2'] = ncfg.picam_2+':'+ncfg._picam_2

    for k, v in endpoints.items():
        conf += "\n"
        conf += "[UdpEndpoint to_"+k+"]\n"
        conf += "Mode = Normal\n"
        addr = v.split(':')
        conf += "Address = "+addr[0]+"\n"
        conf += "Port = "+addr[1]+"\n"

    return conf

try:
    conf = generate_conf()
    with open("main.conf", "w+") as f:
        f.write(conf)

except:
    raise