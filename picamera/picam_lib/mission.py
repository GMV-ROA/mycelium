#!/usr/bin/env python3

import time
import threading
import csv
import os
from picam_lib import PicamImpl, FilterContWheel, FilterPosWheel
from mycelium_utils import DronekitConnector


# MANUAL indicates mission has not started or has finished
# HOLD indicates robot is stationary or mission is paused
# AUTO indicates robot is moving to next waypoint
class FilterMissionExec:

    def __init__(self, filter_servo_pin, filter_wheel_count, connection_string):
        self.vehicle = DronekitConnector(connection_string)
        self.camera = PicamImpl()
        self.filter = FilterContWheel(filter_servo_pin, filter_wheel_count)
        self.filter.detect_c_threshold()
        
        self.mode = None
        self.wp = None
        self.capture = False
        self.filter_capture = False
        self.close_mission = False
        self.mission_complete = False
        self.threads = {}
        self._init_threads()
        

    def _init_threads(self):
        self.threads['check_state_t'] = threading.Thread(target=self._check_state_thread)
        self.threads['capture_t'] = threading.Thread(target=self._capture_thread)        
        self.threads['check_state_t'].start()

    def start(self):
        self.threads['capture_t'].start()

    def stop(self):
        self.close_mission = True
        time.sleep(2)
        for t in self.threads:
            try:
                t.join()
            except:
                pass
    
        self.vehicle.disconnect()
        self.camera.disconnect()

    def is_mission_complete(self):
        return self.mission_complete

    def _check_state_thread(self):
        while not self.close_mission:
            self.mode = self.vehicle.get_mode()
            # Camera will capture frames when mission has started and mode is not manual
            if self.mode == 'MANUAL':
                self.capture = False
            else:
                self.capture = True

            new_wp = self.vehicle.mission.next
            if new_wp != self.wp:
                # Trigger filter capture at waypoint
                self.filter_capture = True
                self.wp = new_wp
            
            if self.wp == self.vehicle.mission.count and self.mode == 'MANUAL':
                self.mission_complete = True

    def _capture_thread(self):
        while not self.close_mission:
            try:
                if self.filter_capture:
                    self._process_filters()
                    self.filter_capture = False

                if self.capture:
                    self.camera.capture_single()
            except:
                pass

    def _process_filters(self):
        for i in range(self.filter.filter_count):
            self.filter.rotate_to_next(0.5)
            self.camera.capture_single("f%d"%i)


# Captures images when waypoint reached
# AUTO to trigger start
# MANUAL to trigger mission end
class WaypointMissionExec:

    NO_FILTER = 0
    CONT_FILTER = 1
    POS_FILTER = 2

    def __init__(self, 
        connection_string, 
        filter_servo_pin=None,
        filter_count=None,
        mode=NO_FILTER, 
        capture_time=2,
        **kwargs):
        
        self.vehicle = DronekitConnector(connection_string)
        self.vehicle.get_mission(update=True)
        self.camera = PicamImpl()
        self.capture_time = capture_time

        self.mode = None
        self.mission_started = False
        self.wp = None
        self.waypoint_capture = False
        self.close_mission = False
        self.threads = {}
        self._init_threads()

        if mode == self.CONT_FILTER:
            self.filter = FilterContWheel(filter_servo_pin, filter_count, **kwargs)
        elif mode == self.POS_FILTER:
            self.filter = FilterPosWheel(filter_servo_pin)
        else:
            self.filter = None
        

    def _init_threads(self):
        self.threads['check_state_t'] = threading.Thread(target=self._check_state_thread)
        self.threads['capture_t'] = threading.Thread(target=self._capture_thread)        
        self.threads['check_state_t'].start()

    def start(self):
        self.threads['capture_t'].start()

    def stop(self):
        self.close_mission = True
        time.sleep(2)
        for t in self.threads:
            try:
                t.join()
            except:
                pass
    
        self.vehicle.disconnect()
        self.camera.disconnect()

    def is_mission_complete(self):
        return self.close_mission

    def _check_state_thread(self):
        while not self.close_mission:
            self.mode = self.vehicle.get_mode()
            # Camera will capture frames when mission has started and mode is not manual
            if self.mode == 'AUTO':
                self.mission_started = True
            elif self.mission_started:
                continue # Mission is started but robot is not in AUTO mode

            new_wp = self.vehicle.mission.next
            if new_wp != self.wp:
                # Trigger filter capture at waypoint
                self.waypoint_capture = True
                self.wp = new_wp
            
            if self.wp == self.vehicle.mission.count and self.mode == 'MANUAL':
                self.close_mission = True

    def _capture_thread(self):
        filename = self.camera.save_dir + 'waypoint_mission.csv'
        file_exists = os.path.exists(filename)
        with open(filename, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = ['image_timestamp', 'gps_lat', 'gps_lon', 'gps_fix_type']
                csvwriter.writerow(header)

            while not self.close_mission:
                try:
                    if self.waypoint_capture:
                        if self.mode == self.NO_FILTER:
                            images = self._capture_no_filter()
                        else:
                            images = self._process_filters()
                        
                        csvwriter.writerow(images)
                        self.waypoint_capture = False
                except:
                    pass

    def _capture_no_filter(self):
        images = []
        start = time.time()
        while time.time() < start + self.capture_time:
            filename = self.camera.capture_single()
            images.append([filename]+self.vehicle.get_gps())
        
        return images

    def _process_filters(self):
        images = []
        for i in range(self.filter.filter_count):
            self.filter.rotate_to_next(0.5)
            filename = self.camera.capture_single("f%d"%i)
            images.append([filename]+self.vehicle.get_gps())
        
        return images

# Manual trigger of camera capture running through all filters for positional servo filter
class FilterCapture:

    def __init__(self,
        filter_servo_pin,
        connection_string=None,
        connect_robot=False):
        
        self.camera = PicamImpl()
        self.close_mission = False
        self.filter = FilterPosWheel(filter_servo_pin)
        
        if connect_robot and connection_string is not None:
            try:
                self.vehicle = DronekitConnector(connection_string)
            except:
                self.vehicle = None
        else:
            self.vehicle = None
        
    def run_once_gps_log(self):
        filename = self.camera.save_dir + 'waypoint_mission.csv'
        file_exists = os.path.exists(filename)
        with open(filename, 'a+', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',')
            if not file_exists:
                header = ['image_timestamp', 'gps_lat', 'gps_lon', 'gps_fix_type']
                csvwriter.writerow(header)

            while not self.close_mission:
                filters = len(self.filter.filter_angles)
                try:
                    for _ in range(filters):
                        images = self._process_filters()                    
                        csvwriter.writerow(images)
                except:
                    pass

    def run_once(self):
        filters = len(self.filter.filter_angles)
        for i in range(filters):
            self.camera.capture_single("f%d"%i)
            self.filter.rotate_to_next()
        
    def _process_filters(self):
        images = []
        for i in range(self.filter.filter_count):
            filename = self.camera.capture_single("f%d"%i)
            if self.vehicle:
                gps_data = self.vehicle.get_gps()
            else:
                gps_data = []
            
            images.append([filename]+gps_data)
            self.filter.rotate_to_next()

        return images

    def stop(self):
        self.camera.disconnect()
        self.filter.stop()
        self.vehicle.disconnect()


