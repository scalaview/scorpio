import hashlib
import json
import logging
from secp256k1 import PrivateKey, PublicKey
from binascii import hexlify, unhexlify
from functools import reduce

BLOCK_GENERATION_INTERVAL = 10

DIFFICULTY_ADJUSTMENT_INTERVAL = 10

# privkey = PrivateKey(unhexlify('a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'))
# compressed = hexlify(privkey.pubkey.serialize()).decode('ascii')
# uncompressed = hexlify(privkey.pubkey.serialize(compressed=False)).decode('ascii')
# print(compressed)
# print(uncompressed)


class Scorpio(object):

    def __init__(self):
        pass

    @staticmethod
    def getDifficulty(blocks):
        latest_block = blocks[-1]
        if latest_block.index % DIFFICULTY_ADJUSTMENT_INTERVAL == 0 and latest_block.index != 0:
            return adjust_difficulty(blocks)
        else:
            return latest_block.difficulty

    @staticmethod
    def adjust_difficulty(blocks):
        if len(blocks) > DIFFICULTY_ADJUSTMENT_INTERVAL:
            latest_block = blocks[-1]
            prev_adjusted_block = blocks[-BLOCK_GENERATION_INTERVAL]
            expected_cost = BLOCK_GENERATION_INTERVAL * DIFFICULTY_ADJUSTMENT_INTERVAL
            spend_time = latest_block.timestamp - prev_adjusted_block.timestamp
            if spend_time > expected_cost * 1.5 :
                return prev_adjusted_block.difficulty - 1
            elif spend_time < expected_cost / 2 :
                return prev_adjusted_block.difficulty + 1
            else:
                return prev_adjusted_block.difficulty


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
        pass

    def sign(self, data):
        return hexlify(self.privkey.ecdsa_sign(bytes(bytearray.fromhex(data)), raw=True)).decode('ascii')

    @staticmethod
    def find_unspent_tx_outs(address, unspent_tx_outs):
        return [tx_out for tx_out in unspent_tx_outs if tx_out.address == address]


    @staticmethod
    def create_transation_tx_outs(receiver_address, amount, from_address, left_amount):
        if left_amount == 0.00:
            return [TxOut(receiver_address, amount)]
        else:
            return [TxOut(receiver_address, amount), TxOut(from_address, left_amount)]

    # https://webbtc.com/tx/a4bfa8ab6435ae5f25dae9d89e4eb67dfa94283ca751f393c1ddc5a837bbc31b
    @staticmethod
    def create_transaction(privkey, receiver_address, amount, unspent_tx_outs, transaction_pool):
        account = Account(privkey)
        available_tx_outs = [ tx_out for tx_out in unspent_tx_outs if tx_out.address == account.pubkey_der ]
        tx_ins = [ tx_in for transction in transaction_pool for tx_in in transction.tx_ins]

        # from itertools import filterfalse
        # available_tx_outs[:] = filterfalse(lambda tx_out:  , available_tx_outs)
        for tx_out in available_tx_outs:
            tx_in = None
            for _tx_in in tx_ins:
                if _tx_in.tx_out_index == tx_out.tx_out_index and _tx_in.tx_out_id == tx_out.tx_out_id:
                    tx_in = _tx_in
            if tx_in is not None:
                available_tx_outs.remove(tx_in)

        is_enough, prepare_tx_outs, left_amount = Account.is_enough(amount, available_tx_outs)
        if is_enough:
            tx = Transaction()
            tx.tx_ins = list(map(Account.unsigned_tx_in, prepare_tx_outs))
            tx.tx_outs = Account.create_transation_tx_outs(receiver_address, amount, account.pubkey_der, left_amount)
            tx.gene_transaction_id()
            tx.sign_tx_ins(account)
            return tx
        else:
            raise ValueError( "amount: {%0.6f} not enough from unspent_tx_outs: %s " % amount, json.dumps(available_tx_outs))


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


class TxIn(object):
    def __init__(self):
        self.tx_out_id = None
        self.tx_out_index = None
        self.signature = None

    def validate(self, transaction, unspent_tx_outs):
        utx_out = unspent_tx_out for unspent_tx_out in unspent_tx_outs if unspent_tx_out.tx_out_id == self.tx_out_id and unspent_tx_out.tx_out_index == self.tx_out_index
        if utx_out is None:
            return False
        pubkey = PublicKey(utx_out.address, raw=True)
        if not pubkey.ecdsa_verify(bytes(bytearray.fromhex(transaction.id)), sig):
            return False
        return True


class TxOut(object):
    def __init__(self, address, amount):
        self.address = address
        self.amount = amount


class UnspentTxOut(object):
    def __init__(self, tx_out_id, tx_out_index, address, amount):
        self.tx_out_id = tx_out_id
        self.tx_out_index = tx_out_index
        self.address = address
        self.amount = amount


class Transaction(object):
    def __init__(self, arg):
        self.id = None
        self.tx_ins = []
        self.tx_outs = []

    @staticmethod
    def _gene_transaction_id(transaction):
        tx_in_str = reduce((lambda x, y: x+y), list(map( (lambda tx_in: tx_in.tx_out_id + str(tx_in.tx_out_index)), transaction.tx_ins)))
        tx_out_str = reduce((lambda x, y: x+y), list(map( (lambda tx_in: ( "%s{%0.6f}" % (tx_in.address, tx_in.amount) )), transaction.tx_outs)))

        return hashlib.sha256(tx_in_str+tx_out_str).hexdigest()

    def gene_transaction_id(self):
        self.id = Transaction._gene_transaction_id(self)

    def sign_tx_ins(self, account):
        for tx_in in self.tx_ins:
            tx_in.signature = account.sign(self.id)

    def validate(self, unspent_tx_outs):
        # check
        if self.gene_transaction_id() != self.id:
            return False
        for tx_in in self.tx_ins:
            if not tx_in.validate(self, unspent_tx_outs):
                return False
        total_tx_in_amount = 0.0
        for tx_in in self.tx_ins:
            result = Account.find_unspent_tx_outs(tx_in, unspent_tx_outs)
            if result is not None:
                total_tx_in_amount += result.amount
        total_tx_out_amount = 0.0
        for tx_out in self.tx_outs:
            total_tx_out_amount += tx_out.amount
        if total_tx_in_amount != total_tx_out_amount:
            return False

        return True

    def validate_transaction_id(self):
        self.id == Transaction._gene_transaction_id(self)

    def is_reward(self, block_index):
        if not self.validate_transaction_id():
            return False
        if len(self.tx_ins) != 1:
            return False
        if len(self.tx_outs) != 1:
            return False
        if self.tx_ins[0] and self.tx_ins[0].tx_out_index != block_index:
            return False
        if self.tx_outs[0] and self.tx_outs[0].amount !== Block.reward():
            return False
        return True


class Block(object):

    @staticmethod
    def reward():
        return 20

    def __init__(self, index, hash, prev_hash, difficulty, transactions, timestamp):

        self.index = index
        self.hash = hash
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.transactions = transactions
        self.timestamp = timestamp

    @staticmethod
    def validate(transactions, unspent_tx_outs, block_index):
        if not Block.validate_reward_transaction(transactions[0], block_index):
            logging.error("invalid reward transaction: %s" % json.dumps(transactions[0]))

        # check uniq tx in


    @staticmethod
    def validate_reward_transaction(transaction, index):
        if transaction is None:
            logging.error("the first transaction must be the reward transaction")
            return False

        if not transaction.is_reward(index):
            return False

        return True



