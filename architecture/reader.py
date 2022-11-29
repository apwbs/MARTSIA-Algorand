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

app_id_box = config('APPLICATION_ID_BOX')
app_id_messages = config('APPLICATION_ID_MESSAGES')

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def retrieve_data(authority_address):
    method = 'read_specific_box'
    box_name = base64.b64encode(decode_address(authority_address))
    result = subprocess.run(['python3.11', 'blockchain/BoxContract/BoxContractMain.py', method,
                             app_id_box, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
    result = ast.literal_eval(result)
    all_elements = base64.b64decode(result['value']).decode('utf-8')
    all_elements = all_elements.split('#')
    public_parameters = all_elements[2]
    return public_parameters


def generate_public_parameters():
    check_parameters = []

    data = retrieve_data(authority1_address)
    check_parameters.append(data)

    data = retrieve_data(authority2_address)
    check_parameters.append(data)

    data = retrieve_data(authority3_address)
    check_parameters.append(data)

    if len(set(check_parameters)) == 1:
        getfile = api.cat(check_parameters[0])
        with open('files/reader/public_parameters_reader.txt', 'wb') as ppw:
            ppw.write(getfile)


def retrieve_public_parameters():
    with open('files/reader/public_parameters_reader.txt', 'rb') as ppr:
        public_parameters = ppr.read()
    return public_parameters


def main(groupObj, maabe, message_id, slice_id):
    public_parameters = retrieve_public_parameters()
    public_parameters = bytesToObject(public_parameters, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    # keygen Bob
    with open('files/reader/user_sk1.txt', 'r') as us1:
        user_sk1 = us1.read()
    user_sk1 = bytesToObject(user_sk1, groupObj)

    with open('files/reader/user_sk2.txt', 'r') as us2:
        user_sk2 = us2.read()
    user_sk2 = bytesToObject(user_sk2, groupObj)

    with open('files/reader/user_sk3.txt', 'r') as us3:
        user_sk3 = us3.read()
    user_sk3 = bytesToObject(user_sk3, groupObj)

    user_sk = {'GID': 'bob', 'keys': merge_dicts(user_sk1, user_sk2, user_sk3)}

    # decrypt
    ciphertext_link = retriever.retrieveMessage(app_id_messages, message_id)
    getfile = api.cat(ciphertext_link)
    ciphertext_dict = json.loads(getfile)
    slice_check = ciphertext_dict['header']
    for remaining in slice_check:
        if remaining['Slice_id'] == slice_id:
            test = remaining['CipheredKey'].encode('utf-8')

            ct = bytesToObject(test, groupObj)
            v2 = maabe.decrypt(public_parameters, user_sk, ct)
            v2 = groupObj.serialize(v2)

            dec_field = [cryptocode.decrypt(remaining['Fields'][x], str(v2)) for x in range(len(remaining['Fields']))]
            decoded = [cryptocode.decrypt(ciphertext_dict['body'][x], str(v2)) for x in remaining['Fields']]
            decoded_final = zip(dec_field, decoded)
            print(dict(decoded_final))


if __name__ == '__main__':
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    process_instance_id = app_id_box
    # generate_public_parameters()
    message_id = 15807291614623720630
    slice_id = 3081925425294630327
    main(groupObj, maabe, message_id, slice_id)
