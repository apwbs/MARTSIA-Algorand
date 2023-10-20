from algosdk.atomic_transaction_composer import *
from pyteal import *
from decuple import config

algod_address = config("ALGOD_ADDRESS")
algod_token = config("ALGOD_TOKEN")
headers = {
    "X-API-Key": algod_token,
}

DATAOWNER_ADDRESS = config("DATAOWNER_MANUFACTURER_ADDRESS")
DATAOWNER_PRIVATEKEY = config("DATAOWNER_MANUFACTURER_PRIVATEKEY")

def main():
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    address=DATAOWNER_ADDRESS
    private_key=DATAOWNER_PRIVATEKEY
    app_id=239586147

    txn = transaction.ApplicationOptInTxn(
        sender=address,
        index=app_id,
        sp=algod_client.suggested_params(),
    )
    signedTxn = txn.sign(private_key)
    algod_client.send_transaction(signedTxn)
    transaction.wait_for_confirmation(algod_client, signedTxn.get_txid())


if __name__ == "__main__":
    main()