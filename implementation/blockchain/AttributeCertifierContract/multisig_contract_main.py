import base64

from algosdk import transaction
from algosdk import account, mnemonic
from algosdk.atomic_transaction_composer import *
from algosdk.v2client import algod
import contract_eeeeh

private_key_1 = "VZtHXj4T2DT2atlThLRuOgPE0n+bj9sO6e/6STgm3Nqrr3giY49gyUtq/fJ5mIPp9S8clJfgy2QhgnBkybRvrg=="
private_key_2 = "v1NEi7llgXaH66aofgHv+/8RW3MsOUmqneWc/Tm97n+IsGQHQS4zOZ6l+p9ezvUDMdxxmmua9TIPXeVfdLjhwg=="
private_key_3 = "nOewRj9MCGANg7oSlpqc6YO+2zl+2SBzp70/W4MlEka9EUkqdHXusgjGprC0u2C3A3HgBeP1AolBuxzUnlwYmw=="
private_key_4 = "9Qekcr0Ba5DV3gm9XrH267zy3xElYlAvv8QArpgEqfMzVNyMgn1/ZBIAuHNkZXusBB3GPeufTH5Z8vNiFvHGog=="

account_1 = account.address_from_private_key(private_key_1)
account_2 = account.address_from_private_key(private_key_2)
account_3 = account.address_from_private_key(private_key_3)
account_4 = account.address_from_private_key(private_key_4)

version = 1  # multisig version
threshold = 2  # how many signatures are necessary
msig = transaction.Multisig(version, threshold, [account_1, account_2])

print("Multisig Address: ", msig.address())

creator_mnemonic = "infant flag husband illness gentle palace eye tilt large reopen current purity enemy depart couch moment gate transfer address diamond vital between unlock able cave"
algod_address = "https://testnet-algorand.api.purestake.io/ps2"
algod_token = "p8IwM35NPv3nRf0LLEquJ5tmpOtcC4he7KKnJ3wE"
headers = {
    "X-API-Key": algod_token,
}

# helper function to compile program source
def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response["result"])


# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


# helper function that formats global state for printing
def format_state(state):
    formatted = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        formatted_key = base64.b64decode(key).decode("utf-8")
        if value["type"] == 1:
            # byte string
            if formatted_key == "voted":
                formatted_value = base64.b64decode(value["bytes"]).decode("utf-8")
            else:
                formatted_value = value["bytes"]
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value["uint"]
    return formatted


# helper function to read app global state
def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = (
        app["params"]["global-state"] if "global-state" in app["params"] else []
    )
    return format_state(global_state)

# create new application
def create_app(
    client, approval_program, clear_program, global_schema, local_schema
):
    # define sender as creator
    sender = msig.address()

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender,
        params,
        on_complete,
        approval_program,
        clear_program,
        global_schema,
        local_schema,
    )

    mtx = transaction.MultisigTransaction(txn, msig)
    mtx.sign(private_key_1)
    mtx.sign(private_key_2)

    # sign transaction
    # signed_txn = txn.sign(private_key)
    tx_id = mtx.transaction.get_txid()

    # send transaction
    client.send_transactions([mtx])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
        print("TXID: ", tx_id)
        print(
            "Result confirmed in round: {}".format(
                transaction_response["confirmed-round"]
            )
        )

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response["application-index"]
    print("Created new app-id:", app_id)

    return app_id


# delete new application
def delete_app(
    client
):
    # define sender as creator
    sender = "GNKNZDECPV7WIEQAXBZWIZL3VQCB3RR55OPUY7SZ6LZWEFXRY2RA5GWXTQ"

    # get node suggested parameters
    params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationDeleteTxn(
        sender,
        params,
        index=162459748
    )

    mtx = transaction.MultisigTransaction(txn, msig)
    mtx.sign(private_key_1)
    mtx.sign(private_key_2)

    # sign transaction
    # signed_txn = txn.sign(private_key)
    tx_id = mtx.transaction.get_txid()

    # send transaction
    client.send_transactions([mtx])

    # # sign transaction
    # signed_txn = txn.sign(private_key_4)
    # tx_id = signed_txn.transaction.get_txid()

    # # send transaction
    # client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 5)
        print("TXID: ", tx_id)
        print(
            "Result confirmed in round: {}".format(
                transaction_response["confirmed-round"]
            )
        )

    except Exception as err:
        print(err)
        return

    # display results
    # transaction_response = client.pending_transaction_info(tx_id)
    # app_id = transaction_response["application-index"]
    # print("Created new app-id:", app_id)

    # return app_id


# call application
def call_app(client, private_key, index, contract):
    # get sender address
    sender = account.address_from_private_key(private_key)
    # create a Signer object
    signer = AccountTransactionSigner(private_key)

    # get node suggested parameters
    sp = client.suggested_params()

    # Create an instance of AtomicTransactionComposer
    atc = AtomicTransactionComposer()
    atc.add_method_call(
        app_id=index,
        method=contract.get_method_by_name("on_save"),
        sender=sender,
        sp=sp,
        signer=signer,
        method_args=[],  # No method args needed here
    )

    # send transaction
    results = atc.execute(client, 2)

    # wait for confirmation
    print("TXID: ", results.tx_ids[0])
    print("Result confirmed in round: {}".format(results.confirmed_round))


def main():
    # initialize an algodClient
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    # # declare application state storage (immutable)
    # local_ints = 0
    # local_bytes = 0
    # global_ints = 2
    # global_bytes = 2
    # global_schema = transaction.StateSchema(global_ints, global_bytes)
    # local_schema = transaction.StateSchema(local_ints, local_bytes)

    # # Compile the program
    # router = contract_eeeeh.getRouter()
    # approval_program, clear_program, contract = router.compile_program(version=6)

    # with open("approval.teal", "w") as f:
    #     f.write(approval_program)

    # with open("clear.teal", "w") as f:
    #     f.write(clear_program)

    # with open("contract.json", "w") as f:
    #     import json

    #     f.write(json.dumps(contract.dictify()))

    # # compile program to binary
    # approval_program_compiled = compile_program(algod_client, approval_program)

    # # compile program to binary
    # clear_state_program_compiled = compile_program(algod_client, clear_program)

    # print("--------------------------------------------")
    # print("Deploying Counter application......")

    # # create new application
    # app_id = create_app(
    #     algod_client,
    #     approval_program_compiled,
    #     clear_state_program_compiled,
    #     global_schema,
    #     local_schema,
    # )

    # # read global state of application
    # print("Global state:", read_global_state(algod_client, app_id))

    app_id = delete_app(
        algod_client,
    )

    # print("Global state:", read_global_state(algod_client, app_id))

    # print("--------------------------------------------")
    # print("Calling Counter application......")
    # call_app(algod_client, creator_private_key, app_id, contract)

    # # read global state of application
    # print("Global state:", read_global_state(algod_client, app_id))

    # print("--------------------------------------------")
    # print("Calling application......")
    # call_app(algod_client, creator_private_key, app_id, contract)

    # # read global state of application
    # print("Global state:", read_global_state(algod_client, app_id))


if __name__ == "__main__":
    main()