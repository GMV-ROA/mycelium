from picam_lib import FilterPosWheel, PicamImpl
from mycelium_utils import Scripter
from mycelium_utils.utils import progress

class ScripterExt(Scripter):

    def run_main(self):
        args = self.get_args()         
        args_ = {}

        if args.pin is None:
            raise Exception("Servo pin required")
        else:
            try:
                args_['servo_pin'] = int(args.pin)
            except:
                raise Exception("Valid servo pin required")

        self.fpw = FilterPosWheel(**args_)

        camera = PicamImpl()
        camera.set_save_directory('tests', 'filter_pos')

        while not self.exit_threads:
            progress("\
n: rotate to next filter\n\
p: rotate to previous filter\n\
a: capture image\n\
e: exit\n\
filter id, >0 : rotate to filter no.\n\
            ")
            try:
                c = input()
                if c == "n":
                    self.logger.log_info("Rotate to next filter...")
                    self.fpw.rotate_to_next()
                    self.logger.log_info("Filter reached: %d" % self.fpw.filter_id)
                elif c == "p":
                    self.logger.log_info("Rotate to previous filter...")
                    self.fpw.rotate_to_prev()
                    self.logger.log_info("Filter reached: %d" % self.fpw.filter_id)
                elif c == "e":
                    self.logger.log_info("Exiting...")
                    break
                elif c == "a":
                    self.logger.log_info("Capturing image...")
                    camera.capture_single()
                else:
                    try:
                        fid = int(c)
                        self.logger.log_info("Rotate to filter %d..." % fid)
                        self.fpw.rotate_to_filter(fid)
                        self.logger.log_info("Filter reached: %d" % self.fpw.filter_id)
                    except:
                        self.logger.log_info("Got keyboard input %s" % c)

            except Exception as e:
                self.logger.log_debug(e)

    def close_script(self):
        self.fpw.stop()

args = {
    '--pin': 'servo pin'
}
scripter = ScripterExt(log_source="picamera/run_filter_pos")
scripter.init_arg_parser('Test: run filter with positional servo', args)
scripter.run()