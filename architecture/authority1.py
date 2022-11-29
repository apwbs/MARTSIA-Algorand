import json

from charm.toolbox.pairinggroup import *
from maabe_class import *
import mpc_setup
from decouple import config
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import os
import sys
import base64
import subprocess
from algosdk.encoding import decode_address, encode_address
import ast

# sys.path.insert(0, 'blockchain/')
# from blockchain.retreiver import *

app_id_box = config('APPLICATION_ID_BOX')

authority1_mnemonic = config('AUTHORITY1_MNEMONIC')
authority1_private_key = config('AUTHORITY1_PRIVATEKEY')
authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')


def initial_parameters_hashed(groupObj):
    g1_1 = groupObj.random(G1)
    g2_1 = groupObj.random(G2)
    (h1_1, h2_1) = mpc_setup.commit(groupObj, g1_1, g2_1)

    with open('files/authority1/h1_1.txt', 'w') as h1_1w:
        h1_1w.write(h1_1)

    with open('files/authority1/h2_1.txt', 'w') as h2_1w:
        h2_1w.write(h2_1)

    hashed = h1_1 + ',' + h2_1 + '#'
    padding = '0' * 275
    hashed_padded = hashed + padding

    method = 'put_box'
    print(os.system('python3.11 blockchain/BoxContract/BoxContractMain.py %s %s %s %s' % (
        authority1_private_key, method, app_id_box, hashed_padded)))

    g1_1_bytes = groupObj.serialize(g1_1)
    g2_1_bytes = groupObj.serialize(g2_1)

    with open('files/authority1/g1_1.txt', 'wb') as g1_1w:
        g1_1w.write(g1_1_bytes)

    with open('files/authority1/g2_1.txt', 'wb') as g2_1w:
        g2_1w.write(g2_1_bytes)


def initial_parameters():
    with open('files/authority1/g1_1.txt', 'rb') as g1:
        g1_1_bytes = g1.read()

    with open('files/authority1/g2_1.txt', 'rb') as g2:
        g2_1_bytes = g2.read()

    method = 'read_box'
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', authority1_private_key, method,
                             app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')
    elements = g1_1_bytes.decode('utf-8') + ',' + g2_1_bytes.decode('utf-8') + '#'
    hashed_elements = result[:130] + elements
    padding = '0' * 93
    hashed_elements_padded = hashed_elements + padding

    method = 'put_box'
    print(os.system('python3.11 blockchain/BoxContract/BoxContractMain.py %s %s %s %s' % (
        authority1_private_key, method, app_id_box, hashed_elements_padded)))


