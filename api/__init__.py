from flask import Blueprint, jsonify, request
from blockchain import Scorpio, Account, Transaction, DymEncoder
from util import url_validator, sync_blocks, block_decoder, transaction_decoder
from config import config
import logging
import json
import util

api = Blueprint('api', __name__)

def json_res(data={}, err=0, message="success"):
    result = {'err': err, 'message': message }
    if data:
        result['data'] = data
    return jsonify(result)

@api.before_app_request
def before_request():
    if request.method in ['POST']:
        if not request.is_json:
            return json_res(err=1005, message="only accep application/json")

@api.errorhandler(Exception)
def handle_error(e):
    code = 500
    logging.error(str(e))
    return jsonify(error=str(e)), code

@api.route('/blocks', methods=['GET'])
def blocks():
    return json_res(Scorpio.get_blockchain()), 200

@api.route('/block', methods=['POST'])
def receive_block():
    params = request.get_json(silent=True)
    if params:
        json_block = params.get("block")
        if not json_block:
            return json_res(err=1017, message="invalid block")
        if Scorpio.add_block_to_chain(block_decoder(json_block)):
            util.broadcast_latest()
        return json_res(Scorpio.get_blockchain()), 200
    return json_res(err=1013, message="miss params")

@api.route('/latest_block', methods=['GET'])
def latest_block():
    return json_res(Scorpio.get_latest_block()), 200

@api.route('/block/<hash>', methods=['GET'])
def block(hash):
    target = {}
    for block in Scorpio.get_blockchain():
        if block.hash == hash:
            target = block
    return json_res(target), 200

@api.route('/transaction/<id>', methods=['GET'])
def transaction(id):
    transaction = {}
    for block in Scorpio.get_blockchain():
        for tx in block.transactions:
            if tx.id == id:
                transaction = tx
    return json_res(transaction), 200

@api.route('/address/<address>', methods=['GET'])
def address(address):
    unspent_outputs = [ unspent_output for unspent_output in Scorpio.get_unspent_tx_outs() if unspent_output.address == address ]
    return json_res(unspent_outputs), 200

@api.route('/address', methods=['POST'])
def pub_address():
    params = request.get_json(silent=True)
    if params:
        key = params.get('key')
        if not key:
            return json_res(err=1013, message="miss params")
        try:
            return json_res({'address': Account(key).pubkey_der()})
        except Exception as e:
            logging.error(e)
            return json_res(err=1014, message="private invalid")
    return json_res(err=1013, message="miss params")

@api.route('/unspent_transaction_outputs', methods=['GET'])
def unspent_transaction_outputs():
    return json_res(Scorpio.get_unspent_tx_outs()), 200

@api.route('/my_unspent_transaction_outputs', methods=['GET'])
def my_unspent_transaction_outputs():
    return json_res(Scorpio.get_my_unspent_transaction_outputs()), 200

@api.route('/balance/<address>', methods=['GET'])
def balance(address=Scorpio.get_pubkey_der()):
    balance = Account.get_blance(address, Scorpio.get_unspent_tx_outs())
    return json_res({'balance': balance}), 200

@api.route('/send_transaction', methods=['POST'])
def send_transaction():
    params = request.get_json(silent=True)
    if params:
        address = params.get('address')
        amount = params.get('amount')
        if not address or type(address) != str or not amount or (type(amount) != int and type(amount) != float):
            return json_res(err=1015, message="invalid address or amount")
        result = Transaction.send_transaction(address, amount)
        return json_res(result)
    return json_res(err=1013, message="miss params")


@api.route('/transactions', methods=['POST'])
def transactions():
    params = request.get_json(silent=True)
    if params:
        transactions = params.get('transactions')
        if not transactions:
            return json_res(err=1015, message="invalid transactions")
        for tx in transactions:
            Scorpio.add_to_transaction_pool(transaction_decoder(tx), Scorpio.get_unspent_tx_outs())
        return json_res(Scorpio.get_transaction_pool())
    return json_res(err=1013, message="miss params")

@api.route('/transaction_pool', methods=['GET'])
def transaction_pool():
    return json_res(Scorpio.get_transaction_pool())

@api.route('/add_peer', methods=['POST'])
def add_peer():
    params = request.get_json(silent=True)
    if params:
        url = params.get('url')
        if not url_validator(url):
            return json_res(err=1016, message="invalid url")
        config["nodes"].add(url)
        sync_blocks(config["nodes"])
        logging.error("sync_blocks finish")
        return json_res()
    return json_res(err=1013, message="miss params")

