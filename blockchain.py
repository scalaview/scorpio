import hashlib
import json

from secp256k1 import PrivateKey, PublicKey
from binascii import hexlify, unhexlify

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

    @staticmethod
    def find_unspent_tx_outs(address, unspent_tx_outs):
        return [tx_out for tx_out in unspent_tx_outs if tx_out.address == address]

    @staticmethod
    def create_tx_outs(receiver_address, from_address, amount, fee=0.01, left_amount=0.00):
        # https://blockchain.info/tx/b657e22827039461a9493ede7bdf55b01579254c1630b0bfc9185ec564fc05ab?format=json
        tx_out = TxOut(receiver_address, amount)
        if left_amount == 0.00:
            return [tx_out]
        else:
            left_tx = TxOut(from_address, left_amount)
            return [tx_out left_tx]

    # https://webbtc.com/tx/a4bfa8ab6435ae5f25dae9d89e4eb67dfa94283ca751f393c1ddc5a837bbc31b
    @staticmethod
    def create_transaction(privkey, receiver_address, amount,
                           unspentTxOuts: UnspentTxOut[], transaction_pool):
        pass

class Block(object):
    def __init__(self, index, hash, prev_hash, difficulty, transactions, timestamp):

        self.index = index
        self.hash = hash
        self.prev_hash = prev_hash
        self.difficulty = difficulty
        self.transactions = transactions
        self.timestamp = timestamp