def generate_public_parameters(groupObj, maabe, api):
    with open('files/authority1/g1_1.txt', 'rb') as g1:
        g1_1_bytes = g1.read()
    g1_1 = groupObj.deserialize(g1_1_bytes)

    with open('files/authority1/g2_1.txt', 'rb') as g2:
        g2_1_bytes = g2.read()
    g2_1 = groupObj.deserialize(g2_1_bytes)

    with open('files/authority1/h1_1.txt', 'r') as h1:
        h1 = h1.read()

    with open('files/authority1/h2_1.txt', 'r') as h2:
        h2 = h2.read()

    method = 'read_specific_box'
    ####################
    #######AUTH2########
    ####################
    box_name = base64.b64encode(decode_address(authority2_address))
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', method,
                             app_id_box, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
    result = ast.literal_eval(result)
    all_elements = base64.b64decode(result['value']).decode('utf-8')
    all_elements = all_elements.split('#')
    g1g2_2_hashed = all_elements[0]
    g1g2_2_hashed_split = g1g2_2_hashed.split(',')

    g1g2_2 = all_elements[1]
    g1g2_2_split = g1g2_2.split(',')

    ####################
    #######AUTH3########
    ####################
    box_name = base64.b64encode(decode_address(authority3_address))
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', method,
                             app_id_box, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
    result = ast.literal_eval(result)
    all_elements = base64.b64decode(result['value']).decode('utf-8')
    all_elements = all_elements.split('#')
    g1g2_3_hashed = all_elements[0]
    g1g2_3_hashed_split = g1g2_3_hashed.split(',')

    g1g2_3 = all_elements[1]
    g1g2_3_split = g1g2_3.split(',')

    #############################
    ##########VALUES#############
    #############################

    g1_2 = g1g2_2_split[0]
    g1_2 = bytes(g1_2, 'utf-8')
    g1_2 = groupObj.deserialize(g1_2)
    g2_2 = g1g2_2_split[1]
    g2_2 = bytes(g2_2, 'utf-8')
    g2_2 = groupObj.deserialize(g2_2)

    g1_3 = g1g2_3_split[0]
    g1_3 = bytes(g1_3, 'utf-8')
    g1_3 = groupObj.deserialize(g1_3)
    g2_3 = g1g2_3_split[1]
    g2_3 = bytes(g2_3, 'utf-8')
    g2_3 = groupObj.deserialize(g2_3)

    hashes1 = [h1, g1g2_2_hashed_split[0], g1g2_3_hashed_split[0]]
    hashes2 = [h2, g1g2_2_hashed_split[1], g1g2_3_hashed_split[1]]
    com1 = [g1_1, g1_2, g1_3]
    com2 = [g2_1, g2_2, g2_3]
    (value1, value2) = mpc_setup.generateParameters(groupObj, hashes1, hashes2, com1, com2)

    # setup
    public_parameters = maabe.setup(value1, value2)
    public_parameters_reduced = dict(list(public_parameters.items())[0:3])
    pp_reduced = objectToBytes(public_parameters_reduced, groupObj)

    name_file = 'files/authority1/public_parameters_authority1.txt'
    with open(name_file, 'wb') as ipfs:
        ipfs.write(pp_reduced)

    new_file = api.add(name_file)
    hash_file = new_file['Hash']
    print(f'ipfs hash: {hash_file}')

    method = 'read_box'
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', authority1_private_key, method,
                             app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')

    hashed_elements_pp = result[:312] + hash_file + '#'
    padding = '0' * 46
    hashed_elements_pp_padded = hashed_elements_pp + padding

    method = 'put_box'
    print(os.system('python3.11 blockchain/BoxContract/BoxContractMain.py %s %s %s %s' % (
        authority1_private_key, method, app_id_box, hashed_elements_pp_padded)))


def retrieve_public_parameters():
    with open('files/process_instance_id.txt', 'r') as cir:
        process_instance_id = cir.read()
    with open('files/authority1/public_parameters_authority1.txt', 'rb') as ppa2:
        public_parameters = ppa2.read()
    return public_parameters, process_instance_id


def generate_pk_sk(groupObj, maabe, api):
    response = retrieve_public_parameters()
    public_parameters = bytesToObject(response[0], groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    # authsetup 2AA
    (pk1, sk1) = maabe.authsetup(public_parameters, 'UT')
    pk1_bytes = objectToBytes(pk1, groupObj)
    sk1_bytes = objectToBytes(sk1, groupObj)

    name_file = 'files/authority1/authority_ut_pk.txt'
    with open(name_file, 'wb') as a1:
        a1.write(pk1_bytes)
    with open('files/authority1/private_key_au1.txt', 'wb') as as1:
        as1.write(sk1_bytes)

    new_file = api.add(name_file)
    hash_file = new_file['Hash']
    print(f'ipfs hash: {hash_file}')

    method = 'read_box'
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', authority1_private_key, method,
                             app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')
    hashed_elements_pp_pk = result[:359] + hash_file

    method = 'put_box'
    print(os.system('python3.11 blockchain/BoxContract/BoxContractMain.py %s %s %s %s' % (
        authority1_private_key, method, app_id_box, hashed_elements_pp_pk)))


def main():
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    # initial_parameters_hashed(groupObj)
    # initial_parameters()
    # generate_public_parameters(groupObj, maabe, api)
    generate_pk_sk(groupObj, maabe, api)

    # test = api.name.publish('/ipfs/' + hash_file)
    # print(test)
    # os.system('ipfs cat ' + hash_file)
    # os.system('ipfs name publish /ipfs/' + hash_file)


if __name__ == '__main__':
    main()
