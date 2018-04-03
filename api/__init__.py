from flask import Blueprint
from ..blockchain import Scorpio

api = Blueprint('api', __name__)

@api.route('/blocks', methods=['GET'])
def blocks():
    return jsonify(Scorpio.get_blockchain()), 200


@api.route('/block/<hash>', methods=['GET'])
def block(hash):
    target = {}
    for block in Scorpio.get_blockchain():
        if block.hash == hash:
            target = jsonify(block)
    return target, 200

@api.route('/transaction/<id>', methods=['GET'])
def transaction(id):
    transaction = {}
    for block in Scorpio.get_blockchain():
        for tx in block.transactions:
            if tx.id == id:
                transaction = jsonify(tx)

    return transaction, 200

@api.route('/address/<address>', methods=['GET'])
def address(address):
    unspent_outputs = [ jsonify(unspent_output) for unspent_output in Scorpio.get_unspent_tx_outs() if unspent_output.address == address ]
    return unspent_outputs, 200