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
    coinbase_tx = util.get_coinbase_transaction(node)
    block = blockchain.Block.generate_next_block_from_remote_coinbas(coinbase_tx)


@manager.command
@manager.option('-po', '--port', help='port')
def deploy(port=5000):
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()

if __name__ == '__main__':
    manager.run()