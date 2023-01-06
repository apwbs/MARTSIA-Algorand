import base64
from algosdk import abi, atomic_transaction_composer, logic
from algosdk.future import transaction
from algosdk.v2client import algod
from algosdk import account
from algosdk import mnemonic
from algosdk.encoding import decode_address, encode_address
import sys
from algosdk.v2client import indexer


creator_mnemonic = "infant flag husband illness gentle palace eye tilt large reopen current purity enemy depart couch moment gate transfer address diamond vital between unlock able cave"
algod_address = "https://betanet-algorand.api.purestake.io/ps2"
algod_token = "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
headers = {
    "X-API-Key": algod_token,
}


indexer_address = "https://betanet-algorand.api.purestake.io/idx2"
indexer_token = ""
indexer_client = indexer.IndexerClient(indexer_token, indexer_address, headers)


def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


def compile_program(client: algod.AlgodClient, source_code: bytes) -> bytes:
    compile_response = client.compile(source_code.decode("utf-8"))
    return base64.b64decode(compile_response["result"])


# Decodes a logged transaction response
def decode_return_value(log, isInt=False):
    if log:
        if isInt:
            return [int.from_bytes(base64.b64decode(s), "big") for s in log]
        return [base64.b64decode(s).decode() for s in log]


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


def call_box_method(app_id: int, authority_private_key, method: abi.Method, args=None):
    client = algod.AlgodClient(algod_token, algod_address, headers)
    sender = account.address_from_private_key(authority_private_key)

    # Initialize ATC to call ABI methods
    atc = atomic_transaction_composer.AtomicTransactionComposer()
    transaction_signer = atomic_transaction_composer.AccountTransactionSigner(
        authority_private_key
    )

    atc.add_method_call(
        app_id,
        method,
        sender,
        client.suggested_params(),
        transaction_signer,
        method_args=args if args else [],
        boxes=[
            (0, decode_address(sender))
        ],  # For the Python SDK, provide a list of (app_id, box_key) tuples you want to access.
    )
    resp = atc.execute(client, 5)

    info = client.pending_transaction_info(resp.tx_ids[0])
    # print(f"Box Txn Info: {info}")

    # Decoded the returned output and print
    if "logs" in info:
        return info["logs"]


def put_box(app_id: int, authority_private_key, values):
    put_method = abi.Method.from_signature("put(string)void")
    print(">> Write into a box...")
    box_return = call_box_method(
        app_id, authority_private_key, put_method, [values]
    )
    print(f"Returned box: {decode_return_value(box_return)}\n")


def read_box(app_id: int, authority_private_key):
    read_method = abi.Method.from_signature("read()void")
    box_return = call_box_method(app_id, authority_private_key, read_method)
    print(decode_return_value(box_return)[0])


def read_specific_box(application_id, box_name):
    application_id = int(application_id)
    box_name = bytes(box_name, 'utf-8')
    box_name = (base64.b64decode(box_name))
    response = indexer_client.application_box_by_name(application_id=application_id, box_name=box_name)
    print(response)


# def length_box(app_id: int):
#     length_method = abi.Method.from_signature("length()void")
#     print(">> Get the length of a box...")
#     box_return = call_box_method(app_id, length_method, b"BoxA")
#     print(f"Length decoded {decode_return_value(box_return, isInt=True)}\n")


# def delete_box(app_id: int):
#     delete_method = abi.Method.from_signature("delete()void")
#     print(">> Deleting a box...")
#     box_return = call_box_method(app_id, delete_method, b"BoxA")
#     print(f"Delete box success: {decode_return_value(box_return, isInt=True)}\n")


def main(params):
    if params[2] == 'put_box':
        put_box(params[3], params[1], params[4])
    if params[2] == 'read_box':
        read_box(params[3], params[1])
    if params[1] == 'read_specific_box':
        read_specific_box(params[2], params[3])


if __name__ == "__main__":
    main(sys.argv)
    # app_id = create_test_app()
    # with open('../../files/process_instance_id.txt', 'w') as piw:
    #     piw.write(str(app_id))
    # print(app_id)
    # app_id = 1387640806
    # fund_program(app_id)
