import json
from datetime import datetime
import random
from decouple import config
import ipfshttpclient
import os
import validator
import sys

sys.path.insert(0, 'blockchain/BoxContract/')
from blockchain.BoxContract import BoxContractMain

app_id_attribute = config('APPLICATION_ID_CERTIFIER')
certifier_private_key = config('CERTIFIER_PRIVATEKEY')


def generate_attributes():
    # now = datetime.now()
    # now = int(now.strftime("%Y%m%d%H%M%S%f"))
    # random.seed(now)
    # process_instance_id = random.randint(1, 2 ** 64)
    # print(f'process instance id: {process_instance_id}')
    #
    # with open('files/process_instance_id.txt', 'w') as piw:
    #     piw.write(str(process_instance_id))

    with open('files/process_instance_id.txt', 'r') as cir:
        process_instance_id = cir.read()

    dict_users = {
        '7M5UN2VQJV6GW7V43XZ2KGF5TIOHOTQ3OYQXDPZAQLZQFYQXU5FOJJHVMU': [str(process_instance_id) + '@UT',
                                                                       str(process_instance_id) + '@OU', 'STUDENT@UT',
                                                                       'PHD@UT', 'STUDENT@OU', 'STUDENT@OT']
    }

    # api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    # dict_users_dumped = json.dumps(dict_users)
    # name_file = 'files/users_attributes.txt'
    # with open(name_file, 'w') as ua:
    #     # ua.write('process instance id: ' + str(process_instance_id) + '\n')
    #     ua.write(dict_users_dumped)
    # new_file = api.add(name_file)
    # hash_file = new_file['Hash']
    # print(f'ipfs hash: {hash_file}')

    # print(os.system('python3.11 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py %s %s %s
    # %s' % ( certifier_private_key, app_id_attribute, process_instance_id, hash_file)))

    # signature = validator.verify(hash_file)
    #
    # element_0 = hash_file + '#' + signature
    # print(element_0)

    app_id = BoxContractMain.create_test_app()
    BoxContractMain.create_box(app_id)


if __name__ == "__main__":
    generate_attributes()
