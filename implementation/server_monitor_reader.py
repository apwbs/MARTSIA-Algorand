from algosdk.v2client import indexer
import base64
import time
from decouple import config
import rsa
import ipfshttpclient

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')
authority4_address = config('AUTHORITY4_ADDRESS')

manufacturer_address = config('READER_ADDRESS_MANUFACTURER')
electronics_address = config('READER_ADDRESS_SUPPLIER1')
mechanics_address = config('READER_ADDRESS_SUPPLIER2')

indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
indexer_token = ""
headers = {
    "X-API-Key": "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
}

indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)


def retrieve_key(transaction):
    if transaction['sender'] == authority4_address:
        partial = base64.b64decode(transaction['note']).decode('utf-8').split(',')
        process_instance_id = partial[1]
        ipfs_link = partial[0]
        getfile = api.cat(ipfs_link)

        info2 = [getfile[i:i + 128] for i in range(0, len(getfile), 128)]
        final_bytes = b''

        with open('files/keys_readers/private_key_' + str(electronics_address) + '.txt', 'rb') as sk1r:
            sk1 = sk1r.read()
        sk1 = sk1.split(b'###')[1]
        privateKey_usable = rsa.PrivateKey.load_pkcs1(sk1)

        for j in info2:
            message = rsa.decrypt(j, privateKey_usable)
            final_bytes = final_bytes + message

        with open('files/reader/user_sk4_' + str(process_instance_id) + '.txt', "wb") as text_file:
            text_file.write(final_bytes)

        print('key retrieved')


def transactions_monitoring():
    min_round = 26454090
    transactions = []
    while True:
        response = indexer_client.search_transactions_by_address(address=electronics_address, min_round=min_round,
                                                                 txn_type='pay', max_amount=0)
        for tx in response['transactions']:
            if tx['id'] not in transactions and 'note' in tx:
                transactions.append(tx)
        min_round = min_round + 1
        for x in transactions:
            retrieve_key(x)
            transactions.remove(x)
        time.sleep(5)


if __name__ == "__main__":
    transactions_monitoring()
