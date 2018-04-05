from flask import Flask
import requests
import os
from config import config
from flask_script import Manager, Shell, Server

def create_app(env):
    app = Flask(__name__)
    app.config.from_object(config[env])
    config[env].init_app(app)
    from api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
