import time
import hashlib
import json
import logging
from secp256k1 import PrivateKey, PublicKey
from binascii import hexlify, unhexlify
from functools import reduce
import math
import copy

BLOCK_GENERATION_INTERVAL = 10

DIFFICULTY_ADJUSTMENT_INTERVAL = 10

DEFAULT_DIFFICULTY = 2

def get_current_timestamp():
    return int(time.time())

def repeat_to_length(string_to_expand, length):
    return (string_to_expand * (int(length/len(string_to_expand))+1))[:length]

def hex_to_binary(string):
    result = ''
    store_dict = {
        '0': '0000', '1': '0001', '2': '0010', '3': '0011', '4': '0100',
        '5': '0101', '6': '0110', '7': '0111', '8': '1000', '9': '1001',
        'a': '1010', 'b': '1011', 'c': '1100', 'd': '1101',
        'e': '1110', 'f': '1111'
    }
    for s in string:
        if store_dict.get(s):
            result += store_dict.get(s)
        else:
            return None
    return result

class DymEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, TxIn) or isinstance(obj, TxOut) or isinstance(obj, Transaction) or isinstance(obj, Account) or isinstance(obj, Block) or isinstance(obj, UnspentTxOut):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)

class Scorpio(object):

    instance = None

    @staticmethod
    def build_instance(privkey=None):
        Scorpio.instance = Scorpio(Account(privkey))

    @staticmethod
    def get_latest_block():
        if Scorpio.instance:
            return Scorpio.instance._get_latest_block()
        else:
            return None

    @staticmethod
    def get_blockchain():
        if Scorpio.instance:
            return Scorpio.instance.blockchain
        else:
            return None

    @staticmethod
    def get_unspent_tx_outs():
        return Scorpio.instance.unspent_tx_outs

    @staticmethod
    def get_transaction_pool():
        return Scorpio.instance._get_transaction_pool()

    @staticmethod
    def add_block_to_chain(new_block):
        return Scorpio.instance._add_block_to_chain(new_block)

    @staticmethod
    def get_tx_pool_ins(_transaction_pool):
        return [tx_in for tx in _transaction_pool for tx_in in tx.tx_ins]

    @staticmethod
    def is_valid_tx_for_pool(tx, _transaction_pool):
        tx_pool_ins = Scorpio.get_tx_pool_ins(_transaction_pool)

        for tx_in in tx.tx_ins:
            for tx_pool_in in tx_pool_ins:
                if tx_in.tx_out_index == tx_pool_in.tx_out_index and tx_in.tx_out_id == tx_pool_in.tx_out_id:
                    return False
        return True

    @staticmethod
    def get_my_unspent_transaction_outputs():
        return Account.find_unspent_tx_outs(Scorpio.get_pubkey_der(), Scorpio.get_unspent_tx_outs())

    @staticmethod
    def get_pubkey_der():
        return Scorpio.instance.my_account.pubkey_der()

    @staticmethod
    def get_privkey_der():
        return Scorpio.instance.my_account.privkey_der()

    @staticmethod
    def get_difficulty(blocks):
        latest_block = blocks[-1]
        if latest_block.index % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latest_block.index != 0:
            return Scorpio.adjust_difficulty(blocks)
        else:
            return latest_block.difficulty or DEFAULT_DIFFICULTY

    @staticmethod
    def adjust_difficulty(blocks):
        if len(blocks) > DIFFICULTY_ADJUSTMENT_INTERVAL:
            latest_block = blocks[-1]
            prev_adjusted_block = blocks[-BLOCK_GENERATION_INTERVAL]
            expected_cost = BLOCK_GENERATION_INTERVAL * DIFFICULTY_ADJUSTMENT_INTERVAL
            spend_time = latest_block.timestamp - prev_adjusted_block.timestamp
            if spend_time > expected_cost * 2 :
                return prev_adjusted_block.difficulty - 1
            elif spend_time < expected_cost / 2 :
                return prev_adjusted_block.difficulty + 1
            else:
                return prev_adjusted_block.difficulty

    @staticmethod
    def get_accumulated_difficulty(blocks):
        diff = 0
        for block in blocks:
            diff += math.pow(2, block.difficulty)
        return diff

    @staticmethod
    def add_to_transaction_pool(tx, unspent_tx_outs):
        return Scorpio.instance._add_to_transaction_pool(tx, unspent_tx_outs)

    @staticmethod
    def is_valid_chain(blockchain_to_validate):
        if json.dumps(blockchain_to_validate[0], cls=DymEncoder) != json.dumps(Block.genesis_block(), cls=DymEncoder):
            return None

        unspent_tx_outs = [];
        for index, current_block in enumerate(blockchain_to_validate):
            if index != 0 and not Block.is_valid_new_block(current_block, blockchain_to_validate[index-1]):
                return None
            unspent_tx_outs = Block.process_transactions(current_block.transactions, unspent_tx_outs, current_block.index)
            if unspent_tx_outs is None or len(unspent_tx_outs) == 0:
                return None
        return unspent_tx_outs

    @staticmethod
    def replace_chain(new_blocks):
        Scorpio.instance._replace_chain(new_blocks)

    @staticmethod
    def handle_received_transaction(transaction):
        Scorpio.add_to_transaction_pool(transaction, Scorpio.get_unspent_tx_outs())

    def __init__(self, account=None):
        self.transaction_pool = []
        self.blockchain = [Block.genesis_block()]
        self.unspent_tx_outs = Block.process_transactions(self.blockchain[0].transactions, [], 0)
        self.my_account = account or Account()

    def _get_transaction_pool(self):
        return copy.deepcopy(self.transaction_pool)

    def set_transaction_pool(self, tx_pool):
        self.transaction_pool = tx_pool

    def _get_latest_block(self):
        return self.blockchain[-1]

    def _add_to_transaction_pool(self, tx, unspent_tx_outs):
        if not self.validate_transaction(tx, unspent_tx_outs):
            raise ValueError('Trying to add invalid tx to pool, error from transaction')

        if not Scorpio.is_valid_tx_for_pool(tx, self.transaction_pool):
            raise ValueError('Trying to add invalid tx to pool, error from tx')

        logging.info('adding to tx_pool: %s', json.dumps(tx, cls=DymEncoder))
        self.transaction_pool.append(tx)

    def validate_transaction(self, transaction, unspent_tx_outs):
        return transaction.validate(unspent_tx_outs)

    def update_transaction_pool(self, unspent_tx_outs):
        invalid_txs = []
        for tx in self.transaction_pool:
            for tx_in in tx.tx_ins:
                if not UnspentTxOut.has_tx_in(tx_in, unspent_tx_outs):
                    invalid_txs.append(tx)

        if len(invalid_txs) > 0:
            logging.info('removing the following transactions from txPool: %s', json.dumps(invalid_txs, cls=DymEncoder))
            for tx in invalid_txs:
                if tx in self.transaction_pool:
                    self.transaction_pool.remove(tx)


    def _get_blockchain(self):
        return self.blockchain

    def _get_unspent_tx_outs(self):
        return self.unspent_tx_outs

    def set_unspent_tx_outs(self, un_tx_outs):
        self.unspent_tx_outs = un_tx_outs

    def _add_block_to_chain(self, new_block):
        if Block.is_valid_new_block(new_block, self._get_latest_block()):
            ret_val = Block.process_transactions(new_block.transactions, self._get_unspent_tx_outs(), new_block.index)
            if ret_val is None or len(ret_val) == 0:
                return False
            else:
                self.blockchain.append(new_block)
                self.set_unspent_tx_outs(ret_val)
                self.update_transaction_pool(ret_val)
                return True

        return False

    def _replace_chain(self, new_blocks):
        unspent_tx_outs = Scorpio.is_valid_chain(new_blocks)
        if unspent_tx_outs is not None and Scorpio.get_accumulated_difficulty(new_blocks) > Scorpio.get_accumulated_difficulty(self._get_blockchain()):
            logging.info('Received blockchain is valid. Replacing current blockchain with received blockchain')
            self.blockchain = new_blocks
            self.set_unspent_tx_outs(unspent_tx_outs)
            self.update_transaction_pool(self._get_unspent_tx_outs())
            import util
            util.broadcast_latest()
        else:
            logging.error("Received blockchain invalid, no need replace")

