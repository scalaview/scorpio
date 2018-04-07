import os
from flask_script import Manager, Shell, Server
from app import create_app
import blockchain
import logging
import json

app = create_app(os.getenv('CHAIN_CONFIG') or 'default')
manager = Manager(app)

@manager.command
def mine():
    from config import config
    import util
    config['nodes'].add('http://127.0.0.1:5000')
    util.sync_blocks(config['nodes'])
    util.sync_transaction_pool()
    block = blockchain.Block.generate_next_block()



if __name__ == '__main__':
    manager.run()