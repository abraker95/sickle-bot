import logging
import flask
import socket
import sys
from gevent.pywsgi import WSGIServer

import config


class FeedServer():

    app = flask.Flask(__name__)

    @staticmethod
    def init(callback):
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
        FeedServer.http_server = WSGIServer(('127.0.0.1', 5000), FeedServer.app)

        try:
            FeedServer.http_server.serve_forever()
        except KeyboardInterrupt:
            config.runtime_quit = True
            FeedServer.logger.info('Exiting server loop...')
            return
        except Exception as e:
            FeedServer.logger.exception('Error in server loop!')
            raise e




@FeedServer.app.route('/internal', methods=['PUT'])  # type: ignore
def shutdown():
    if FeedServer.callback is None:
        return

    try:
        data = flask.request.get_json()
        FeedServer.logger.debug(f'Internal command: {data}')

        if 'shutdown' in data:
            FeedServer.http_server.close()
    except Exception as e:
        FeedServer.logger.error(f'Error parsing data: {e}')
        return { 'status' : 'err' }

    return { 'status' : 'ok' }


@FeedServer.app.route('/post', methods=['POST'])  # type: ignore
def handle_post():
    if FeedServer.callback is None:
        return

    try:
        data = flask.request.get_json()
        FeedServer.callback({
            'type' : 'post',
            'data' : data
        })
    except Exception as e:
        FeedServer.logger.error(f'Error queuing data: {e}')
        return { 'status' : 'err' }

    return { 'status' : 'ok' }
