from algosdk.atomic_transaction_composer import *
from pyteal import *
from decuple import config

algod_address = config("ALGOD_ADDRESS")
algod_token = config("ALGOD_TOKEN")
headers = {
    "X-API-Key": algod_token,
}


READER_ADDRESS_MANUFACTURER= config("DATAOWNER_MANUFACTURER_ADDRESS")
READER_PRIVATEKEY_MANUFACTURER= config("DATAOWNER_MANUFACTURER_PRIVATEKEY")

READER_ADDRESS_SUPPLIER1= config("READER_SUPPLIER1_ADDRESS")
READER_PRIVATEKEY_SUPPLIER1= config("READER_SUPPLIER2_PRIVATEKEY")
READER_ADDRESS_SUPPLIER2= config("READER_SUPPLIER2_ADDRESS")
READER_PRIVATEKEY_SUPPLIER2= config("READER_SUPPLIER2_PRIVATEKEY")

def main():
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)

    address=READER_ADDRESS_SUPPLIER2
    private_key=READER_PRIVATEKEY_SUPPLIER2
    app_id=248937298

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