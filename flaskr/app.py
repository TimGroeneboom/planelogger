import logging
from flask import Flask
from flask_cors import CORS

from flaskr.scheduler import Scheduler
from flaskr.swagger import swagger_template, swagger_config
from flaskr.testapi import test_api_page
from flaskr.api import api_page
from flasgger import Swagger, LazyJSONEncoder
from flaskr import environment
import sys, socket

# Set log level
logging.basicConfig(level=environment.LOGLEVEL)


def create_app():
    # Create app
    app = Flask(__name__)

    # Setup scheduler, bind a socket to a port to setup one scheduler for each worker thread
    # spawned by gunicorn
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 47200))
    except socket.error:
        logging.debug("Scheduler already started, do nothing")
    else:
        from apscheduler.schedulers.background import BackgroundScheduler
        app.scheduler = Scheduler(loglevel=environment.LOGLEVEL)

    # Set log level
    app.logger.setLevel(level=environment.LOGLEVEL)

    # Setup json encoder
    app.json_encoder = LazyJSONEncoder

    # Register blueprints
    app.register_blueprint(api_page)
    if environment.DEPLOY_TEST_API:
        app.register_blueprint(test_api_page)

    # Setup swagger
    app.swagger = Swagger(app,
                          template=swagger_template,
                          config=swagger_config)

    if __name__ != '__main__':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(level=environment.LOGLEVEL)

    # Enable CORS
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    return app


# Fire up app from cli
if __name__ == '__main__':
    create_app().run()
