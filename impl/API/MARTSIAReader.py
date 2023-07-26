from charm.toolbox.pairinggroup import *
from charm.core.engine.util import objectToBytes, bytesToObject
import cryptocode
from decouple import config
import ipfshttpclient
import json
from maabe_class import *
import sys
import base64
import subprocess
from algosdk.encoding import decode_address, encode_address
import ast
import retriever
import sqlite3

# This class is equivalent to the content of ../reader.py
class MARTSIAReader:

    def __init__(self, process_instance_id, number_of_authorities):
        self.process_instance_id = process_instance_id
        self.number_of_authorities = number_of_authorities
        self.app_id_messages = config('APPLICATION_ID_MESSAGES')
        self.authorities_addresses = []
        for i in range(1, number_of_authorities+1):
            self.authorities_addresses.append(config('AUTHORITY' + str(i) + '_ADDRESS'))

        self.groupObj = PairingGroup('SS512')
        self.maabe = MaabeRW15(self.groupObj)
        self.api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

        self.message_id_caterpillar = 0

        # Connection to SQLite3 data_owner database
        self.conn = sqlite3.connect('files/reader/reader.db')
        self.x = self.conn.cursor()


    def merge_dicts(dict_args):
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
        """
        result = {}
        for dictionary in dict_args:
            result.update(dictionary)
        return result


    def __retrieve_data__(self, authority_address, process_instance_id):
        method = 'read_specific_box'
        box_name = base64.b64encode(decode_address(authority_address))
        result = subprocess.run(['python3.10', 'blockchain/BoxContract/BoxContractMain.py', method,
                                process_instance_id, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
        result = ast.literal_eval(result)
        all_elements = base64.b64decode(result['value']).decode('utf-8')
        all_elements = all_elements.split('#')
        authorities = all_elements[0]
        public_parameters = all_elements[3]
        return authorities, public_parameters
        authorities = block_int.retrieve_authority_names(authority_address, process_instance_id)
        public_parameters = block_int.retrieve_parameters_link(authority_address, process_instance_id)
        return authorities, public_parameters


    def generate_public_parameters(self):
        check_authorities = []
        check_parameters = []

        for authority_address in self.authorities_addresses:
            data = self.__retrieve_data__(authority_address, self.process_instance_id)
            check_authorities.append(data[0])
            check_parameters.append(data[1])

        if len(set(check_authorities)) == 1 and len(set(check_parameters)) == 1:
            getfile = self.api.cat(check_parameters[0])        
            self.x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)",
                    (str(self.process_instance_id), check_parameters[0], getfile))
            self.conn.commit()


    def __retrieve_public_parameters__(self):
        self.x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(self.process_instance_id),))
        result = self.x.fetchall()
        try:
            public_parameters = result[0][2]
        except IndexError:
            self.generate_public_parameters()
            self.x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(self.process_instance_id),))
            result = self.x.fetchall()
            public_parameters = result[0][2]
        return public_parameters


    def __actual_decryption__(self, remaining, public_parameters, user_sk, ciphertext_dict):
        test = remaining['CipheredKey'].encode('utf-8')

        ct = bytesToObject(test, self.groupObj)
        v2 = self.maabe.decrypt(public_parameters, user_sk, ct)
        v2 = self.groupObj.serialize(v2)

        dec_field = [cryptocode.decrypt(remaining['Fields'][x], str(v2)) for x in
                    range(len(remaining['Fields']))]
        decoded = [cryptocode.decrypt(ciphertext_dict['body'][x], str(v2)) for x in remaining['Fields']]
        decoded_final = zip(dec_field, decoded)
        print(dict(decoded_final))


    def read(self, message_id, slice_id, gid):
        response = self.__retrieve_public_parameters__()
        public_parameters = bytesToObject(response, self.groupObj)
        H = lambda x: self.group.hash(x, G2)
        F = lambda x: self.group.hash(x, G2)
        public_parameters["H"] = H
        public_parameters["F"] = F

        user_sks = []
        # keygen Bob
        # we can do this with a for loop
        for i in range(1, self.number_of_authorities):
#            user_sks.append(self.maabe.keygen(public_parameters, self.groupObj.random(G2)))
            self.x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), 'Auth-'+str(i)))
            result = self.x.fetchall()
            user_sk = result[0][2]
            user_sk = user_sk.encode()
            user_sks.append(bytesToObject(user_sk, self.groupObj))
        user_sk = {'GID': gid, 'keys': MARTSIAReader.merge_dicts(user_sks)}

        # decrypt
        response = retriever.retrieveMessage(self.app_id_messages, message_id)
        ciphertext_link = response[0]
        getfile = self.api.cat(ciphertext_link)
        ciphertext_dict = json.loads(getfile)
        sender = response[1]
        if ciphertext_dict['metadata']['process_instance_id'] == int(self.process_instance_id) \
                and ciphertext_dict['metadata']['message_id'] == message_id \
                and ciphertext_dict['metadata']['sender'] == sender:
            slice_check = ciphertext_dict['header']
            if len(slice_check) == 1:
                self.__actual_decryption__(ciphertext_dict['header'][0], public_parameters, user_sk, ciphertext_dict)
            elif len(slice_check) > 1:
                for remaining in slice_check:
                    if remaining['Slice_id'] == slice_id:
                        self.__actual_decryption__(remaining, public_parameters, user_sk, ciphertext_dict)


    def set_message_id(message_id_value):
        global message_id_caterpillar
        message_id_caterpillar = message_id_value

        # main(process_instance_id, message_id_caterpillar, slice_id)
