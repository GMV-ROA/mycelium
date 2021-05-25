#!/usr/bin/env python3

import time
from gpiozero import AngularServo
from bh1745 import BH1745
import pigpio

class FilterContWheel:

    C_THRESHOLD_0 = 1000
    C_THRESHOLD_VAR_0 = 50

    def __init__(self, 
        servo_pin, 
        filter_count, 
        c_threshold=C_THRESHOLD_0, 
        c_threshold_var=C_THRESHOLD_VAR_0):

        # Init colour sensor and turn onboard LEDs on
        self.colour_sensor = BH1745()
        self.colour_sensor.setup()
        self.colour_sensor.set_leds(1)
        time.sleep(2)

        # Init servo and set to mid position
        self.servo = AngularServo(servo_pin)
        self.servo.mid()

        self.filter_count = int(filter_count)
        self.filter_id = 0
        self.c_threshold = int(c_threshold)
        self.c_threshold_var = int(c_threshold_var)

    def detect_c_threshold(self):
        self.rotate(0.4)
        start = time.time()
        c_range = []
        while time.time() < start + 10:
            r,g,b,c = self.get_rgbc_raw()
            c_range.append(c)

        self.c_threshold = max(c_range)-100
        self.rotate_to_next(-0.4) # Rotate back to previous notch
        return c_range
        # c_tolerance = 70 # Tolerance to fluctuation in c value
        # r0, g0, b0, c0 = self.colour_sensor.get_rgbc_raw() # Get initial c value
        # c_variance_max = 0
        # c_max = c0
        # c_min = c0

        # while True:
        #     r, g, b, c = self.colour_sensor.get_rgbc_raw()
        #     variance = abs(c - c0)
        #     if variance > c_tolerance:
        #         initial_notch = c < c0 # Initial position is not at notch
        #         if variance > c_variance_max:
        #             c_variance_max = variance
        #     if c_variance_max > 0 and variance < c_tolerance: # c has returned to original value
        #         break
        
        # if initial_notch:
        #     self.c_threshold = c0 

    def get_rgbc_raw(self):
        return self.colour_sensor.get_rgbc_raw()

    def is_notch_detected(self):
        r, g, b, c = self.get_rgbc_raw()
        return c >= self.c_threshold

    # Speed between -1 and 1
    def rotate(self, speed=0.5):
        self.servo.angle = speed*self.servo.max_angle
    
    def halt(self):
        self.servo.angle = 0

    # Speed between -1 and 1
    def rotate_to_next(self, speed=0.5):
        detected_initial = self.is_notch_detected()
        state_changed = False
        self.rotate(speed)
        
        while True:
            detected = self.is_notch_detected()
            if detected_initial and state_changed and detected or not detected_initial and detected:
                self.halt()
                break
            if detected_initial and not detected:
                state_changed = True

        self.filter_id = (self.filter_id+1)%self.filter_count

    def rotate_to_filter(self, fid, speed=0.5):
        if fid >= self.filter_count or fid < 0:
            return

        while self.filter_id != fid:
            self.rotate_to_next(speed)

class FilterPosWheel:

    filter_angles = [580, 1000, 1400, 1830, 2220] # Angles determined manually by eye

    def __init__(self, servo_pin):
        self.servo = pigpio.pi()
        self.servo_pin = servo_pin
        self.filter_count = len(self.filter_angles)
        self.filter_id = 0
        self.rotate_to_filter(self.filter_id)

    def rotate_to_filter(self, filter_id):
        if filter_id >= self.filter_count or filter_id < 0:
            raise Exception("Invalid filter id: %s" % str(filter_id))

        self.servo.set_servo_pulsewidth(self.servo_pin, self.filter_angles[filter_id])
        self.filter_id = filter_id

    def rotate_to_next(self):
        next_id = (self.filter_id+1)%self.filter_count
        self.rotate_to_filter(next_id)

    def rotate_to_prev(self):
        next_id = (self.filter_id-1)%self.filter_count
        self.rotate_to_filter(next_id)

    def stop(self):
        self.servo.stop()
