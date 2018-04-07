import os
from flask_script import Manager, Shell, Server
from app import create_app
import blockchain
import logging
import json

app = create_app(os.getenv('CHAIN_CONFIG') or 'default')
manager = Manager(app)

@manager.command
@manager.option('-n', '--node', help='Node Url')
def mine(node='http://127.0.0.1:5000'):
    from config import config
    import util
    config['nodes'].add(node)
    util.sync_blocks()
    util.sync_transaction_pool()
    block = blockchain.Block.generate_next_block()

if __name__ == '__main__':
    manager.run()