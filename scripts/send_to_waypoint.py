#!/usr/bin/env python3

import signal
import traceback
import sys
import argparse

from mycelium.components import DronekitConnector, DefaultConfig, Logger

#######################################
# Setup
#######################################

logger = Logger()
cfg = DefaultConfig()

parser = argparse.ArgumentParser(description='Sets next waypoint')
parser.add_argument('--connection',
                    help="Dronekit connection string")      
parser.add_argument('--wp',
                    help="Send waypoint")               

args = parser.parse_args()
connection = args.connection
wp = args.wp

if wp is None:
    wp = 0

if connection is None:
    conn_string = cfg.mavlink_msg_external
else:
    conn_string = connection

logger.log_info("Connecting to %s" % conn_string)
connector = DronekitConnector(conn_string)
logger.log_info("Connected")

exit_threads = False
exit_code = 1

def _sigint_handler(sig, frame):
    global exit_threads
    exit_threads = True

def _sigterm_handler(sig, frame):
    global exit_threads, exit_code
    exit_threads = True
    exit_code = 0


#######################################
# Main code
#######################################

signal.signal(signal.SIGINT, _sigint_handler)
signal.signal(signal.SIGTERM, _sigterm_handler)

logger.log_info("Sending to waypoint")
try:    
    connector.fetch_mission()
    connection.mission.next(wp)

except:
    logger.log_crit(traceback.format_exc())

finally:
    logger.log_info("Closing send_to_waypoint script")
    try:
        connector.disconnect()
    except:
        pass

    # start a timer in case stopping everything nicely doesn't work.
    signal.setitimer(signal.ITIMER_REAL, 5)  # seconds...
    sys.exit(exit_code)