from PKReadersContract import *
from algosdk.atomic_transaction_composer import AtomicTransactionComposer
from algosdk.abi import Method, Contract
import sys
import base64
from algosdk import account

algod_address = config("ALGOD_ADDRESS")
algod_token = config("ALGOD_TOKEN")
headers = {
    "X-API-Key": algod_token,
}

def get_method(name: str, js: str) -> Method:
    c = Contract.from_json(js)
    for m in c.methods:
        if m.name == name:
            return m
    raise Exception("No method with the name {}".format(name))

def format_state(state):
    formatted = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        formatted_key = base64.b64decode(key).decode("utf-8")
        if value["type"] == 1:
            formatted_value = base64.b64decode(value["bytes"])
            if formatted_key == 'authorityAddress':
                formatted[formatted_key] = encode_address(formatted_value)
            else:
                formatted[formatted_key] = formatted_value
        else:
            formatted[formatted_key] = value["uint"]
    return formatted


def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = (
        app["params"]["global-state"] if "global-state" in app["params"] else []
    )
    return format_state(global_state)


def saveData(
        client: algod.AlgodClient,
        creator: str,
        app_id: int,
        ipfs_link: str,
) -> None:
    atc = AtomicTransactionComposer()
    signer = AccountTransactionSigner(creator)
    sp = client.suggested_params()

    app_args = [
        ipfs_link
    ]

    with open("blockchain/Controlled/multisig/PublicKeysReadersContract/pk_readers_contract.json") as f:
        js = f.read()
    
    atc.add_method_call(
        app_id=app_id,
        method=get_method('on_save', js),
        sender=account.address_from_private_key(creator),
        sp=sp,
        signer=signer,
        method_args=app_args
    )

    result = atc.execute(client, 10)

    print("Transaction id:", result.tx_ids[0])

    print("Global state:", read_global_state(client, app_id))


def main(params):
    creator_private_key = params[1]

    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    print("--------------------------------------------")
    print("Saving reader public key in the application......")
    print('Im using this one')
    app_id = params[2]
    ipfs_link = params[3]
    saveData(algod_client, creator_private_key, app_id, ipfs_link)


if __name__ == "__main__":
    main(sys.argv)
    