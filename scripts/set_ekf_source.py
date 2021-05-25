import argparse
from mycelium import EKFSwitch
from mycelium.components import Logger
import traceback
import sys

logger = Logger()
parser = argparse.ArgumentParser(description='Sets EKF source')
parser.add_argument('--source',
                    help="Set to EKF source.\n1 - GPS only\n2 - Vicon only\n3 - Fuse sources")

args = parser.parse_args()
source = args.source
if source is None:
    logger.log_error("EKF source not valid")
    sys.exit()

source = int(source)
if source not in EKFSwitch.sources:
    logger.log_error("EKF source not valid")
    sys.exit()

logger.log_info("Setting to EKF source: %s" % source)

try:
    switch = EKFSwitch()
    switch.set_ekf_source(source)

except:
    logger.log_crit(traceback.format_exc())

finally:
    logger.log_info("Closing script")