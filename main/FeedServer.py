import os
import platform
import asyncio
import socket
from typing import List, Optional, Sequence

import uvicorn

import logging
import fastapi
import config

from main.utils import Utils


class UvicornServerPatch(uvicorn.Server):
    """
    Patches the original `startup` behavior as of uvicorn 0.21.1
    Fixes case(s):
        - When port is already taken the server would fail to bind to the port. This would
          proceed to call `sys.exit(1)` after shutting down, effectively terminating the
          entire python app. This is undesired since the this server is a service that resides
          in a larger overall app. ctrl+f "PATCH" for code commentating fix.
    """

    __logger = logging.getLogger('UvicornServerPatch')

    async def startup(self: uvicorn.Server, sockets: Optional[List[socket.socket]] = None) -> None:
        await self.lifespan.startup()
        if self.lifespan.should_exit:
            self.should_exit = True
            return

        config = self.config

        def create_protocol(
            _loop: Optional[asyncio.AbstractEventLoop] = None,
        ) -> asyncio.Protocol:
            return config.http_protocol_class(  # type: ignore[call-arg]
                config=config,
                server_state=self.server_state,
                app_state=self.lifespan.state,
                _loop=_loop,
            )

        loop = asyncio.get_running_loop()

        listeners: Sequence[socket.SocketType]
        if sockets is not None:
            # Explicitly passed a list of open sockets.
            # We use this when the server is run from a Gunicorn worker.

            def _share_socket(
                sock: socket.SocketType,
            ) -> socket.SocketType:  # pragma py-linux pragma: py-darwin
                # Windows requires the socket be explicitly shared across
                # multiple workers (processes).
                from socket import fromshare  # type: ignore[attr-defined]

                sock_data = sock.share(os.getpid())  # type: ignore[attr-defined]
                return fromshare(sock_data)

            self.servers = []
            for sock in sockets:
                if config.workers > 1 and platform.system() == "Windows":
                    sock = _share_socket(  # type: ignore[assignment]
                        sock
                    )  # pragma py-linux pragma: py-darwin
                server = await loop.create_server(
                    create_protocol, sock=sock, ssl=config.ssl, backlog=config.backlog
                )
                self.servers.append(server)
            listeners = sockets

        elif config.fd is not None:  # pragma: py-win32
            # Use an existing socket, from a file descriptor.
            sock = socket.fromfd(config.fd, socket.AF_UNIX, socket.SOCK_STREAM)
            server = await loop.create_server(
                create_protocol, sock=sock, ssl=config.ssl, backlog=config.backlog
            )
            assert server.sockets is not None  # mypy
            listeners = server.sockets
            self.servers = [server]

        elif config.uds is not None:  # pragma: py-win32
            # Create a socket using UNIX domain socket.
            uds_perms = 0o666
            if os.path.exists(config.uds):
                uds_perms = os.stat(config.uds).st_mode
            server = await loop.create_unix_server(
                create_protocol, path=config.uds, ssl=config.ssl, backlog=config.backlog
            )
            os.chmod(config.uds, uds_perms)
            assert server.sockets is not None  # mypy
            listeners = server.sockets
            self.servers = [server]

        else:
            # Standard case. Create a socket from a host/port pair.
            try:
                server = await loop.create_server(
                    create_protocol,
                    host=config.host,
                    port=config.port,
                    ssl=config.ssl,
                    backlog=config.backlog,
                )
            except OSError as exc:
                UvicornServerPatch.__logger.error(exc)
                await self.lifespan.shutdown()
                return  # PATCH: Replaces the `sys.exit(1)` of original implementation

            assert server.sockets is not None
            listeners = server.sockets
            self.servers = [server]

        if sockets is None:
            self._log_started_message(listeners)
        else:
            # We're most likely running multiple workers, so a message has already been
            # logged by `config.bind_socket()`.
            pass

        self.started = True



class FeedServer():

    app = fastapi.FastAPI()

    @staticmethod
    async def init(callback):
        is_debug = 'db' in config.runtime_mode
        #FeedServer.app.config['DEBUG'] = is_debug
        FeedServer.callback = callback
        FeedServer.logger = logging.getLogger('FeedServer')

        FeedServer.logger.info('Initializing server: 127.0.0.1:5001')
        FeedServer.http_server = UvicornServerPatch(uvicorn.Config(app=FeedServer.app, host='127.0.0.1', port=config.feed_server_port, log_level='debug'))
        await FeedServer.http_server.serve()


    @staticmethod
    @app.put('/ping')  # type: ignore
    async def ping():
        FeedServer.logger.info('Pong')
        return { 'status' : 'ok' }


    @staticmethod
    @app.put('/internal')  # type: ignore
    async def shutdown(data: fastapi.Request):
        if FeedServer.callback is None:
            return { 'status' : 'err' }

        data = await data.json()
        FeedServer.logger.debug(f'Internal command: {data}')

        if 'shutdown' in data:
            try:
                await FeedServer.http_server.shutdown()
                return { 'status' : 'ok' }
            except Exception as e:
                FeedServer.logger.error(
                    f'Error processing "/internal": {type(e)}\n'
                    f'{Utils.format_exception(e)}'
                )
                return { 'status' : 'err' }

        return { 'status' : 'err' }


    @staticmethod
    @app.post('/post')  # type: ignore
    async def handle_post(data: fastapi.Request):
        if FeedServer.callback is None:
            return { 'status' : 'err' }

        data = await data.json()

        try:
            await FeedServer.callback(data)
        except KeyError as e:
            FeedServer.logger.error(
                f'Error processing "/post":\n'
                f'Raised {type(e)}: {e}\n'
                f'Data: {data}'
            )
        except Exception as e:
            FeedServer.logger.error(
                f'Error processing "/post":\n'
                f'{Utils.format_exception(e)}'
            )
            return { 'status' : 'err' }

        return { 'status' : 'ok' }
