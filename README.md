# scorpio
## A simple blockchain/cryptocurrency implement

### How to run

* Python require >= 3.6.0b1
* generate a secp256k1 keypair yourself or [enumaelish.tk](https://enumaelish.tk)
```shell
pip3 install -r requirements.txt
export export PRIV_KEY="your private key"
python3 manager.py runserver
```
### What next
you can mine some block yourself
```shell
python3 manager.py mine -n 'https://yournodedomain'
#for example 
python3 manager.py mine -n 'https://enumaelish.tk'
```

### Api
#### get all blocks
##### GET /blocks
```json
{
    "data": [
        {
            "difficulty": 0,
            "hash": "d7b59f69ece171eceaccd18a79b297f1.....",
            "index": 0,
            "nonce": 0,
            "previous_hash": "",
            "timestamp": 1523026288,
            "transactions": [
                {
                    "id": "8e7b7a29be988415d9634....",
                    "tx_ins": [
                        {
                            "signature": "...",
                            "tx_out_id": "...",
                            "tx_out_index": 0
                        }
                    ],
                    "tx_outs": [
                        {
                            "address": "02e525a9b78192e0a589a0ef74fc053ec9....",
                            "amount": 50
                        }
                    ]
                }
            ]
        }
    ],
    "err": 0,
    "message": "success"
}
```
### post a block data to a node
#### POST /block, only accept 'application/json'
require params:

* block

```json
//POST data sample
    {
            "difficulty": 0,
            "hash": "d7b59f69ece171eceaccd18a79b297f1.....",
            "index": 0,
            "nonce": 0,
            "previous_hash": "",
            "timestamp": 1523026288,
            "transactions": [
                {
                    "id": "8e7b7a29be988415d9634....",
                    "tx_ins": [
                        {
                            "signature": "....",
                            "tx_out_id": "....",
                            "tx_out_index": 0
                        }
                    ],
                    "tx_outs": [
                        {
                            "address": "02e525a9b78192e0a589a0ef74fc053ec9....",
                            "amount": 50
                        }
                    ]
                }
            ]
        }
```
### Get the latest block data
#### GET /latest_block

### Get a special block data
#### GET /block/:hash

### Get a sepecial transaction
#### GET /transaction/:id
```json
{
    "data": [
        {
            "id": "28022e9fe3c82fbb25498cd5b33bdd......",
            "tx_ins": [
                {
                    "signature": "3045022100e054f7ff334a1709461a440...",
                    "tx_out_id": "8e7b7a29be988415d963417a428b26e718f3fcffe9ccc8e402bf9423f960b2a8",
                    "tx_out_index": 0
                }
            ]
            ...
        }
    ],
}
```

### Get unspent output tx from one address
#### GET /address/:address

### Get all unspent out put tx
#### GET /unspent_transaction_outputs

### Get balance from an address
#### GET /balance/:address


### Send transaction
#### POST /send_transaction
require params:

* String: address (addree you want to send, receive address)
* Float: amount
* String: privkey

### Get all transactions
#### GET /transaction_pool

### register your node to an existing node
#### POST /add_peer

require params:

* url


## License
[MIT](http://opensource.org/licenses/MIT)

Copyright (c) 2019-present, Benko bin
