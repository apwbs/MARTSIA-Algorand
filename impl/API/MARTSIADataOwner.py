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
import base64
import subprocess
from algosdk.encoding import decode_address, encode_address
import ast
import sqlite3

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')
authority4_address = config('AUTHORITY4_ADDRESS')

dataOwner_address = config('DATAOWNER_MANUFACTURER_ADDRESS')
dataOwner_private_key = config('DATAOWNER_MANUFACTURER_PRIVATEKEY')

#process_instance_id_env = config('PROCESS_INSTANCE_ID')

class MARTSIADataOwner:
    def __init__(self, process_instance_id):
        self.authority1_address = config('AUTHORITY1_ADDRESS')
        self.authority2_address = config('AUTHORITY2_ADDRESS')
        self.authority3_address = config('AUTHORITY3_ADDRESS')
        self.authority4_address = config('AUTHORITY4_ADDRESS')

        self.dataOwner_address = config('DATAOWNER_MANUFACTURER_ADDRESS')
        self.dataOwner_private_key = config('DATAOWNER_MANUFACTURER_PRIVATEKEY')

        #self.process_instance_id_env = process_instance_id
        self.conn = sqlite3.connect('files/data_owner/data_owner.db')
        self.x = self.conn.cursor()

        self.groupObj = PairingGroup('SS512')
        self.maabe = MaabeRW15(self.groupObj)
        self.api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        self.process_instance_id = process_instance_id
        self.app_id_messages = config('APPLICATION_ID_MESSAGES')


    def __retrieve_data__(self, authority_address):

        method = 'read_specific_box'
        box_name = base64.b64encode(decode_address(authority_address))
        result = subprocess.run(['python3.10', 'blockchain/BoxContract/BoxContractMain.py', method,
                                self.process_instance_id, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
        result = ast.literal_eval(result)
        all_elements = base64.b64decode(result['value']).decode('utf-8')
        all_elements = all_elements.split('#')
        authorities = all_elements[0]
        public_parameters = all_elements[3]
        public_key = all_elements[4]
        return authorities, public_parameters, public_key


    def generate_pp_pk(self):
        check_authorities = []
        check_parameters = []

        data = self.__retrieve_data__(authority1_address)
        check_authorities.append(data[0])
        check_parameters.append(data[1])
        pk1 = self.api.cat(data[2])
        pk1 = pk1.decode('utf-8').rstrip('"').lstrip('"')
        pk1 = pk1.encode('utf-8')
        self.x.execute("INSERT OR IGNORE INTO authorities_public_keys VALUES (?,?,?,?)",
                (str(self.process_instance_id), 'Auth-1', data[2], pk1))
        self.conn.commit()

        data = self.__retrieve_data__(authority2_address)
        check_authorities.append(data[0])
        check_parameters.append(data[1])
        pk2 = self.api.cat(data[2])
        pk2 = pk2.decode('utf-8').rstrip('"').lstrip('"')
        pk2 = pk2.encode('utf-8')
        self.x.execute("INSERT OR IGNORE INTO authorities_public_keys VALUES (?,?,?,?)",
                (str(self.process_instance_id), 'Auth-2', data[2], pk2))
        self.conn.commit()

        data = self.__retrieve_data__(authority3_address)
        check_authorities.append(data[0])
        check_parameters.append(data[1])
        pk3 = self.api.cat(data[2])
        pk3 = pk3.decode('utf-8').rstrip('"').lstrip('"')
        pk3 = pk3.encode('utf-8')
        self.x.execute("INSERT OR IGNORE INTO authorities_public_keys VALUES (?,?,?,?)",
                (str(self.process_instance_id), 'Auth-3', data[2], pk3))
        self.conn.commit()

        data = self.__retrieve_data__(authority4_address)
        check_authorities.append(data[0])
        check_parameters.append(data[1])
        pk4 = self.api.cat(data[2])
        pk4 = pk4.decode('utf-8').rstrip('"').lstrip('"')
        pk4 = pk4.encode('utf-8')
        self.x.execute("INSERT OR IGNORE INTO authorities_public_keys VALUES (?,?,?,?)",
                (str(self.process_instance_id), 'Auth-4', data[2], pk4))
        self.conn.commit()

        if len(set(check_authorities)) == 1 and len(set(check_parameters)) == 1:
            getfile = self.api.cat(check_parameters[0])
            getfile = getfile.decode('utf-8').rstrip('"').lstrip('"')
            getfile = getfile.encode('utf-8')
            self.x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)",
                    (str(self.process_instance_id), check_parameters[0], getfile))
            self.conn.commit()


    def __retrieve_public_parameters__(self):
        self.x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(self.process_instance_id),))
        result = self.x.fetchall()
        public_parameters = result[0][2]
        return public_parameters


    def cipher_data(self, data, entries, access_policy):

