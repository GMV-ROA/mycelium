#!/usr/bin/env python3

from .utils import progress
import logging
import os
import datetime
import traceback

class Logger:

    CRITICAL = logging.CRITICAL     # 50
    ERROR = logging.ERROR           # 40
    WARNING = logging.WARNING       # 30
    INFO = logging.INFO             # 20
    DEBUG = logging.DEBUG           # 10
    NOTSET = logging.NOTSET         # 0

    levels = {
        CRITICAL: 'CRITICAL',
        ERROR: 'ERROR',
        WARNING: 'WARNING',
        INFO: 'INFO',
        DEBUG: 'DEBUG',
        NOTSET: 'NOT SET'
    }

    def __init__(self, log_dir=None, level=INFO, sysout_level=DEBUG, source=None, logger_name='mycelium'):
        self.sysout_level = sysout_level
        filename = self._setup_log_file(log_dir)
        if source is None:
            source = 'na'

        self.logger = logging.getLogger(logger_name)
        handler = logging.FileHandler(filename)
        handler.setLevel(level)
        formatter = logging.Formatter('[%(asctime)s] - [%(source)s] - [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.source = source
        self.extra = {'source': source}

    def _setup_log_file(self, log_dir=None):
        datestamp = datetime.datetime.now().strftime("%Y_%m_%d")
        try:
            if log_dir is None:
                dir_path = os.environ['MYCELIUM_ROOT']
                log_dir = dir_path + "/logs/"
            
            if not os.path.exists(log_dir):
                progress("Creating log directory: %s" % log_dir)
                os.makedirs(log_dir)

            return log_dir + datestamp + ".log"
        except:
            progress(traceback.format_exc())
            return datestamp + ".log"

    def log(self, msg, level=INFO):
        if level >= self.sysout_level:
            arr = ["["+self.levels[level]+"]", "["+self.source+"]", msg]
            progress(" - ".join(arr))

        self.logger.log(level, msg, extra=self.extra)

    def log_info(self, msg):
        self.log(msg, self.INFO)

    def log_error(self, msg):
        self.log(msg, self.ERROR)

    def log_warn(self, msg):
        self.log(msg, self.WARNING)

    def log_debug(self, msg):
        self.log(msg, self.DEBUG)

    def log_crit(self, msg):
        self.log(msg, self.CRITICAL)