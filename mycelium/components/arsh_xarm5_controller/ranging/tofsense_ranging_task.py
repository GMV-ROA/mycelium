

import threading
import time
from tofsense_laser_range_finder import TOFSenseLaserRangeFinder
from mycelium.components import RedisBridge

class RangingTask(threading.Thread):
    
    def __init__(self, ranging_port, ranging_baudrate, sample_frequency = 10, wakeup_frequency=20):
        threading.Thread.__init__(self)

        self.sample_period = 1/sample_frequency
        self.wakeup_period = 1/wakeup_frequency

        self.condition = threading.Condition()
        self.done = False
        self.capture_trigger = False

        self.tof_sensor = TOFSenseLaserRangeFinder(ranging_port, ranging_baudrate)

        self.start()


    def run(self):

        while not self.done:
            self.condition.acquire()
            self.condition.wait(0.0)
            trigger = self.capture_trigger
            self.condition.release()

            if(trigger):
                timing_result = self.tof_sensor.get_distance_data()
                print("TOF RESULT: %s" % str(timing_result))
                time.sleep(self.sample_period)
            else:
                print("waiting to start ranging.......")
                time.sleep(self.wakeup_period)


    def stop(self):
        self.done = True
        self.capture_trigger = False


    def update_state(self, capture_trigger):
        self.condition.acquire()
        self.capture_trigger = capture_trigger
        self.condition.notify()
        self.condition.release()


if __name__ == "__main__":
    try:

        test_task = RangingTask('/dev/ttyUSB0', 115200, 10, 5)
        time.sleep(10)
        test_task.update_state(True)
        time.sleep(10)
        test_task.update_state(False)
        test_task.stop()
        
    except Exception as e:
        print("Exception: %s" % e)