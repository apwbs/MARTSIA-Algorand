import base64
from algosdk import abi, atomic_transaction_composer, logic
from algosdk import transaction
from algosdk.v2client import algod
from algosdk import account
from algosdk import mnemonic
from algosdk.encoding import decode_address, encode_address
import sys
from algosdk.v2client import indexer
from decouple import config
import argparse
from BoxContract import *

creator_mnemonic = config("CREATOR_MNEMONIC")
algod_address = config("ALGOD_ADDRESS")
algod_token = config("ALGOD_TOKEN")
headers = {
    "X-API-Key": algod_token,
}


indexer_address = "https://testnet-algorand.api.purestake.io/idx2"
indexer_token = ""
indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def compile_program(client: algod.AlgodClient, source_code: bytes) -> bytes:
    compile_response = client.compile(source_code.decode("utf-8"))
    return base64.b64decode(compile_response["result"])


# Creates an app and returns the app ID
def create_test_app() -> int:
    client = algod.AlgodClient(algod_token, algod_address, headers)

    # Declare application state storage (immutable)
    local_ints = 1
    local_bytes = 1
    global_ints = 1
    global_bytes = 1

    # Define app schema
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)
    on_complete = transaction.OnComplete.NoOpOC.real

    # Compile the program with algod
    with open("approve-box.teal", mode="rb") as file:
        source_code = file.read()
    with open("clear-box.teal", mode="rb") as file:
        clear_code = file.read()
    source_program = compile_program(client, source_code)
    clear_program = compile_program(client, clear_code)

    # Prepare the transaction
    params = client.suggested_params()

    senderSK = get_private_key_from_mnemonic(creator_mnemonic)
    sender = account.address_from_private_key(senderSK)

    private_key = senderSK

    # Create an unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        source_program,
        clear_program,
        global_schema,
        local_schema,
    )

    # Sign transaction with funded private key
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])

    transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
    # print(transaction_response)
    app_id = transaction_response["application-index"]
    algod_response = client.application_info(app_id)
    # print(algod_response)
    return app_id


def fund_program(app_id: int):
    client = algod.AlgodClient(algod_token, algod_address, headers)
    senderSK = get_private_key_from_mnemonic(creator_mnemonic)
    sender = account.address_from_private_key(senderSK)
    private_key = senderSK

    # Send transaction to fund the app.
    txn = transaction.PaymentTxn(
        sender,
        client.suggested_params(),
        logic.get_application_address(app_id),
        5_000_000,
    )

    # Sign transaction with funded private key
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # Send transaction
    client.send_transactions([signed_txn])
    _ = transaction.wait_for_confirmation(client, tx_id, 5)

def store_to_env(value, label):
    with open('../../.env', 'r', encoding='utf-8') as file:
        data = file.readlines()
    edited = False
    for line in data:
        if line.startswith(label):
            data.remove(line)
            break
    line = label + "=" + str(value) + "\n"
    #line = "\n" +  label + "=" + value + "\n"
    data.append(line)

    with open('../../.env', 'w', encoding='utf-8') as file:
        file.writelines(data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--firstrun", help="True if this is the first run of the script, False otherwise", action="store_true")
    args = parser.parse_args()
    if args.firstrun:
        app_id = create_test_app()
        print(app_id)
        store_to_env(app_id, 'APPLICATION_ID_BOX')
    else:
        app_id = config("APPLICATION_ID_BOX")
    # Move from crator to box application 5 algos
    fund_program(app_id)