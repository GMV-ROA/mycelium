#!/usr/bin/env python3

##########################################
##          EKF source switch           ##
##########################################

from mycelium.components import Base, Connector

class Switch(Base):

     def __init__(self, 
        connection_string=None, # Port set in mavproxy/mavlink to send MAVLINK messages
        connection_baudrate=None):
        super().__init__()
        self.connection_string = connection_string
        self.connection_baudrate = connection_baudrate

        if self.connection_string is None:
            self.connection_string = self.cfg.mavlink_msg_direct
        if self.connection_baudrate is None:
            self.connection_baudrate = self.cfg.connection_baudrate


class EKFSwitch(Switch):
    '''implements switching between GPS and non-GPS source, and fusing all sources
    '''
    EKF_GPS_ONLY = 1
    EKF_VICON_ONLY = 2
    EKF_FUSE_SOURCES = 3

    sources = [EKF_GPS_ONLY, EKF_VICON_ONLY, EKF_FUSE_SOURCES]

    rc_pwm = {
        EKF_GPS_ONLY: 1000,
        EKF_VICON_ONLY: 1500
    }

    def __init__(self, 
        connection_string=None, # Port set in mavproxy/mavlink to send MAVLINK messages
        connection_baudrate=None,
        rc_channel_id=None): # This is the rc channel for pwm input. https://github.com/ArduPilot/ardupilot/pull/14803
        super().__init__(connection_string, connection_baudrate)
        self.rc_channel_id = rc_channel_id

        if self.rc_channel_id is None:
            self.rc_channel_id = self.cfg.rc_channel_id

        self.rc_channel_id = int(self.rc_channel_id)

    def set_ekf_source(self, source, timeout=10):
        connector = Connector(self.connection_string, self.connection_baudrate, 1, 0)

        if source == self.EKF_FUSE_SOURCES:
            connector.set_param('EK3_SRC_OPTIONS', 1)
            self.logger.log_info("Set to fuse EKF sources")
            connector.disconnect()
            return

        pwm = self.rc_pwm[source]
        connector.set_param('EK3_SRC_OPTIONS', 0)        
        
        i = 0
        success = False
        while i < timeout:
            connector.set_rc_channel_pwm(self.rc_channel_id, pwm)
            connector.send_heartbeat()
            m = connector.get_callbacks(['RC_CHANNELS'], 3)
            if m is not None and m.chan9_raw == pwm:
                self.logger.log_debug("RC9 PWM set to %s" % str(pwm))
                self.logger.log_info("EKF source set")
                success = True
                break
            i += 1
        
        if not success:
            self.logger.log_debug("RC9 PWM not set or no response")
            self.logger.log_info("No response, source may not be set correctly")

        connector.disconnect()
    
class RelaySwitch(Switch):

    def __init__(self, 
        connection_string=None, # Port set in mavproxy/mavlink to send MAVLINK messages
        connection_baudrate=None,
        relay_pin=None): # This is the rc channel for pwm input. https://github.com/ArduPilot/ardupilot/pull/14803
        super().__init__(connection_string, connection_baudrate)
        self.relay_pin = relay_pin
        
        if self.relay_pin is None:
            self.relay_pin = self.cfg.relay_pin['led']

    def on(self):
        connector = Connector(self.connection_string, self.connection_baudrate, 1, 0)
        connector.set_relay(self.relay_pin, True)
        connector.disconnect()
        
    def off(self):
        connector = Connector(self.connection_string, self.connection_baudrate, 1, 0)
        connector.set_relay(self.relay_pin, False)
        connector.disconnect()

    
class InitialModeSwitch(Switch):

    MANUAL = 0
    HOLD = 4
    LOITER = 5
    AUTO = 10

    modes = [MANUAL, HOLD, LOITER, AUTO]

    def __init__(self, 
        connection_string=None, # Port set in mavproxy/mavlink to send MAVLINK messages
        connection_baudrate=None): # This is the rc channel for pwm input. https://github.com/ArduPilot/ardupilot/pull/14803
        super().__init__(connection_string, connection_baudrate)

    def set_mode(self, mode):
        if mode not in self.modes:
            raise Exception("Invalid mission mode")

        connector = Connector(self.connection_string, self.connection_baudrate, 1, 0)
        connector.set_param('INITIAL_MODE', mode)
        connector.disconnect()
        