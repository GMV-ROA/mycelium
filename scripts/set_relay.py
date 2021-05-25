import argparse
from mycelium import RelaySwitch
from mycelium.components import Logger
import traceback
import sys

logger = Logger()
parser = argparse.ArgumentParser(description='Sets relay pin')
parser.add_argument('--pin',
                    help="Set relay pin.")
parser.add_argument('--state',
                    help="Set state.")

args = parser.parse_args()
pin = args.pin
state = args.state
if pin is None or state is None:
    logger.log_error("Pin and state arguments must be valid")
    sys.exit()

logger.log_info("Setting pin %s to state %s" % (pin, state))

pin = int(pin)
state = bool(state)

try:
    switch = RelaySwitch(relay_pin=pin)
    if state:
        switch.on()
    else:
        switch.off()

except:
    logger.log_crit(traceback.format_exc())

finally:
    logger.log_info("Closing relay script")