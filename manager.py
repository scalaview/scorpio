import os
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand, upgrade
from flask_sqlalchemy import get_debug_queries
from app import create_app, db
import blockchain
import logging
import json
import models

app = create_app(os.getenv('CHAIN_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

def make_shell_context():
    return dict(get_debug_queries=get_debug_queries, app=app, db=db, DBBlock=models.DBBlock, DBTransaction=models.DBTransaction, \
        DBTxIn=models.DBTxIn, DBTxOut=models.DBTxOut)
manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
@manager.option('-n', '--node', help='Node Url')
def mine(node='http://127.0.0.1:5000'):
    from config import config
    import util
    config['nodes'].add(node)
    while True:
        util.sync_blocks()
        util.sync_transaction_pool()
        coinbase_tx = util.get_coinbase_transaction(node)
        block = blockchain.Block.generate_next_block_from_remote_coinbas(coinbase_tx)
        print("generate block %s" % block.hash)


@manager.command
@manager.option('-po', '--port', help='port')
def deploy(port=5000):
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()

@manager.command
@manager.option('-n', '--node', help='Node Url')
def mine(node='http://127.0.0.1:5000'):
    from config import config
    import util
    config['nodes'].add(node)
    while True:
        util.sync_blocks()
        util.sync_transaction_pool()
        coinbase_tx = util.get_coinbase_transaction(node)
        block = blockchain.Block.generate_next_block_from_remote_coinbas(coinbase_tx)
        print("generate block %s" % block.hash)

@manager.command
@manager.option('-f', '--file', help='file path')
def import_file(file):
    from util import import_from_json, chain_serialization
    blocks = import_from_json(file)
    chain_serialization(blocks)


@manager.command
def migrate():
    upgrade()

if __name__ == '__main__':
    manager.run()
