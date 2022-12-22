from algosdk.v2client import indexer
import base64
import time
from decouple import config
import authority1_keygeneration

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')
authority4_address = config('AUTHORITY4_ADDRESS')

indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
indexer_token = ""
headers = {
    "X-API-Key": "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
}

indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)


def generate_key(x):
    gid = base64.b64decode(x['note']).decode('utf-8').split(',')[1]
    process_instance_id = int(base64.b64decode(x['note']).decode('utf-8').split(',')[2])
    reader_address = x['sender']
    key = authority1_keygeneration.generate_user_key(gid, process_instance_id, reader_address)
    print(key)


def transactions_monitoring():
    min_round = 26444819
    transactions = []
    note = 'generate your part of my key'
    while True:
        response = indexer_client.search_transactions_by_address(address=authority1_address, min_round=min_round,
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
