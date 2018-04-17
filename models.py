from app import db
from sqlalchemy import or_, text, and_
import json
from sqlalchemy.dialects.sqlite import \
            BLOB, BOOLEAN, CHAR, DATE, DATETIME, DECIMAL, FLOAT, \
            INTEGER, NUMERIC, SMALLINT, TEXT, TIME, TIMESTAMP, \
            VARCHAR
from sqlalchemy import func
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
        return DBTransaction.query.filter_by(block_id=self.id).order_by(DBTransaction.position).all()

    @staticmethod
    def build(block):
        return DBBlock(index=block.index, hash=block.hash, \
            previous_hash=block.previous_hash, difficulty=block.difficulty, \
            timestamp=fromtimestamp(block.timestamp), nonce=block.nonce)

    @staticmethod
    def batch_all(start=0, offet=500, func=None, condition=None):
        total = DBBlock.query.filter(DBBlock.index>0).count()
        total_dbblocks = []
        for chunkstart in range(start, total, offet):
            if condition:
                dbblocks = DBBlock.query.filter(condition).order_by(DBBlock.index).offset(chunkstart).limit(offet).all()
            else:
                dbblocks = DBBlock.query.order_by(DBBlock.index).offset(chunkstart).limit(offet).all()
            if func is not None:
                func(dbblocks)
            total_dbblocks = total_dbblocks + dbblocks
        return total_dbblocks

    @staticmethod
    def get_latest_block():
        total = db.session.query(func.max(DBBlock.index).label('max_index')).one().max_index
        return DBBlock.query.filter_by(index=total).first()

    @staticmethod
    def get_blockchain():
        return DBBlock.batch_all()

    @staticmethod
    def update_unspent_tx_outs(transactions):
        for transaction in transactions:
            for tx_in in transaction.tx_ins:
                prepare_tx_out = DBUnspentTxOut.query.filter_by(tx_out_id=tx_in.tx_out_id).filter_by(tx_out_index=tx_in.tx_out_index).first()
                if prepare_tx_out:
                    db.session.delete(prepare_tx_out)
            db.session.commit()
            for index, tx_out in enumerate(transaction.tx_outs):
                db.session.add(DBUnspentTxOut(tx_out_id=transaction.id, tx_out_index=index, address=tx_out.address, amount=tx_out.amount))
            db.session.commit()
        return DBUnspentTxOut.unspent_tx_outs()


class DBTransaction(BaseModel, Model):
    __tablename__ = 'transactions'

    txid = Column(String(64), index=True, nullable=False)
    block_id = Column(INTEGER, index=True, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)

    @property
    def tx_ins(self):
        return DBTxIn.query.filter_by(transaction_id=self.id).order_by(DBTxIn.position).all()

    @property
    def tx_outs(self):
        return DBTxOut.query.filter_by(transaction_id=self.id).order_by(DBTxOut.position).all()

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

    @staticmethod
    def build(transaction_id, tx_out, position):
        return DBTxOut(transaction_id=transaction_id, address=tx_out.address, amount=tx_out.amount, position=position)


class DBUnspentTxOut(BaseModel, Model):
    __tablename__ = 'unspent_tx_out'

    tx_out_id = Column(String(64), index=True, nullable=True)
    tx_out_index = Column(INTEGER, index=True, nullable=True)
    address = Column(String(64), index=False, nullable=True)
    amount = Column(NUMERIC(precision=8, scale=6, asdecimal=False, decimal_return_scale=None), nullable=False)

    @staticmethod
    def unspent_tx_outs():
        total = DBUnspentTxOut.query.count()
        total_dbunspent_tx_outs = []
        for chunkstart in range(0, total, 1000):
            dbunspent_tx_outs = DBUnspentTxOut.query.offset(chunkstart).limit(offet).all()
            total_dbunspent_tx_outs = total_dbunspent_tx_outs + dbunspent_tx_outs
        return total_dbunspent_tx_outs

    @staticmethod
    def has_tx_in(tx_in):
        return db.session.query(db.exists().where(DBUnspentTxOut.tx_out_id == tx_in.tx_out_id)).where(DBUnspentTxOut.tx_out_index == tx_in.tx_out_index).scalar()


