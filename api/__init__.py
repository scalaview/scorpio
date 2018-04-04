from flask import Blueprint, jsonify
from ..blockchain import Scorpio, Account
import logging

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

@api.route('/blocks', methods=['GET'])
def blocks():
    return json_res(Scorpio.get_blockchain()), 200

@api.route('/block/<hash>', methods=['GET'])
def block(hash):
    target = {}
    for block in Scorpio.get_blockchain():
        if block.hash == hash:
            target = jsonify(block)
    return json_res(target), 200

@api.route('/transaction/<id>', methods=['GET'])
def transaction(id):
    transaction = {}
    for block in Scorpio.get_blockchain():
        for tx in block.transactions:
            if tx.id == id:
                transaction = jsonify(tx)

    return json_res(transaction), 200

@api.route('/address/<address>', methods=['GET'])
def address(address):
    unspent_outputs = [ jsonify(unspent_output) for unspent_output in Scorpio.get_unspent_tx_outs() if unspent_output.address == address ]
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
    return jsonify(Scorpio.my_unspent_transaction_outputs()), 200


@api.route('/balance/<address>', methods=['GET'])
def balance(address=Scorpio.get_pubkey_der()):
    balance = Account.get_blance(address, Scorpio.get_unspent_tx_outs())
    return json_res({'balance': balance}), 200

@api.route('/send_transaction', methods=['POST'])
def send_transaction():
    pass