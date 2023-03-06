import sys

if sys.version_info < (3, 8):
    print('Python 3.8 or later is required!')
    sys.exit(1)

import traceback

from main.DiscordBot import DiscordBot
from main.FeedServer import FeedServer

import logging
from main.Logger import Logger


logging.setLoggerClass(Logger)


excepthook_old = sys.excepthook
def exception_hook(exctype, value, tb):
    #excepthook_old(exctype, value, tb)
    
    trace = ''.join(traceback.format_exception(exctype, value, tb))
    logging.getLogger('DiscordBot').exception(trace)
    sys.exit(1)
sys.excepthook = exception_hook


if __name__ == '__main__':
    discord_bot = DiscordBot()
    FeedServer.init(discord_bot.queue_data)
