from app import db
from sqlalchemy import or_, text
import json
from sqlalchemy.dialects.sqlite import \
            BLOB, BOOLEAN, CHAR, DATE, DATETIME, DECIMAL, FLOAT, \
            INTEGER, NUMERIC, SMALLINT, TEXT, TIME, TIMESTAMP, \
            VARCHAR
import datetime

Column = db.Column
Model = db.Model
String = db.String
fromtimestamp = datetime.datetime.fromtimestamp

class BaseModel(object):
    id = Column(INTEGER, primary_key=True)


class DBBlock(BaseModel, Model):
    __tablename__ = 'blocks'

    index = Column(INTEGER, index=True, nullable=False, unique=True)
    hash = Column(String(64), index=True, nullable=False, unique=True)
    previous_hash = Column(String(64), index=True, nullable=False, unique=True)
    difficulty = Column(INTEGER, nullable=False)
    timestamp = Column(DATETIME, nullable=False)
    nonce = Column(String(64), nullable=False)

    @property
    def transactions(self):
        pass

    @staticmethod
    def build(block):
        return DBBlock(index=block.index, hash=block.hash, \
            previous_hash=block.previous_hash, difficulty=block.difficulty, \
            timestamp=fromtimestamp(block.timestamp), nonce=block.nonce)



class DBTransaction(BaseModel, Model):
    __tablename__ = 'transactions'

    txid = Column(String(64), index=True, nullable=False)
    block_id = Column(INTEGER, index=True, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)

    @property
    def tx_ins(self):
        pass

    @property
    def tx_outs(self):
        pass

    @staticmethod
    def build(block_id, transaction, position):
        return DBTransaction(block_id=block_id, txid=transaction.id, position=position)

class DBTxIn(BaseModel, Model):
    __tablename__ = 'tx_ins'

    transaction_id = Column(INTEGER, index=True, nullable=False)
    signature = Column(String(256), nullable=False)
    tx_out_id = Column(String(64), nullable=False)
    tx_out_index = Column(INTEGER, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)

    @property
    def transaction(self):
        pass

    @staticmethod
    def build(transaction_id, tx_in, position):
        return DBTxIn(transaction_id=transaction_id, signature=tx_in.signature, tx_out_id=tx_in.tx_out_id, tx_out_index=tx_in.tx_out_index, position=position)

class DBTxOut(BaseModel, Model):
    __tablename__ = 'tx_outs'

    transaction_id = Column(INTEGER, index=True, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)
    address = Column(String(64), nullable=False)
    amount = Column(NUMERIC(precision=8, scale=6, asdecimal=False, decimal_return_scale=None), nullable=False)

    @property
    def transaction(self):
        pass

    @staticmethod
    def build(transaction_id, tx_out, position):
        return DBTxOut(transaction_id=transaction_id, address=tx_out.address, amount=tx_out.amount, position=position)
