import rsa
from decouple import config
import os
import ipfshttpclient
import sqlite3
import io

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

# Connection to SQLite3 reader database
conn = sqlite3.connect('files/reader/reader.db')
x = conn.cursor()


def generate_keys():
    (publicKey, privateKey) = rsa.newkeys(1024)
    publicKey_store = publicKey.save_pkcs1().decode('utf-8')
    privateKey_store = privateKey.save_pkcs1().decode('utf-8')

    f = io.StringIO()
    f.write('reader_address: ' + reader_address + '###')
    f.write(publicKey_store)
    f.seek(0)

    hash_file = api.add_json(f.read())
    print(hash_file)

    x.execute("INSERT OR IGNORE INTO rsa_private_key VALUES (?,?)", (privateKey_store,))
    conn.commit()

    x.execute("INSERT OR IGNORE INTO rsa_public_key VALUES (?,?,?)", (hash_file, publicKey_store))
    conn.commit()

    # name_file1 = 'files/keys_readers/private_key_' + str(reader_address) + '.txt'
    # with open(name_file1, 'w') as ipfs:
    #     ipfs.write('reader_address: ' + reader_address + '###')
    #     ipfs.write(privateKey_store)
    # name_file = 'files/keys_readers/public_key_' + str(reader_address) + '.txt'
    # with open(name_file, 'w') as ipfs:
    #     ipfs.write('reader_address: ' + reader_address + '###')
    #     ipfs.write(publicKey_store)
    # new_file = api.add(name_file)
    # hash_file = new_file['Hash']
    # print(f'ipfs hash: {hash_file}')

    print(os.system('python3.11 blockchain/PublicKeysReadersContract/PKReadersContractMain.py %s %s %s' % (
        private_key, app_id_pk_readers, hash_file)))


if __name__ == "__main__":
    generate_keys()
