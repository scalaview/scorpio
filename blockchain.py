



class Block(object):
  def __init__(self, index, hash, prev_hash, difficulty, transactions, timestamp):

    self.index = index
    self.hash = hash
    self.prev_hash = prev_hash
    self.difficulty = difficulty
    self.transactions = transactions
    self.timestamp = timestamp


