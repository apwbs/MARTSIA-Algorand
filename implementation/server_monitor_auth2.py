from algosdk.v2client import indexer
import base64
import time
from decouple import config
import authority2_keygeneration
import rsa
import json
import retriever
from algosdk.v2client import algod
from algosdk import mnemonic, account
from algosdk.future.transaction import PaymentTxn
import ipfshttpclient
import io

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
app_id_pk_readers = config('APPLICATION_ID_PK_READERS')

authority2_address = config('AUTHORITY2_ADDRESS')
authority2_mnemonic = config('AUTHORITY2_MNEMONIC')

indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
indexer_token = ""
headers = {
    "X-API-Key": "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
}

indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)

algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
headers = {
    "X-API-Key": algod_token,
}


creator_mnemonic = authority2_mnemonic


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def send_ipfs_link(reader_address, process_instance_id, hash_file):
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    private_key = get_private_key_from_mnemonic(creator_mnemonic)
    my_address = account.address_from_private_key(private_key)
    print("My address: {}".format(my_address))
    params = algod_client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    # params.flat_fee = True
    # params.fee = 1000
    note = hash_file + ',' + str(process_instance_id)
    note_encoded = note.encode()
    receiver = reader_address

    unsigned_txn = PaymentTxn(my_address, params, receiver, 0, None, note_encoded)

    # sign transaction
    signed_txn = unsigned_txn.sign(private_key)

    # send transaction
    txid = algod_client.send_transaction(signed_txn)
    print("Send transaction with txID: {}".format(txid))


def generate_key(x):
    gid = base64.b64decode(x['note']).decode('utf-8').split(',')[1]
    process_instance_id = int(base64.b64decode(x['note']).decode('utf-8').split(',')[2])
    reader_address = x['sender']
    key = authority2_keygeneration.generate_user_key(gid, process_instance_id, reader_address)
    cipher_generated_key(reader_address, process_instance_id, key)


def cipher_generated_key(reader_address, process_instance_id, generated_ma_key):
    public_key_ipfs_link = retriever.retrieveReaderPublicKey(app_id_pk_readers, reader_address)
    getfile = api.cat(public_key_ipfs_link)
    getfile = getfile.split(b'###')
    if getfile[0].split(b': ')[1].decode('utf-8') == reader_address:
        publicKey_usable = rsa.PublicKey.load_pkcs1(getfile[1].rstrip(b'"').replace(b'\\n', b'\n'))

        info = [generated_ma_key[i:i + 117] for i in range(0, len(generated_ma_key), 117)]

        f = io.BytesIO()
        for part in info:
            crypto = rsa.encrypt(part, publicKey_usable)
            f.write(crypto)
        f.seek(0)

        file_to_str = f.read()
        j = base64.b64encode(file_to_str).decode('ascii')
        s = json.dumps(j)
        hash_file = api.add_json(s)
        print(hash_file)

        send_ipfs_link(reader_address, process_instance_id, hash_file)


def transactions_monitoring():
    min_round = 27669863
    transactions = []
    note = 'generate your part of my key'
    while True:
        response = indexer_client.search_transactions_by_address(address=authority2_address, min_round=min_round,
                                                                 txn_type='pay', max_amount=0)
        for tx in response['transactions']:
            if tx['id'] not in transactions and 'note' in tx:
                if base64.b64decode(tx['note']).decode('utf-8').split(',')[0] == note:
                    transactions.append(tx)
        min_round = min_round + 1
        for x in transactions:
            generate_key(x)
            transactions.remove(x)
        time.sleep(5)


if __name__ == "__main__":
    transactions_monitoring()
