

import threading
import time

from .tofsense_laser_range_finder import TOFSenseLaserRangeFinder
from mycelium.components import RedisBridge

class TOFSenseRangingTask(threading.Thread):
    
    def __init__(self, rb_i, sensor_name, ranging_port, ranging_baudrate, sample_frequency = 10, wakeup_frequency=20, expiry=1, default_active=False):
        threading.Thread.__init__(self)

        self.rb = rb_i
        self.sensor_name = sensor_name
        self.expiry = expiry
        self.sample_period = 1/sample_frequency
        self.wakeup_period = 1/wakeup_frequency
        

        self.condition = threading.Condition()
        self.done = False
        self.capture_trigger = False

        self.tof_sensor = TOFSenseLaserRangeFinder(ranging_port, ranging_baudrate)

        self.start()
        self.update_active(default_active)


    def run(self):

        while not self.done:
            self.condition.acquire()
            self.condition.wait(0.0)
            trigger = self.capture_trigger
            self.condition.release()

            if(trigger):
                timing_result = self.tof_sensor.get_distance_data()
                self.rb.add_key(timing_result, 'tofsense_range', self.sensor_name, 'range_data', expiry=self.expiry)
                time.sleep(self.sample_period)
            else:
                time.sleep(self.wakeup_period)


    def stop(self):
        self.done = True
        self.capture_trigger = False
        self._update_active_key(False)


    def update_active(self, capture_trigger):
        self.condition.acquire()
        self.capture_trigger = capture_trigger
        self.condition.notify()
        self.condition.release()
        self._update_active_key(capture_trigger)


    def _update_active_key(self, trigger_value):
        active_status = 'active' if trigger_value else 'inactive'
        self.rb.add_key(active_status, 'tofsense_range', self.sensor_name, 'state')


# TODO: fix this!
if __name__ == "__main__":
    try:

        # self.rb_i = RedisBridge(db=self.rd_cfg.databases['instruments'])
        test_task = TOFSenseRangingTask('/dev/ttyUSB0', 115200, 10, 5)
        time.sleep(10)
        test_task.update_active(True)
        time.sleep(10)
        test_task.update_active(False)
        test_task.stop()
        
    except Exception as e:
        print("Exception: %s" % e)