#        groupObj = PairingGroup('SS512')
#        maabe = MaabeRW15(groupObj)
#        api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

        response = self.__retrieve_public_parameters__()
        public_parameters = bytesToObject(response, self.groupObj)
        H = lambda x: self.group.hash(x, G2) #questo self c'era già prima, forse va in conflitto con l'uso di self nella funzione, possibile soluzione una funzione statics
        F = lambda x: self.group.hash(x, G2)
        public_parameters["H"] = H
        public_parameters["F"] = F

        self.x.execute("SELECT * FROM authorities_public_keys WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), 'Auth-1'))
        result = self.x.fetchall()
        pk1 = result[0][3]
        pk1 = bytesToObject(pk1, self.groupObj)

        self.x.execute("SELECT * FROM authorities_public_keys WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), 'Auth-2'))
        result = self.x.fetchall()
        pk2 = result[0][3]
        pk2 = bytesToObject(pk2, self.groupObj)

        self.x.execute("SELECT * FROM authorities_public_keys WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), 'Auth-3'))
        result = self.x.fetchall()
        pk3 = result[0][3]
        pk3 = bytesToObject(pk3, self.groupObj)

        self.x.execute("SELECT * FROM authorities_public_keys WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), 'Auth-4'))
        result = self.x.fetchall()
        pk4 = result[0][3]
        pk4 = bytesToObject(pk4, self.groupObj)

        # public keys authorities
        pk = {'UT': pk1, 'OU': pk2, 'OT': pk3, 'TU': pk4}

        # with open('files/data_to_martsia.json', 'r') as file:
        #     data = json.load(file)
        # value1 = data['clear_data']
        # _, value = list(data.items())[1]
        # split_value = value[9:].split('\\n')
        # result = {}
        # for item in split_value:
        #     key, value = item.split(':')
        #     key = ' '.join(key.split())
        #     value = ' '.join(value.split())
        #     result[key] = value
        # with open('files/data.json', 'w') as file:
        #     file.write(json.dumps(result))
       
        #This informations should be given by the user as input
        # '(8785437525079851029@UT and MANUFACTURER@UT) and (8785437525079851029@OU and MANUFACTURER@OU)'
        # access_policy = ['(' + str(process_instance_id_env) + '@UT and ' + str(process_instance_id_env) + '@OU and ' + str(process_instance_id_env) + '@OT and '
        #                  '' + str(process_instance_id_env) + '@TU) and (MANUFACTURER@UT or '
        #                  'SUPPLIER@OU)',
        #                  '(' + str(process_instance_id_env) + '@UT and ' + str(process_instance_id_env) + '@OU and ' + str(process_instance_id_env) + '@OT and '
        #                  '' + str(process_instance_id_env) + '@TU) and (MANUFACTURER@UT or ('
        #                  'SUPPLIER@OU and ELECTRONICS@OT)',
        #                  '(' + str(process_instance_id_env) + '@UT and ' + str(process_instance_id_env) + '@OU and ' + str(process_instance_id_env) + '@OT and '
        #                  '' + str(process_instance_id_env) + '@TU) and (MANUFACTURER@UT or ('
        #                  'SUPPLIER@OU and MECHANICS@TU)']
        #entries = [['ID', 'SortAs', 'GlossTerm'], ['Acronym', 'Abbrev'], ['Specs', 'Dates']]
    
        #

        if len(access_policy) != len(entries):
            print('ERROR: The number of policies and entries is different')
            print("Policy: ", len(access_policy), access_policy)
            print("Entries: ", len(entries), entries)
            exit()

        keys = []
        header = []
        for i in range(len(entries)):
            key_group = self.groupObj.random(GT)
            key_encrypt = self.groupObj.serialize(key_group)
            keys.append(key_encrypt)
            key_encrypt_deser = self.groupObj.deserialize(key_encrypt)

            ciphered_key = self.maabe.encrypt(public_parameters, pk, key_encrypt_deser, access_policy[i])
            ciphered_key_bytes = objectToBytes(ciphered_key, self.groupObj)
            ciphered_key_bytes_string = ciphered_key_bytes.decode('utf-8')

            ## Possibility to clean the code here. This check can be done outside the 'for loop'
            if len(access_policy) == len(entries) == 1:
                dict_pol = {'CipheredKey': ciphered_key_bytes_string, 'Fields': entries[i]}
                header.append(dict_pol)
            else:
                now = datetime.now()
                now = int(now.strftime("%Y%m%d%H%M%S%f"))
                random.seed(now)
                slice_id = random.randint(1, 2 ** 64)
                dict_pol = {'Slice_id': slice_id, 'CipheredKey': ciphered_key_bytes_string, 'Fields': entries[i]}
                print(f'slice id {i}: {slice_id}')
                header.append(dict_pol)

        json_file_ciphered = {}
        for i, entry in enumerate(entries):
            ciphered_fields = []
            for field in entry:
                cipher_field = cryptocode.encrypt(field, str(keys[i]))
                ciphered_fields.append(cipher_field)
                try:
                    cipher = cryptocode.encrypt(data[field], str(keys[i]))
                except:
                    print(f'ERROR: The field {field} is not present in the data')
                    print("Data: ", data)
                    print("Type of data", type(data))
                    print("Field: ", field)
                    print("Keys", keys)
                    print("i: ", i)
                    exit()
                json_file_ciphered[cipher_field] = cipher
            header[i]['Fields'] = ciphered_fields

        now = datetime.now()
        now = int(now.strftime("%Y%m%d%H%M%S%f"))
        random.seed(now)
        message_id = random.randint(1, 2 ** 64)
        metadata = {'sender': dataOwner_address, 'process_instance_id': int(self.process_instance_id),
                    'message_id': message_id}
        print(f'message id: {message_id}')

        json_total = {'metadata': metadata, 'header': header, 'body': json_file_ciphered}

        # encoded = cryptocode.encrypt("Ciao Marzia!", str(key_encrypt1))

        hash_file = self.api.add_json(json_total)
        print(f'ipfs hash: {hash_file}')

        self.x.execute("INSERT OR IGNORE INTO messages VALUES (?,?,?,?)",
                (str(self.process_instance_id), str(message_id), hash_file, str(json_total)))
        self.conn.commit()

        # hash_to_store = "@MARTSIA:" + hash_file
        # ciphered_file = {}
        # with open('files/ciphered_file.json', 'w') as file:
        #     ciphered_file['clear_data'] = value1
        #     ciphered_file['martsia'] = hash_to_store
        #     file.write(json.dumps(ciphered_file))

        print(os.system('python3.10 blockchain/Controlled/multisig/MessageContract/MessageContractMain.py %s %s %s %s' % (
            self.dataOwner_private_key, self.app_id_messages, json_total['metadata']['message_id'], hash_file)))
