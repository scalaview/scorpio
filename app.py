from flask import Flask
import requests
import os
from config import config
from flask_script import Manager, Shell, Server
from flask_sqlalchemy import SQLAlchemy
from flask.json import JSONEncoder
db = SQLAlchemy()

class MiniJSONEncoder(JSONEncoder):
    """Minify JSON output."""
    item_separator = ','
    key_separator = ':'

def create_app(env):
    app = Flask(__name__)

    app.config.from_object(config[env])
    if app.config.get('DEBUG'):
      from flask_cors import CORS
      CORS(app)
    app.json_encoder = MiniJSONEncoder
    db.init_app(app)
    config[env].init_app(app)
    from api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app
