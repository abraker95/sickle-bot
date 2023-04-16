import uvicorn

import logging
import fastapi


class FeedServer():

    app = fastapi.FastAPI()

    @staticmethod
    async def init(callback):
        #is_debug = 'db' in config.runtime_mode
        #FeedServer.app.config['DEBUG'] = is_debug
        FeedServer.callback = callback
        FeedServer.logger = logging.getLogger('FeedServer')

        # Unsupported for now because discord dispatch events act weird when this is done
        #if is_debug:
        #    FeedServer.logger.info(f'Discord feed server version {FeedServer._version}')
        #    FeedServer.logger.info('Initializing debug server...')
        #    FeedServer.app.run()
        #else:
        FeedServer.logger.info('Initializing server: 127.0.0.1:5000')
        FeedServer.http_server = uvicorn.Server(uvicorn.Config(app=FeedServer.app, host='127.0.0.1', port=5000, log_level='debug'))
        await FeedServer.http_server.serve()



@FeedServer.app.put('/ping')  # type: ignore
async def ping():
    FeedServer.logger.info('Pong')
    return { 'status' : 'ok' }


@FeedServer.app.put('/internal')  # type: ignore
async def shutdown(data: dict):
    if FeedServer.callback is None:
        return

    try:
        #data = flask.request.get_json()
        FeedServer.logger.debug(f'Internal command: {data}')

        if 'shutdown' in data:
            await FeedServer.http_server.shutdown()
    except Exception as e:
        FeedServer.logger.error(f'Error parsing data: {e}')
        return { 'status' : 'err' }

    return { 'status' : 'ok' }


@FeedServer.app.post('/post')  # type: ignore
async def handle_post(data: dict):
    if FeedServer.callback is None:
        return

    try:
        #data = flask.request.get_json()
        FeedServer.callback({
            'type' : 'post',
            'data' : data
        })
    except Exception as e:
        FeedServer.logger.error(f'Error queuing data: {e}')
        return { 'status' : 'err' }

    return { 'status' : 'ok' }