class Account(object):
    def __init__(self, key=None):
        if key == None:
            self.privkey = self.generate_privatekey()
        else:
            self.privkey = self.get_privkey(key)
        self.pubkey = self.get_publickey()

    def generate_privatekey(self):
        return PrivateKey()

    def get_privkey(self, key):
        return PrivateKey(unhexlify(key))

    def get_publickey(self):
        return self.privkey.pubkey

    def privkey_der(self):
        return self.privkey.serialize()

    def pubkey_der(self):
        return hexlify(self.pubkey.serialize()).decode('ascii')

    def balance(self):
        return Account.get_blance(self.pubkey_der, Scorpio.get_unspent_tx_outs())

    def sign(self, data):
        return hexlify(self.privkey.ecdsa_serialize(self.privkey.ecdsa_sign(unhexlify(data)))).decode('ascii')

    @staticmethod
    def get_blance(address, unspent_tx_outs):
        amount = 0.0
        for tx_out in Account.find_unspent_tx_outs(address, unspent_tx_outs):
            amount += tx_out.amount
        return amount

    @staticmethod
    def find_unspent_tx_out(transaction_id, index, unspent_tx_outs):
        for unspent_tx_out in unspent_tx_outs:
            if unspent_tx_out.tx_out_id == transaction_id and unspent_tx_out.tx_out_index == index:
                return unspent_tx_out
        return None

    @staticmethod
    def find_unspent_tx_outs(address, unspent_tx_outs):
        return [tx_out for tx_out in unspent_tx_outs if tx_out.address == address]

    @staticmethod
    def create_transation_tx_outs(receiver_address, amount, from_address, left_amount):
        if left_amount == 0.00:
            return [TxOut(receiver_address, amount)]
        else:
            return [TxOut(receiver_address, amount), TxOut(from_address, left_amount)]

    @staticmethod
    def unsigned_tx_in(available_tx_out):
        tx_in = TxIn()
        tx_in.tx_out_id = available_tx_out.tx_out_id
        tx_in.tx_out_index = available_tx_out.tx_out_index
        return tx_in

    @staticmethod
    def is_enough(amount, unspent_tx_outs):
        current_amount = 0.00
        for index, unspent_tx_out in enumerate(unspent_tx_outs):
            current_amount += unspent_tx_out.amount
            if current_amount >= amount:
                return (True, unspent_tx_outs[:(index+1)], (current_amount - amount))
        return (False, None, None)

    @staticmethod
    def is_valid_address(address):
        return True

