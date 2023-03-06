from tinydb.middlewares import Middleware
import threading

from main.Logger import Logger


class DbThreadSafeMiddleware(Middleware):
    """
    Adds lock to perform thread safe operations
    """

    def __init__(self, storage_cls):
        Middleware.__init__(self, storage_cls)

        self.__logger = Logger(__class__.__name__)
        self.__lock   = threading.Lock()


    def read(self):
        with self.__lock:
            return self.storage.read()


    def write(self, data):
        #self.__logger.debug(f'db req: {id(data)}')
        with self.__lock:
            #self.__logger.debug(f'db write: {id(data)}')
            self.storage.write(data)


    def close(self):
        with self.__lock:
            self.storage.close()
