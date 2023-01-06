from decouple import config
import os
from Crypto.PublicKey import RSA
from hashlib import sha512
import ipfshttpclient

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
app_id_pk_readers = config('APPLICATION_ID_PK_READERS')

manufacturer_address = config('READER_ADDRESS_MANUFACTURER')
manufacturer_private_key = config('READER_PRIVATEKEY_MANUFACTURER')
electronics_address = config('READER_ADDRESS_SUPPLIER1')
electronics_private_key = config('READER_PRIVATEKEY_SUPPLIER1')
mechanics_address = config('READER_ADDRESS_SUPPLIER2')
mechanics_private_key = config('READER_PRIVATEKEY_SUPPLIER2')

reader_address = manufacturer_address
private_key = manufacturer_private_key


def generate_keys():
    keyPair = RSA.generate(bits=1024)
    print(f"Public key:  (n={hex(keyPair.n)}, e={hex(keyPair.e)})")
    print(f"Private key: (n={hex(keyPair.n)}, d={hex(keyPair.d)})")

    name_file1 = 'files/keys_readers/handshake_private_key_' + str(reader_address) + '.txt'
    with open(name_file1, 'w') as ipfs:
        ipfs.write('reader_address: ' + reader_address + '###')
        ipfs.write(str(keyPair.n) + '###' + str(keyPair.d))

    name_file = 'files/keys_readers/handshake_public_key_' + str(reader_address) + '.txt'
    with open(name_file, 'w') as ipfs:
        ipfs.write('reader_address: ' + reader_address + '###')
        ipfs.write(str(keyPair.n) + '###' + str(keyPair.e))

    new_file = api.add(name_file)
    hash_file = new_file['Hash']
    print(f'ipfs hash: {hash_file}')

    print(os.system('python3.11 blockchain/PublicKeysReadersContract/PKReadersContractMain.py %s %s %s' % (
        private_key, app_id_pk_readers, hash_file)))


if __name__ == "__main__":
    generate_keys()