class TxIn(object):
    def __init__(self, tx_out_id=None, tx_out_index=None, signature=None):
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.signature = signature

    def validate_struct(self):
        if not isinstance(self.signature, str):
            logging.error("invalid TxIn signature type")
            return False
        elif not isinstance(self.tx_out_id, str):
            logging.error("invalid TxIn tx_out_id type")
            return False
        elif not isinstance(self.tx_out_index, int):
            logging.error("invalid TxIn tx_out_index type")
            return False
        return True

    def validate(self, transaction, unspent_tx_outs):
        if not self.validate_struct():
            return False
        utx_out = None
        for unspent_tx_out in unspent_tx_outs:
            if unspent_tx_out.tx_out_id == self.tx_out_id and unspent_tx_out.tx_out_index == self.tx_out_index:
                utx_out = unspent_tx_out
        if utx_out is None:
            return False
        pubkey = PublicKey(unhexlify(utx_out.address), raw=True)
        if not pubkey.ecdsa_verify(unhexlify(transaction.id), pubkey.ecdsa_deserialize(unhexlify(self.signature))):
            logging.error("invalid tx_in signature")
            return False
        return True

    @staticmethod
    def db2obj(dbtx_in):
        return TxIn(tx_out_id=dbtx_in.tx_out_id, tx_out_index=dbtx_in.tx_out_index, signature=dbtx_in.signature)


class TxOut(object):
    def __init__(self, address, amount):
        self.address = address
        self.amount = amount

    @staticmethod
    def validate(address):
        True

    @staticmethod
    def db2obj(dbtx_out):
        return TxOut(address=dbtx_out.address, amount=dbtx_out.amount)

    def validate_struct(self):
        if not isinstance(self.address, str):
            logging.error("invalid TxOut address type")
            return False
        elif not (isinstance(self.amount, int) or isinstance(self.amount, float)) :
            logging.error("invalid TxOut amount type")
            return False
        return True

    def validate(self):
        if not self.validate_struct():
            return False
        TxOut.validate(self.address)

class UnspentTxOut(object):
    def __init__(self, tx_out_id, tx_out_index, address, amount):
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.address = address
        self.amount = amount

    @staticmethod
    def has_tx_in(tx_in, unspent_tx_outs):
        for u_tx_out in unspent_tx_outs:
            if u_tx_out.tx_out_id == tx_in.tx_out_id and u_tx_out.tx_out_index == tx_in.tx_out_index:
                return True
        return False

