from collections.abc import Callable

import logging
import traceback
import functools


class Logger(logging.Logger):

    def __init__(self, log_path: str, is_debug: str, name: str, level: int = logging.NOTSET):
        logging.Logger.__init__(self, name, level=logging.DEBUG)

        self.callback = None

        formatter = logging.Formatter(u'%(levelname)s  %(asctime)s   [ %(name)s ] %(message)s')

        self.sh = logging.StreamHandler()
        self.sh.setFormatter(formatter)

        if is_debug: self.sh.setLevel(logging.DEBUG)
        else:        self.sh.setLevel(logging.INFO)

        self.addHandler(self.sh)

        # \TODO: Maybe break up the logging file if it goes over 1MB
        #   get file size
        #   if over 1MB, then rename current logging file to '{start_date}_{end_date}_{logger_name}.log'
        #   cut-paste into logging folder named '{logger_name}'

        self.fh = logging.FileHandler(f'{log_path}/{name}.log', encoding='utf-8')
        self.fh.setFormatter(formatter)
        self.fh.setLevel(logging.INFO)
        self.addHandler(self.fh)


    def __del__(self):
        self.sh.close(); self.removeHandler(self.sh)
        self.fh.close(); self.removeHandler(self.fh)


    def set_report_callback(self, callback: Callable):
        self.callback = callback


    # \FIXME: https://osu.ppy.sh/forum/t/772528 <- this thread's title has characters which break logger encoding; Error report: https://i.imgur.com/pFmcQvB.png
    '''
    def error(self, msg):
        msg = msg.strip()
        if msg == 'None' or msg == 'N/A' or len(msg) == 0:
            self.exception(msg)
        else:
            self.error(msg)


    def critical(self, msg):
        msg = msg.strip()
        if msg == 'None' or msg == 'N/A' or len(msg) == 0:
            self.exception(msg)
        else:
            self.critical(msg)
    '''


    def exception(self, msg):
        msg = msg.strip()
        msg += '\n' + traceback.format_exc()
        self.critical(msg)


def LoggerClass(log_path, is_debug):

    class LoggerClassFull(Logger):
        __init__ = functools.partialmethod(Logger.__init__, log_path, is_debug)

    return LoggerClassFull
