from charm.toolbox.pairinggroup import *
from maabe_class import *
import retriever
import mpc_setup
from decouple import config
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import io
import sqlite3
import os
import time
import argparse
import subprocess
import base64
import ast

process_instance_id_env = config('PROCESS_INSTANCE_ID')
app_id_box = config('APPLICATION_ID_BOX')


authorities_list = [config('AUTHORITY1_ADDRESS'),
                    config('AUTHORITY2_ADDRESS'),
                    config('AUTHORITY3_ADDRESS'),
                    config('AUTHORITY4_ADDRESS')]

authorities_names = ['UT', 'OU', 'OT', 'TU']

void_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

class Authority:
    def __init__(self, authority_number):
        self.authority_number = authority_number
        self.authority_address = authorities_list[authority_number - 1]
        self.__authority_private_key__ = config('AUTHORITY' + str(authority_number) + '_PRIVATEKEY')
        self.__conn__ = sqlite3.connect('files/authority' +str(authority_number)+ '/authority' + str(authority_number) + '.db')
        self.__x__ = self.__conn__.cursor()

    def save_authorities_names(self, api, process_instance_id):
        f = io.StringIO()
        for i, addr in enumerate(authorities_list):
            f.write('process_instance: ' + str(process_instance_id) + '\n')
            f.write('identification: ' + 'authority ' + str(i + 1) + '\n')
            f.write('name: ' + str(authorities_names[i]) + '\n')
            f.write('address: ' + addr + '\n\n')
        f.seek(0)

        file_to_str = f.read()

        hash_file = api.add_json(file_to_str)
        print(f'ipfs hash: {hash_file}')

        authorities_name = hash_file + '#'
        padding = '0' * 405
        authorities_name_padded = authorities_name + padding

        self.x.execute("INSERT OR IGNORE INTO authority_names VALUES (?,?,?)", (process_instance_id, hash_file, file_to_str))
        self.conn.commit()

        # x.execute("SELECT * FROM authority_names WHERE process_instance=?", (process_instance_id,))
        # result = x.fetchall()
        # with open('files/authority1/test.txt', 'w') as u1:
        #     u1.write(result[0][1])

        method = 'put_box'
        print(os.system('python3.10 blockchain/Controlled/multisig/BoxContract/BoxContractMain.py %s %s %s %s' % (
            self.__authority_private_key__, method, app_id_box, authorities_name_padded)))


    def initial_parameters_hashed(self, groupObj, process_instance_id):
        g1_1 = groupObj.random(G1)
        g2_1 = groupObj.random(G2)
        (h1_1, h2_1) = mpc_setup.commit(groupObj, g1_1, g2_1)

        self.x.execute("INSERT OR IGNORE INTO h_values VALUES (?,?,?)", (process_instance_id, h1_1, h2_1))
        self.conn.commit()

        method = 'read_box'
        result = subprocess.run(['python3.10', 'blockchain/Controlled/multisig/BoxContract/BoxContractMain.py', authority1_private_key, method,
                                app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')
        authorities = result[:47]
        hashed = authorities + h1_1 + ',' + h2_1 + '#'
        padding = '0' * 275
        hashed_padded = hashed + padding

        method = 'put_box'
        print(os.system('python3.10 blockchain/Controlled/multisig/BoxContract/BoxContractMain.py %s %s %s %s' % (
            self.__authority_private_key__, method, app_id_box, hashed_padded)))

        g1_1_bytes = groupObj.serialize(g1_1)
        g2_1_bytes = groupObj.serialize(g2_1)

        self.x.execute("INSERT OR IGNORE INTO g_values VALUES (?,?,?)", (process_instance_id, g1_1_bytes, g2_1_bytes))
        self.conn.commit()



    def initial_parameters(self, process_instance_id):
        self.x.execute("SELECT * FROM g_values WHERE process_instance=?", (process_instance_id,))
        result = self.x.fetchall()
        g1_1_bytes = result[0][1]
        g2_1_bytes = result[0][2]

        method = 'read_box'
        result = subprocess.run(['python3.10', 'blockchain/Controlled/multisig/BoxContract/BoxContractMain.py', self.__authority_private_key__, method,
                                app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')
        elements = g1_1_bytes.decode('utf-8') + ',' + g2_1_bytes.decode('utf-8') + '#'
        hashed_elements = result[:177] + elements
        padding = '0' * 93
        hashed_elements_padded = hashed_elements + padding

        method = 'put_box'
        print(os.system('python3.10 blockchain/Controlled/multisig/BoxContract/BoxContractMain.py %s %s %s %s' % (
            self.__authority_private_key__, method, app_id_box, hashed_elements_padded)))

    def generate_public_parameters(self, groupObj, maabe, api, process_instance_id):
        hashes1 = []
        hashes2 = []
        com1 = []
        com2 = []

        method = 'read_specific_box'
        count = 0
        for auth in authorities_list:
            box_name = base64.b64encode(decode_address(authorities_list))
            result = subprocess.run(['python3.10', 'blockchain/BoxContract/BoxContractMain.py', method,
                                app_id_box, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
            
            result = ast.literal_eval(result)
            all_elements = base64.b64decode(result['value']).decode('utf-8')
            all_elements = all_elements.split('#')
            g1gx_2_hashed = all_elements[1]
            g1gx_2_hashed_split = g1gx_2_hashed.split(',')
            g1gx_2 = all_elements[2]
            g1gx_2_split = g1gx_2.split(',')
            g1_x = g1gx_2_split[0]
            g1_x = bytes(g1_x, 'utf-8')
            g1_x = groupObj.deserialize(g1_x)
            g2_x = g1gx_2_split[1]
            g2_x = bytes(g2_x, 'utf-8')
            g2_x = groupObj.deserialize(g2_x)
            hashes1.append(g1gx_2_hashed_split[0])
            hashes2.append(g1gx_2_hashed_split[1])
            com1.append(g1_x)
            com2.append(g2_x)
            count += 1

        (value1, value2) = mpc_setup.generateParameters(groupObj, hashes1, hashes2, com1, com2)

        # setup
        public_parameters = maabe.setup(value1, value2)
        public_parameters_reduced = dict(list(public_parameters.items())[0:3])
        pp_reduced = objectToBytes(public_parameters_reduced, groupObj)

        file_to_str = pp_reduced.decode('utf-8')
        hash_file = api.add_json(file_to_str)
        print(f'ipfs hash: {hash_file}')

        self.x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)", (process_instance_id, hash_file, file_to_str))
        self.conn.commit()

        # name_file = 'files/authority1/public_parameters_authority1_' + str(process_instance_id) + '.txt'
        # with open(name_file, 'wb') as ipfs:
        #     ipfs.write(pp_reduced)
        # new_file = api.add(name_file)
        # hash_file = new_file['Hash']
        # print(f'ipfs hash: {hash_file}')

        method = 'read_box'
        result = subprocess.run(['python3.10', 'blockchain/BoxContract/BoxContractMain.py', self.__authority_private_key__, method,
                                app_id_box], stdout=subprocess.PIPE).stdout.decode('utf-8')

        hashed_elements_pp = result[:359] + hash_file + '#'
        padding = '0' * 46
        hashed_elements_pp_padded = hashed_elements_pp + padding

        method = 'put_box'
        print(os.system('python3.10 blockchain/BoxContract/BoxContractMain.py %s %s %s %s' % (
            self.__authority_private_key__, method, app_id_box, hashed_elements_pp_padded)))



    def retrieve_public_parameters(self, process_instance_id):
        self.__x__.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
        result = self.__x__.fetchall()
        public_parameters = result[0][2].encode()
        return public_parameters

    def generate_pk_sk(self, groupObj, maabe, api, process_instance_id):
        response = self.retrieve_public_parameters(process_instance_id)
        public_parameters = bytesToObject(response, groupObj)
        H = lambda x: group.hash(x, G2)
        F = lambda x: group.hash(x, G2)
        public_parameters["H"] = H
        public_parameters["F"] = F

        # authsetup 2AA
        (pk1, sk1) = maabe.authsetup(public_parameters, authorities_names[self.authority_number -1])
        pk1_bytes = objectToBytes(pk1, groupObj)
        sk1_bytes = objectToBytes(sk1, groupObj)

        file_to_str = pk1_bytes.decode('utf-8')
        hash_file = api.add_json(file_to_str)
        print(f'ipfs hash: {hash_file}')

        self.__x__.execute("INSERT OR IGNORE INTO private_keys VALUES (?,?)", (str(process_instance_id), sk1_bytes))
        self.__conn__.commit()

        self.__x__.execute("INSERT OR IGNORE INTO public_keys VALUES (?,?,?)", (str(process_instance_id), hash_file, pk1_bytes))
        self.__conn__.commit()

        block_int.send_publicKey_link(self.authority_address, self.__authority_private_key__, process_instance_id, hash_file)


def main():
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    process_instance_id = int(process_instance_id_env)

    parser = argparse.ArgumentParser(description='Authority')
    parser.add_argument('-a', '--authority', type=int, default='MANUFACTURER',help='Authority number')
    args = parser.parse_args()
    if args.authority < 1 or args.authority > len(authorities_list):
        print("Invalid authority number")
        exit()
    authority_number = args.authority
    authority = Authority(authority_number)
    # 0.1
    print("Phase 0.1")
    authority.save_authorities_names(api, process_instance_id)
    # 0.2
    print("Phase 0.2")
    authority.initial_parameters_hashed(groupObj, process_instance_id)
    # 0.3
    print("Phase 0.3")
    authority.initial_parameters(process_instance_id)
    # 0.4
    print("Phase 0.4")
    while not authority.generate_public_parameters(groupObj, maabe, api, process_instance_id):
        time.sleep(5) 
    # 0.5
    print("Phase 0.5")
    authority.generate_pk_sk(groupObj, maabe, api, process_instance_id)

#TODO Resta in ascolto per verificare che gli altri abbiano fatto il loro (monitor)
# 0.1, 0.2, 0.3 ascolto 0.4 0.5

if __name__ == '__main__':
    main()
