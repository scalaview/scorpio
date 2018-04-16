import re
import requests
import blockchain
import config as config_obj
import logging
import json
import threading

config = config_obj.config
Scorpio = blockchain.Scorpio
Block = blockchain.Block
Transaction = blockchain.Transaction
TxIn = blockchain.TxIn
TxOut = blockchain.TxOut
DymEncoder = blockchain.DymEncoder

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def url_validator(url):
    return regex.match(url)

def broadcast_latest():
    threading.Thread(target=broadcast_latest_with_thread).start()

def broadcast_latest_with_thread():
    for peer in config["nodes"]:
        post_data = {"block": Scorpio.get_latest_block()}
        headers = {'Content-type': 'application/json'}
        try:
            res = requests.post("%s/block" % peer, data=json.dumps(post_data, cls=blockchain.DymEncoder), headers=headers)
        except Exception as e:
            logging.error(e)

def broad_cast_transaction_pool():
    threading.Thread(target=broad_cast_transaction_pool).start()

def broad_cast_transaction_pool_with_thread():
    for peer in config["nodes"]:
        post_data = {"transactions": json.dumps(Scorpio.get_transaction_pool(), cls=DymEncoder)}
        headers = {'Content-type': 'application/json'}
        try:
            res = requests.post("%s/transactions" % peer, json=post_data, headers=headers)
        except Exception as e:
            logging.error(e)

def block_decoder(obj):
    transactions = []
    if obj.get("transactions"):
        for x in obj.get('transactions'):
            transactions.append(transaction_decoder(x))
    return Block(int(obj.get('index')), obj.get('hash'), obj.get('previous_hash'), int(obj.get('difficulty')), transactions, obj.get('timestamp'), obj.get('nonce'))

def transaction_decoder(obj):
    tx_ins = []
    tx_outs = []
    if obj.get('tx_ins'):
        for x in obj.get('tx_ins'):
            tx_ins.append(tx_in_decoder(x))
    if obj.get('tx_outs'):
        for x in obj.get('tx_outs'):
            tx_outs.append(tx_out_decoder(x))
    return Transaction(obj.get('id'), tx_ins, tx_outs)

def tx_in_decoder(obj):
    return TxIn(obj.get('tx_out_id'), obj.get('tx_out_index'), obj.get('signature'))

def tx_out_decoder(obj):
    return TxOut(obj.get('address'), obj.get('amount'))

def sync_block(peer):
    try:
        res = requests.get("%s/blocks" % peer)
        if res.status_code != 200:
            raise ValueError("sync blocks from %s fail, status code: %d" %(peer, res.status_code))
        json_data = res.json()
        if json_data.get("err") != 0:
            raise ValueError("sync blocks from %s, invalid response, message %s" %(peer, json_data.get("message")))
        data = json_data.get("data")
        if data:
            blocks = []
            for x in data:
                blocks.append(block_decoder(x))
            Scorpio.replace_chain(blocks)
    except ValueError as e:
        logging.error(e)

def sync_blocks(nodes=config['nodes']):
    for peer in nodes:
        try:
            res = requests.get("%s/latest_block" % peer)
            if res.status_code != 200:
                raise ValueError("latest_block from %s fail, status code: %d" %(peer, res.status_code))
            json_data = res.json()
            if json_data.get("err") != 0:
                raise ValueError("latest_block from %s, invalid response, message %s" %(peer, json_data.get("message")))
            data = json_data.get("data")
            if data:
                latest_block = Scorpio.get_latest_block()
                if data.get('index') == latest_block.index and data.get('hash') == latest_block.hash:
                    pass
                else:
                    sync_block(peer)
        except ValueError as e:
            logging.error(e)

def sync_transaction_pool():
    for peer in config['nodes']:
        try:
            res = requests.get("%s/transaction_pool" % peer)
            if res.status_code != 200:
                raise ValueError("transaction_pool from %s fail, status code: %d" %(peer, res.status_code))
            json_data = res.json()
            if json_data.get("err") != 0:
                raise ValueError("transaction_pool from %s, invalid response, message %s" %(peer, json_data.get("message")))
            data = json_data.get("data")
            if data:
                for tx in data:
                    Scorpio.add_to_transaction_pool(transaction_decoder(tx), Scorpio.get_unspent_tx_outs())
        except ValueError as e:
            logging.error(e)

def get_coinbase_transaction(peer):
    try:
        res = requests.get("%s/coinbase_transaction" % peer)
        if res.status_code != 200:
            raise ValueError("coinbase_transaction from %s fail, status code: %d" %(peer, res.status_code))
        json_data = res.json()
        if json_data.get("err") != 0:
            raise ValueError("coinbase_transaction from %s, invalid response, message %s" %(peer, json_data.get("message")))
        data = json_data.get("data")
        if data:
            return transaction_decoder(data)
        else:
            raise ValueError("miss transaction")
    except ValueError as e:
        logging.error(e)

def import_from_json(file):
    from models import DBBlock, DBTransaction, DBTxIn, DBTxOut
    data = json.loads(open(file).read())
    blocks = []
    for index, json_block in enumerate(data.get('data')):
        blocks.append(block_decoder(json_block))
    return blocks


def chain_serialization(blocks):
    from models import DBBlock, DBTransaction, DBTxIn, DBTxOut
    from app import db
    for block in blocks:
        block_serialization(block)

def block_serialization(block):
    from models import DBBlock, DBTransaction, DBTxIn, DBTxOut
    from app import db
    dbblock = DBBlock.build(block)
    db.session.add(dbblock)
    db.session.commit()
    for index, tx in enumerate(block.transactions):
        dbtransaction = DBTransaction.build(dbblock.id, tx, index)
        db.session.add(dbtransaction)
        db.session.commit()
        for tx_in_idx, tx_in in enumerate(tx.tx_ins):
            dbtx_in = DBTxIn.build(tx.id, tx_in, tx_in_idx)
            db.session.add(dbtx_in)
        db.session.commit()
        for tx_out_idx, tx_out in enumerate(tx.tx_outs):
            dbtx_out = DBTxOut.build(tx.id, tx_out, tx_out_idx)
            db.session.add(dbtx_out)
        db.session.commit()


