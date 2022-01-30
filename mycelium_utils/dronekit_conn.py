#!/usr/bin/env python3

import time
import dronekit

class DronekitConnector:

    def __init__(self, 
        connection_string,
        connection_baudrate=921600,
        timeout=30,
        source_system=1,
        source_component=0):

        self.conn = dronekit.connect(ip=connection_string,
            baud=connection_baudrate,
            timeout=timeout, 
            source_system=source_system,
            source_component=source_component)
        self.mission = None

    def arm(self, timeout=10):
        i = 0
        while not self.conn.is_armable and i < timeout:
            i += 1
            time.sleep(1)
        
        self.set_mode('GUIDED')
        self.conn.arm()

    def disarm(self, timeout=10):
        self.conn.disarm(timeout=timeout)

    def set_mode(self, mode):
        self.conn.mode = dronekit.VehicleMode(mode)
        time.sleep(1)
        return self.conn.mode.name

    def get_mode(self):
        return self.conn.mode.name

    def reboot(self):
        self.reboot()
        # check if rebooted

    def get_mission(self, update=False):            
        if update:
            self.mission = self.conn.commands
            self.mission.download()
            self.mission.wait_ready()

        return self.mission

    def fetch_mission(self):
        return self.get_mission(update=True)

    def send_to_waypoint(self, waypoint):
        if self.mission is None:
            self.fetch_mission()

        # check if waypoint is valid

        self.mission.next(waypoint)

    def get_gps(self):
        gps = self.conn.location.global_frame
        if gps:
            return [gps.lat, gps.lon, gps.fix_type]
        return [None, None, None]

    def get_attitude(self):
        attitude = self.conn.attitude
        if attitude:
            return [attitude.roll, attitude.pitch, attitude.yaw]
        return [None, None, None]

    def disconnect(self):
        self.conn.close()