class Transaction(object):
    def __init__(self, id=None, tx_ins=[], tx_outs=[]):
        self.id = id
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs

    @staticmethod
    def _gene_transaction_id(transaction):
        tx_in_str = reduce((lambda x, y: x+y), list(map( (lambda tx_in: tx_in.tx_out_id + str(tx_in.tx_out_index)), transaction.tx_ins)))
        tx_out_str = reduce((lambda x, y: x+y), list(map( (lambda tx_in: ( tx_in.address + "%0.6f" % (tx_in.amount) )), transaction.tx_outs)))

        return hashlib.sha256((tx_in_str+tx_out_str).encode()).hexdigest()

    @staticmethod
    def generate_coinbase_transaction(address, index):
        transaction = Transaction()

        tx_in = TxIn()
        tx_in.signature = ''
        tx_in.tx_out_id = ''
        tx_in.tx_out_index = index

        transaction.tx_ins = [tx_in]
        transaction.tx_outs = [TxOut(address, Block.reward())]
        transaction.id = Transaction._gene_transaction_id(transaction)
        return transaction;

    # https://webbtc.com/tx/a4bfa8ab6435ae5f25dae9d89e4eb67dfa94283ca751f393c1ddc5a837bbc31b
    @staticmethod
    def create_transaction(privkey, receiver_address, amount, unspent_tx_outs, transaction_pool):
        account = Account(privkey)
        available_tx_outs = [ tx_out for tx_out in unspent_tx_outs if tx_out.address == account.pubkey_der() ]
        tx_ins = [ tx_in for transaction in transaction_pool for tx_in in transaction.tx_ins]

        invalid_tx_outs = []
        for tx_out in available_tx_outs:
            tx_in = None
            for _tx_in in tx_ins:
                if _tx_in.tx_out_index == tx_out.tx_out_index and _tx_in.tx_out_id == tx_out.tx_out_id:
                    tx_in = _tx_in
            if tx_in is not None:
                invalid_tx_outs.append(tx_out)
        for tx_out in invalid_tx_outs:
            available_tx_outs.remove(tx_out)

        is_enough, prepare_tx_outs, left_amount = Account.is_enough(amount, available_tx_outs)
        if is_enough:
            tx = Transaction()
            tx.tx_ins = list(map(Account.unsigned_tx_in, prepare_tx_outs))
            tx.tx_outs = Account.create_transation_tx_outs(receiver_address, amount, account.pubkey_der(), left_amount)
            tx.gene_transaction_id()
            tx.sign_tx_ins(account)
            return tx
        else:
            raise ValueError( "amount: %0.6f not enough from unspent_tx_outs: %s " % (amount, json.dumps(available_tx_outs, cls=DymEncoder)))

    @staticmethod
    def send_transaction(address, amount):
        return Transaction.send_transaction_by_key(Scorpio.get_privkey_der(), address, amount)

    @staticmethod
    def send_transaction_by_key(privkey, address, amount):
        tx = Transaction.create_transaction(privkey, address, amount, Scorpio.get_unspent_tx_outs(), Scorpio.get_transaction_pool())
        Scorpio.add_to_transaction_pool(tx, Scorpio.get_unspent_tx_outs())
        import util
        util.broad_cast_transaction_pool()
        return tx

    @staticmethod
    def db2obj(dbtx):
        return Transaction(id=dbtx.txid, tx_ins=[TxIn.db2obj(dbtx_in) for dbtx_in in dbtx.tx_ins], tx_outs=[TxOut.db2obj(dbtx_out) for dbtx_out in dbtx.tx_outs])

    def gene_transaction_id(self):
        self.id = Transaction._gene_transaction_id(self)

    def sign_tx_ins(self, account):
        for tx_in in self.tx_ins:
            tx_in.signature = account.sign(self.id)

    def validate_struct(self):
        if not isinstance(self.id, str):
            logging.error("invalid Transaction id type")
            return False
        elif not isinstance(self.tx_ins, list):
            logging.error("invalid Transaction tx_ins type")
            return False
        elif not isinstance(self.tx_outs, list):
            logging.error("invalid Transaction tx_outs type")
            return False
        return True

    def validate(self, unspent_tx_outs): #TODO
        # check
        if not self.validate_struct():
            logging.error("invalid transaction struct")
            return False
        if Transaction._gene_transaction_id(self) != self.id:
            logging.error("invalid transaction id")
            return False
        for tx_in in self.tx_ins:
            if not tx_in.validate(self, unspent_tx_outs):
                logging.error("invalid tx_in, transaction id: %s,  signature: %s" % (self.id, tx_in.signature))
                return False
        total_tx_in_amount = 0.0
        for tx_in in self.tx_ins:
            unspent_tx_out = Account.find_unspent_tx_out(tx_in.tx_out_id, tx_in.tx_out_index, unspent_tx_outs)
            if unspent_tx_out:
                total_tx_in_amount += unspent_tx_out.amount
        total_tx_out_amount = 0.0
        for tx_out in self.tx_outs:
            total_tx_out_amount += tx_out.amount
        if total_tx_in_amount != total_tx_out_amount:
            logging.error("invalid amount, total_tx_in_amount: %0.6f, total_tx_out_amount: %0.6f" % (total_tx_in_amount, total_tx_out_amount))
            return False

        return True

    def validate_transaction_id(self):
        return self.id == Transaction._gene_transaction_id(self)

    def is_coinbase(self, block_index):
        if not self.validate_transaction_id():
            logging.error("invalid transaction id", Transaction._gene_transaction_id(self))
            return False
        if len(self.tx_ins) != 1:
            logging.error("invalid tx_ins")
            return False
        if len(self.tx_outs) != 1:
            logging.error("invalid tx_outs")
            return False
        if self.tx_ins[0] and self.tx_ins[0].tx_out_index != block_index:
            logging.error("invalid tx_ins index")
            return False
        if self.tx_outs[0] and self.tx_outs[0].amount != Block.reward():
            logging.error("invalid tx_outs amount")
            return False
        return True


