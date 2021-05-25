#!/usr/bin/env python3

import time
import sys
import signal
import threading

from picam_lib import PicamImpl

#### Setup

print("Starting camera, connecting robot")
camera = PicamImpl(PicamImpl.RAW_BAYER)
subdir = "swc_" % int(time.time())
camera.set_save_directory(subdir)
print("Startup complete")

#### Functions

exit_all_loops = False
exit_code = 1

def _sigint_handler(sig, frame):
    global exit_all_loops
    exit_all_loops = True

def _sigterm_handler(sig, frame):
    global exit_all_loops, exit_code
    exit_all_loops = True
    exit_code = 0

signal.signal(signal.SIGINT, _sigint_handler)
signal.signal(signal.SIGTERM, _sigterm_handler)

CONTINUOUS = 1
BURST = 2
capture = CONTINUOUS
burst_duration = 2

def user_input_monitor():
    global capture, exit_all_loops
    while not exit_all_loops:
        try:
            c = input()
            if c == str(CONTINUOUS):
                print("Capture continuous")
                capture = int(c)
            elif c == str(BURST):
                print("Capture burst")
                capture = int(c)
            elif c == "0":
                print("Exiting")
                exit_all_loops = True
            else:
                print("Got keyboard input %s" % c)
        except IOError: pass

#### Start capture

user_keyboard_input_thread = threading.Thread(target=user_input_monitor)
user_keyboard_input_thread.daemon = True
user_keyboard_input_thread.start()

print("Start mission capture")
try:
    while True:
        if exit_all_loops:
            break
        try:
            if capture == CONTINUOUS:
                camera.capture_single()
            elif capture == BURST:
                print("Start burst capture")
                camera.capture_burst(burst_duration)
                capture = CONTINUOUS
                print("End burst capture")
        except Exception as e:
            print(e)

except Exception as e:
    print(e)

finally:
    print("Closing script...")
    exit_all_loops = True
    signal.setitimer(signal.ITIMER_REAL, 5)
    user_keyboard_input_thread.join()
    sys.exit(exit_code)
