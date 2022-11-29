from charm.toolbox.pairinggroup import *
from charm.core.engine.util import objectToBytes, bytesToObject
import cryptocode
from decouple import config
import ipfshttpclient
import json
from maabe_class import *
from datetime import datetime
import random
import os
import sys

sys.path.insert(0, 'blockchain/')
from blockchain.retreiver import *

app_id_public_parameters = config('APPLICATION_ID_PUBLIC_PARAMETERS')
app_id_public_keys = config('APPLICATION_ID_PUBLIC_KEYS')
app_id_messages = config('APPLICATION_ID_MESSAGES')

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
data_owner_private_key = config('DATAOWNER_PRIVATEKEY')


def retrieve_public_parameters():
    with open('files/data_owner/public_parameters_dataowner1.txt', 'rb') as ppr:
        public_parameters1 = ppr.read()
    with open('files/data_owner/public_parameters_dataowner2.txt', 'rb') as ppr:
        public_parameters2 = ppr.read()
    with open('files/data_owner/public_parameters_dataowner3.txt', 'rb') as ppr:
        public_parameters3 = ppr.read()
    if public_parameters1 == public_parameters2 == public_parameters3:
        return public_parameters1


def main(groupObj, maabe, api, process_instance_id):
    response = retrieve_public_parameters()
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    with open('files/data_owner/public_key_auth1.txt', 'rb') as pk1r:
        pk1 = pk1r.read()
    pk1 = bytesToObject(pk1, groupObj)

    with open('files/data_owner/public_key_auth2.txt', 'rb') as pk2r:
        pk2 = pk2r.read()
    pk2 = bytesToObject(pk2, groupObj)

    with open('files/data_owner/public_key_auth3.txt', 'rb') as pk3r:
        pk3 = pk3r.read()
    pk3 = bytesToObject(pk3, groupObj)

    # public keys authorities
    pk = {'UT': pk1, 'OU': pk2, 'OT': pk3}

    f = open('files/data.json')
    data = json.load(f)
    access_policy = ['(STUDENT@UT and STUDENT@OU and STUDENT@OT)',
                     '(STUDENT@UT and MASTERS@OU)']

    entries = [['ID', 'SortAs', 'GlossTerm'], ['Acronym', 'Abbrev']]

    keys = []
    header = []
    for i in range(len(entries)):
        key_group = groupObj.random(GT)
        key_encrypt = groupObj.serialize(key_group)
        keys.append(key_encrypt)
        key_encrypt_deser = groupObj.deserialize(key_encrypt)

        ciphered_key = maabe.encrypt(public_parameters, pk, key_encrypt_deser, access_policy[i])
        ciphered_key_bytes = objectToBytes(ciphered_key, groupObj)
        ciphered_key_bytes_string = ciphered_key_bytes.decode('utf-8')

        now = datetime.now()
        now = int(now.strftime("%Y%m%d%H%M%S%f"))
        random.seed(now)
        slice_id = random.randint(1, 2 ** 64)
        print(f'slice id {i}: {slice_id}')

        dict_pol = {'Slice_id': slice_id, 'CipheredKey': ciphered_key_bytes_string, 'Fields': entries[i]}
        header.append(dict_pol)

    json_file_ciphered = {}
    for i, entry in enumerate(entries):
        ciphered_fields = []
        for field in entry:
            cipher_field = cryptocode.encrypt(field, str(keys[i]))
            ciphered_fields.append(cipher_field)
            cipher = cryptocode.encrypt(data[field], str(keys[i]))
            json_file_ciphered[cipher_field] = cipher
        header[i]['Fields'] = ciphered_fields

    now = datetime.now()
    now = int(now.strftime("%Y%m%d%H%M%S%f"))
    random.seed(now)
    message_id = random.randint(1, 2 ** 64)
    metadata = {'process_instance_id': process_instance_id, 'message_id': message_id}
    print(f'message id: {message_id}')

    json_total = {'metadata': metadata, 'header': header, 'body': json_file_ciphered}

    # encoded = cryptocode.encrypt("Ciao Marzia!", str(key_encrypt1))

    name_file = 'files/key&ciphertext.txt'
    with open(name_file, 'w', encoding='utf-8') as f:
        json.dump(json_total, f, ensure_ascii=False, indent=4)

    new_file = api.add(name_file)
    hash_file = new_file['Hash']
    print(f'ipfs hash: {hash_file}')

    print(os.system('python3.11 blockchain/MessageContractMain.py %s %s %s %s' % (
        data_owner_private_key, app_id_messages, message_id, hash_file)))


if __name__ == '__main__':
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    process_instance_id = 10615895041881986071
    main(groupObj, maabe, api, process_instance_id)
