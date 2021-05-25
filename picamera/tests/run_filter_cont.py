from picam_lib import FilterContWheel, PicamImpl
from mycelium_utils import Scripter
from mycelium_utils.utils import progress

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()
        args_ = {}
        
        if args.pin is None:
            raise Exception("Servo pin required")
        else:
            args_['servo_pin'] = args.pin

        if args.filters is None:
            raise Exception("Filter count required")
        else:
            args_['filter_count'] = args.filters

        if args.c_thresh:
            args_['c_threshold'] = args.c_thresh
        # else:
        #     args_['c_threshold'] = 1000

        if args.c_thresh_var:
            args_['c_threshold_var'] = args.c_thresh_var
        # else:
        #     args_['c_threshold'] = 50

        fcw = FilterContWheel(**args_)
        if args.speed:
            speed = args.speed
        else:
            speed = 0.5

        camera = PicamImpl()
        camera.set_save_directory('tests', 'filter_cont')

        while not self.exit_threads:
            progress("====================================\n\
n: rotate to next filter\n\
r: rotate at current set speed\n\
s: stop rotation\n\
w: increase speed (max 1)\n\
q: decrease speed (min -1)\n\
d: check if notch is detected\n\
c: calibrate c threshold\n\
a: capture image\n\
e: exit\n\
filter id, >0 : rotate to filter no.\n\
====================================\n\
            ")
            try:
                c = input()
                if c == "n":
                    self.logger.log_info("Rotate to next filter...")
                    fcw.rotate_to_next(speed)
                    self.logger.log_info("Filter reached: %d" % fcw.filter_id)
                elif c == "r":
                    self.logger.log_info("Rotate at speed %f" % speed)
                    fcw.rotate(speed)
                elif c == "s":
                    fcw.halt()
                    self.logger.log_info("Rotation stopped")
                elif c == "w":
                    if speed < 1.0:
                        speed += 0.1
                    self.logger.log_info("Speed set to %f" % speed)
                elif c == "q":
                    if speed > -1.0:
                        speed -= 0.1
                    self.logger.log_info("Speed set to %f" % speed)
                elif c == "d":
                    self.logger.log_info("Check notch detected...")
                    detected = str(fcw.is_notch_detected())
                    self.logger.log_info("Notch detected: %s" % detected)
                elif c == "c":
                    self.logger.log_info("Calibrating c threshold...")
                    a=fcw.detect_c_threshold()
                    self.logger.log_info("C threshold found: %d" % fcw.c_threshold)
                    self.logger.log_info("C threshold found: %s" % str(a))
                elif c == "a":
                    self.logger.log_info("Capturing image...")
                    camera.capture_single()
                elif c == "e":
                    self.logger.log_info("Exiting...")
                    break
                else:
                    try:
                        fid = int(c)
                    except:
                        self.logger.log_info("Got keyboard input %s" % c)
                    else:
                        self.logger.log_info("Rotate to filter %d..." % fid)
                        fcw.rotate_to_filter(fid)
                        self.logger.log_info("Filter reached: %d" % fcw.filter_id)

            except Exception as e:
                self.logger.log_debug(e)

    def close_script(self):
        return

args = {
    '--pin': 'servo pin',
    '--filters': 'number of filters',
    '--c_thresh': "c threshold",
    '--c_thresh_var': "c threshold var",
    '--speed': 'servo speed'
}
scripter = ScripterExt(log_source="picamera/run_filter_cont")
scripter.init_arg_parser('Test: run filter with positional servo', args)
scripter.run()