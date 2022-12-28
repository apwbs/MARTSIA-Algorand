import rsa
from decouple import config
import os
import ipfshttpclient

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
app_id_pk_readers = config('APPLICATION_ID_PK_READERS')

manufacturer_address = config('READER_ADDRESS_MANUFACTURER')
manufacturer_private_key = config('READER_PRIVATEKEY_MANUFACTURER')
electronics_address = config('READER_ADDRESS_SUPPLIER1')
electronics_private_key = config('READER_PRIVATEKEY_SUPPLIER1')
mechanics_address = config('READER_ADDRESS_SUPPLIER2')
mechanics_private_key = config('READER_PRIVATEKEY_SUPPLIER2')

reader_address = electronics_address
private_key = electronics_private_key


def generate_keys():
    (publicKey, privateKey) = rsa.newkeys(1024)
    publicKey_store = publicKey.save_pkcs1().decode('utf-8')
    privateKey_store = privateKey.save_pkcs1().decode('utf-8')

    name_file1 = 'files/keys_readers/private_key_' + str(reader_address) + '.txt'
    with open(name_file1, 'w') as ipfs:
        ipfs.write('reader_address: ' + reader_address + '###')
        ipfs.write(privateKey_store)

    name_file = 'files/keys_readers/public_key_' + str(reader_address) + '.txt'
    with open(name_file, 'w') as ipfs:
        ipfs.write('reader_address: ' + reader_address + '###')
        ipfs.write(publicKey_store)

    new_file = api.add(name_file)
    hash_file = new_file['Hash']
    print(f'ipfs hash: {hash_file}')

    print(os.system('python3.11 blockchain/PublicKeysReadersContract/PKReadersContractMain.py %s %s %s' % (
        private_key, app_id_pk_readers, hash_file)))


if __name__ == "__main__":
    generate_keys()
