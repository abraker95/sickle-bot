from typing import Callable

import warnings
import zmq


class FeedServerOld():

    class DataReciever():

        context = zmq.Context()

        def __init__(self, port, handler):
            self.handler = handler

            self.socket = FeedServerOld.DataReciever.context.socket(zmq.PULL)
            self.socket.connect('tcp://127.0.0.1:%s' % port)

            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)


        async def read_data(self, args):
            if self.poller.poll(0.2*1000):
                await self.handler(self.socket.recv_json(), *args)


    class CtrlClient():

        context = zmq.Context()

        def __init__(self, port: int, handler: Callable):
            self.handler = handler
            self.socket  = None
            self.port    = port

            self.__register()


        async def request(self, data, args):
            try: self.socket.send_json(data, zmq.NOBLOCK)
            except zmq.error.Again:
                warnings.warn('FeedServerOld Request failed to send')
                return False

            # We can afford to poll for so long since it's a one off command and is async
            if self.poller.poll(15.0*1000):
                await self.handler(self.socket.recv_json(), *args)
                return True
            else:
                warnings.warn('FeedServerOld Request timed out')
                self.__register()
                return False


        def __register(self):
            if self.socket != None:
                self.socket.close()

            self.socket = FeedServerOld.CtrlClient.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.connect("tcp://127.0.0.1:%s" % self.port)

            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)