class Block(object):

    @staticmethod
    def reward():
        return 50

    @staticmethod
    def genesis_transaction():

        return Transaction(id="8e7b7a29be988415d963417a428b26e718f3fcffe9ccc8e402bf9423f960b2a8", tx_ins=[TxIn(tx_out_id="", tx_out_index=0, signature='')], tx_outs=[TxOut(address="02e525a9b78192e0a589a0ef74fc053ec97f5aabffe74263f968a57d08424a1e06", amount=Block.reward())])

    @staticmethod
    def genesis_block():
        return Block(0, 'd7b59f69ece171eceaccd18a79b297f13e14575ea7c8305cd60ed6b855525944', '', 0, [Block.genesis_transaction()], 1523026288, 0)


    def __init__(self, index, hash, previous_hash, difficulty, transactions, timestamp, nonce):
        self.index = index
        self.hash = hash
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.transactions = transactions
        self.timestamp = timestamp
        self.nonce = nonce

    @staticmethod
    def db2obj(dbblock):
        return Block(index=dbblock.index, hash=dbblock.hash, previous_hash=dbblock.previous_hash, difficulty=dbblock.difficulty, transactions=[ Transaction.db2obj(dbtx) for dbtx in dbblock.transactions], timestamp=int(time.mktime(dbblock.timestamp.timetuple())), nonce=dbblock.nonce)

    @staticmethod
    def validate(transactions, unspent_tx_outs, block_index):
        if not Block.validate_coinbase_transaction(transactions[0], block_index):
            logging.error("invalid coinbase transaction: %s" % json.dumps(transactions[0], cls=DymEncoder))
            return False
        for transaction in transactions[1:]:
            if not transaction.validate(unspent_tx_outs):
                return False
        return True

    @staticmethod
    def validate_coinbase_transaction(transaction, index):
        if transaction is None:
            logging.error("the first transaction must be the coinbase transaction")
            return False

        if not transaction.is_coinbase(index):
            return False
        return True

    @staticmethod
    def update_unspent_tx_outs(transactions, unspent_tx_outs):
        tmp_unspent_tx_outs = []
        prepare_tx_outs = []
        for transaction in transactions:
            for index, tx_out in enumerate(transaction.tx_outs):
                tmp_unspent_tx_outs.append(UnspentTxOut(transaction.id, index, tx_out.address, tx_out.amount))
            for tx_in in transaction.tx_ins:
                prepare_tx_outs.append(UnspentTxOut(tx_in.tx_out_id, tx_in.tx_out_index, "", 0))

        result = [unspent_tx_out for unspent_tx_out in unspent_tx_outs if not Account.find_unspent_tx_out(unspent_tx_out.tx_out_id, unspent_tx_out.tx_out_index, prepare_tx_outs) ]
        return result + tmp_unspent_tx_outs

    @staticmethod
    def process_transactions(transactions, unspent_tx_outs, block_index):
        if not Block.validate(transactions, unspent_tx_outs, block_index):
            return None
        return Block.update_unspent_tx_outs(transactions, unspent_tx_outs)

    @staticmethod
    def generate_raw_next_block(block_data):
        pre_block = Scorpio.get_latest_block()
        new_block = Block.find_block((pre_block.index+1), pre_block.hash, get_current_timestamp, block_data, Scorpio.get_difficulty(Scorpio.get_blockchain()))
        if Scorpio.add_block_to_chain(new_block):
            import util
            util.broadcast_latest()
            return new_block
        else:
            return None

    @staticmethod
    def calculate_hash_for_block(block):
        return Block.calculate_hash(block.index, block.previous_hash, block.timestamp, block.transactions, block.difficulty, block.nonce)

    @staticmethod
    def calculate_hash(index, previous_hash, timestamp, transactions, difficulty, nonce):
        tx_serialize = ""
        for tx in transactions:
            tx_serialize += tx.id
            for tx_in in tx.tx_ins:
                tx_serialize += tx_in.signature

        return hashlib.sha256((str(index) + previous_hash + str(timestamp) + tx_serialize + str(difficulty) + str(nonce)).encode()).hexdigest()

    @staticmethod
    def hash_matches_difficulty(hash, difficulty):
        hash_in_binary = hex_to_binary(hash)
        required_prefix = repeat_to_length("0", difficulty)
        return hash_in_binary.startswith(required_prefix)

    @staticmethod
    def is_valid_block_structure(block):
        return type(block.index) == int and type(block.hash) == str and type(block.previous_hash) == str and type(block.timestamp) == int and type(block.transactions) == list

    @staticmethod
    def is_valid_timestamp(new_block, previous_block):
        return ( previous_block.timestamp - 60 < new_block.timestamp ) and (new_block.timestamp - 60 < get_current_timestamp())

    @staticmethod
    def is_valid_hash(block):
        if not Block.hash_matches_block_content(block):
            logging.error('invalid hash, got:' + block.hash)
            return False

        if not Block.hash_matches_difficulty(block.hash, block.difficulty):
            logging.error('block difficulty not satisfied. Expected: ' + block.difficulty + 'got: ' + block.hash)

        return True

    @staticmethod
    def hash_matches_block_content(block):
        block_hash = Block.calculate_hash_for_block(block)
        return block_hash == block.hash

    @staticmethod
    def is_valid_new_block(new_block, previous_block):
        if not Block.is_valid_block_structure(new_block):
            return False
        if (previous_block.index + 1) != new_block.index:
            logging.error('invalid index')
            return False
        elif previous_block.hash != new_block.previous_hash:
            logging.error('invalid previous hash')
            return False
        elif not Block.is_valid_timestamp(new_block, previous_block):
            logging.error('invalid timestamp')
            return False
        elif not Block.is_valid_hash(new_block):
            return False
        return True

    @staticmethod
    def generate_next_block():
        return Block.generate_next_block_from_remote_coinbas(Transaction.generate_coinbase_transaction(Scorpio.get_pubkey_der(), Scorpio.get_latest_block().index + 1))

    @staticmethod
    def generate_next_block_from_remote_coinbas(coinbase_tx):
        block_data = [coinbase_tx] + Scorpio.get_transaction_pool()
        return Block.generate_raw_next_block(block_data)

    @staticmethod
    def generatenext_block_with_transaction(receiver_address, amount):
        if not Account.is_valid_address(receiver_address):
            raise ValueError('invalid address')

        if type(amount) != int or type(amount) != float:
            raise ValueError('invalid amount')

        coinbase_tx = Transaction.generate_coinbase_transaction(Scorpio.get_pubkey_der(), Scorpio.get_latest_block().index + 1)
        tx = Transaction.create_transaction(receiver_address, amount, Scorpio.privkey_der(), Scorpio.get_unspent_tx_outs(), Scorpio.get_transaction_pool())
        block_data = [coinbase_tx, tx]
        return Block.generate_raw_next_block(block_data)

    @staticmethod
    def find_block(index, previous_hash, current_timestamp_func, transactions, difficulty):
        nonce = 1
        while True:
            current_timestamp = current_timestamp_func()
            _hash = Block.calculate_hash(index, previous_hash, current_timestamp, transactions, difficulty, nonce)
            if Block.hash_matches_difficulty(_hash, difficulty):
                return Block(index, _hash, previous_hash, difficulty, transactions, current_timestamp, nonce)
            nonce +=1

