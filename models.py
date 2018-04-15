from . import db
from sqlalchemy import or_, text
import json
from sqlalchemy.dialects.sqlite import \
            BLOB, BOOLEAN, CHAR, DATE, DATETIME, DECIMAL, FLOAT, \
            INTEGER, NUMERIC, SMALLINT, TEXT, TIME, TIMESTAMP, \
            VARCHAR

Column = db.Column
Model = db.Model
String = db.String

class BaseModel(object):
    id = Column(INTEGER, primary_key=True)


class DBBlock(BaseModel, Model)
    __tablename__ = 'blocks'

    index = Column(INTEGER, index=True, nullable=False)
    hash = Column(String(64), index=True, nullable=False)
    previous_hash = Column(String(64), index=True, nullable=False)
    difficulty = Column(INTEGER, nullable=False)
    timestamp = Column(DATETIME, nullable=False)
    nonce = Column(String(64), nullable=False)

    @property
    def transactions(self):
        pass


class DBTransaction(BaseModel, Model):
    __tablename__ = 'transactions'

    tid = Column(String(64), index=True, nullable=False)
    block_id = Column(INTEGER, index=True, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)

    @property
    def tx_ins(self):
        pass

    @property
    def tx_outs(self):
        pass


class DBTxIn(object, Model):
    __tablename__ = 'tx_ins'

    transaction_id = Column(INTEGER, index=True, nullable=False)
    signature = Column(String(256))
    tx_out_id = Column(String(64), nullable=False)
    tx_out_index = Column(INTEGER, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)

    @property
    def transaction(self):
        pass

class DBTxOut(object, Model):
    __tablename__ = 'tx_outs'

    transaction_id = Column(INTEGER, index=True, nullable=False)
    position = Column(INTEGER, index=True, nullable=False)
    address = Column(String(64), nullable=False)
    amount = Column(Numeric(precision=8, scale=6, asdecimal=False, decimal_return_scale=None), nullable=False)

    @property
    def transaction(self):
        pass

