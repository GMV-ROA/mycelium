import argparse
from mycelium import InitialModeSwitch
from mycelium.components import Logger
import traceback
import sys

logger = Logger()
parser = argparse.ArgumentParser(description='Sets mode')
parser.add_argument('--mode',
                    help="Set mode.")

args = parser.parse_args()
mode = args.mode
if mode is None:
    logger.log_error("Pin and state arguments must be valid")
    sys.exit()

logger.log_info("Setting mode to %s" % mode)

mode = int(mode)

try:
    switch = InitialModeSwitch()
    switch.set_mode(mode)

except:
    logger.log_crit(traceback.format_exc())

finally:
    logger.log_info("Closing mode script")