import os
import json
import blockchain

basedir = os.path.abspath(os.path.dirname(__file__))
config_path = basedir + "/config.json"
config_json = json.loads(open(config_path).read())

class Option():
    def __init__(self, d):
        self.__dict__ = d

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    @staticmethod
    def init_app(app):
        blockchain.Scorpio.build_instance(os.environ.get("PRIV_KEY"))
        app.json_encoder = blockchain.DymEncoder


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    option = Option(config_json.get("development"))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql://%s:%s@%s/%s' % (option.username, option.password, option.hostname, option.database)

class StagingConfig(Config):
    TESTING = True
    option = Option(config_json.get("staging"))
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'mysql://%s:%s@%s/%s' % (option.username, option.password, option.hostname, option.database)

class ProductionConfig(Config):
    option = Option(config_json.get("production"))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql://%s:%s@%s/%s' % (option.username, option.password, option.hostname, option.database)

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'nodes': set(),
    'url': os.environ.get("SELFHOST") or 'http://127.0.0.1:5001'
}