import os
from flask_script import Manager, Shell, Server
from app import create_app
from blockchain import Scorpio, DymEncoder, Block
import logging
import json

app = create_app(os.getenv('CHAIN_CONFIG') or 'default')
manager = Manager(app)

@manager.command
def mine():
    block = Block.generate_next_block()

if __name__ == '__main__':
    manager.run()