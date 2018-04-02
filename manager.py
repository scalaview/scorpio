import os
from flask_script import Manager, Shell, Server
from app import create_app

app = create_app(os.getenv('CHAIN_CONFIG') or 'default')
manager = Manager(app)

if __name__ == '__main__':
    manager.run()