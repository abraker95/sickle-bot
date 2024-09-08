import sys

if sys.version_info < (3, 10):
    print('Python 3.10 or later is required!')
    sys.exit(1)

import traceback
import time
import os

import pathlib
import logging

import yaml

from core.Logger import LoggerClass
from core.DiscordBot import DiscordBot


excepthook_old = sys.excepthook
def exception_hook(exctype, value, tb):
    #excepthook_old(exctype, value, tb)

    trace = ''.join(traceback.format_exception(exctype, value, tb))
    logging.getLogger('DiscordBot').exception(trace)
    sys.exit(1)
sys.excepthook = exception_hook


if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    root = os.path.abspath(os.getcwd())
    log_path = config['Core']['log_path'] = pathlib.Path(f'{root}/{config["Core"]["log_path"]}')

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    logging.setLoggerClass(LoggerClass(log_path, config['Core']['is_debug']))

    discord_bot = DiscordBot()

    while not discord_bot.is_closed():
        try: time.sleep(0.2)
        except KeyboardInterrupt:
            discord_bot.quit = True
