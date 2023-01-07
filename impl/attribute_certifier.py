import json
from decouple import config
import ipfshttpclient
import os
import io
import sqlite3

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

app_id_box = config('APPLICATION_ID_BOX')
app_id_certifier = config('APPLICATION_ID_CERTIFIER')
certifier_private_key = config('CERTIFIER_PRIVATEKEY')

manufacturer_address = config('READER_ADDRESS_MANUFACTURER')
supplier1_address = config('READER_ADDRESS_SUPPLIER1')
supplier2_address = config('READER_ADDRESS_SUPPLIER2')

# Connection to SQLite3 attribute_certifier database
conn = sqlite3.connect('files/attribute_certifier/attribute_certifier.db')
x = conn.cursor()


def generate_attributes():
    process_instance_id = int(app_id_box)

    dict_users = {
        manufacturer_address:   [str(process_instance_id) + '@UT', str(process_instance_id) + '@OU',
                                 str(process_instance_id) + '@OT', str(process_instance_id) + '@TU', 'MANUFACTURER@UT'],

        supplier1_address:      [str(process_instance_id) + '@UT', str(process_instance_id) + '@OU',
                                 str(process_instance_id) + '@OT', str(process_instance_id) + '@TU', 'SUPPLIER@OU',
                                 'ELECTRONICS@OT'],

        supplier2_address:      [str(process_instance_id) + '@UT', str(process_instance_id) + '@OU',
                                 str(process_instance_id) + '@OT', str(process_instance_id) + '@TU', 'SUPPLIER@OU',
                                 'MECHANICS@TU']
    }

    f = io.StringIO()
    dict_users_dumped = json.dumps(dict_users)
    f.write('"process_instance_id": ' + str(process_instance_id) + '####')
    f.write(dict_users_dumped)
    f.seek(0)

    file_to_str = f.read()

    hash_file = api.add_json(file_to_str)
    print(f'ipfs hash: {hash_file}')
    # QmPrZQgoZY9MruZkiHTmfLRRCouXcGZzuxpHpsXY43uQEH

    x.execute("INSERT OR IGNORE INTO user_attributes VALUES (?,?,?)", (process_instance_id, hash_file, file_to_str))
    conn.commit()

    # dict_users_dumped = json.dumps(dict_users)
    # name_file = 'files/users_attributes_' + str(process_instance_id) + '.txt'
    # # there is no need to save the file locally
    # with open(name_file, 'w') as ua:
    #     ua.write('"process_instance_id": ' + str(process_instance_id) + '\n')
    #     ua.write(dict_users_dumped)
    # new_file = api.add(name_file)
    # hash_file = new_file['Hash']
    # print(f'ipfs hash: {hash_file}')

    print(os.system('python3.11 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py %s %s %s %s' %
                    (certifier_private_key, app_id_certifier, process_instance_id, hash_file)))

    # g = io.StringIO()
    # g.write('mandi')
    # g.seek(0)
    # hash_file = api.add_json(g.read())
    # print(f'ipfs hash: {hash_file}')
    # print(os.system('python3.11 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py %s %s %s %s' %
    #                 (certifier_private_key, app_id_certifier, 12311111111111, hash_file)))


if __name__ == "__main__":
    generate_attributes()
