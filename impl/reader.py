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

app_id_box = config('APPLICATION_ID_BOX')
app_id_messages = config('APPLICATION_ID_MESSAGES')

authority1_address = config('AUTHORITY1_ADDRESS')
authority2_address = config('AUTHORITY2_ADDRESS')
authority3_address = config('AUTHORITY3_ADDRESS')
authority4_address = config('AUTHORITY4_ADDRESS')

# Connection to SQLite3 data_owner database
conn = sqlite3.connect('files/reader/reader.db')
x = conn.cursor()


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
    result = subprocess.run(['python3.10', 'blockchain/BoxContract/BoxContractMain.py', method,
                             app_id_box, box_name], stdout=subprocess.PIPE).stdout.decode('utf-8')
    result = ast.literal_eval(result)
    all_elements = base64.b64decode(result['value']).decode('utf-8')
    all_elements = all_elements.split('#')
    authorities = all_elements[0]
    public_parameters = all_elements[3]
    return authorities, public_parameters


def generate_public_parameters():
    check_authorities = []
    check_parameters = []

    data = retrieve_data(authority1_address)
    check_authorities.append(data[0])
    check_parameters.append(data[1])

    data = retrieve_data(authority2_address)
    check_authorities.append(data[0])
    check_parameters.append(data[1])

    data = retrieve_data(authority3_address)
    check_authorities.append(data[0])
    check_parameters.append(data[1])

    data = retrieve_data(authority4_address)
    check_authorities.append(data[0])
    check_parameters.append(data[1])

    if len(set(check_authorities)) == 1 and len(set(check_parameters)) == 1:
        getfile = api.cat(check_parameters[0])
        getfile = getfile.decode('utf-8').rstrip('"').lstrip('"')
        getfile = getfile.encode('utf-8')
        x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)",
                  (process_instance_id, check_parameters[0], getfile))
        conn.commit()
        # with open('files/reader/public_parameters_reader_' + str(process_instance_id) + '.txt', 'wb') as ppw:
        #     ppw.write(getfile)


def retrieve_public_parameters(process_instance_id):
    x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (process_instance_id,))
    result = x.fetchall()
    public_parameters = result[0][2]
    # with open('files/reader/public_parameters_reader_' + str(process_instance_id) + '.txt', 'rb') as ppr:
    #     public_parameters = ppr.read()
    return public_parameters


def actual_decryption(remaining, public_parameters, user_sk, ciphertext_dict):
    test = remaining['CipheredKey'].encode('utf-8')

    ct = bytesToObject(test, groupObj)
    v2 = maabe.decrypt(public_parameters, user_sk, ct)
    v2 = groupObj.serialize(v2)

    dec_field = [cryptocode.decrypt(remaining['Fields'][x], str(v2)) for x in
                 range(len(remaining['Fields']))]
    decoded = [cryptocode.decrypt(ciphertext_dict['body'][x], str(v2)) for x in remaining['Fields']]
    decoded_final = zip(dec_field, decoded)
    print(dict(decoded_final))


def main(process_instance_id, message_id, slice_id):
    public_parameters = retrieve_public_parameters(process_instance_id)
    public_parameters = bytesToObject(public_parameters, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    # keygen Bob
    # with open('files/reader/user_sk1_' + str(process_instance_id) + '.txt', 'r') as us1:
    #     user_sk1 = us1.read()
    # user_sk1 = bytesToObject(user_sk1, groupObj)

    x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_name=?",
              (str(process_instance_id), 'Auth-1'))
    result = x.fetchall()
    user_sk1 = result[0][2]
    user_sk1 = user_sk1.encode()
    user_sk1 = bytesToObject(user_sk1, groupObj)

    x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_name=?",
              (str(process_instance_id), 'Auth-2'))
    result = x.fetchall()
    user_sk2 = result[0][2]
    user_sk2 = user_sk2.encode()
    user_sk2 = bytesToObject(user_sk2, groupObj)

    x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_name=?",
              (str(process_instance_id), 'Auth-3'))
    result = x.fetchall()
    user_sk3 = result[0][2]
    user_sk3 = user_sk3.encode()
    user_sk3 = bytesToObject(user_sk3, groupObj)

    x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_name=?",
              (str(process_instance_id), 'Auth-4'))
    result = x.fetchall()
    user_sk4 = result[0][2]
    user_sk4 = user_sk4.encode()
    user_sk4 = bytesToObject(user_sk4, groupObj)

    user_sk = {'GID': 'bob', 'keys': merge_dicts(user_sk1, user_sk2, user_sk3, user_sk4)}

    # decrypt
    response = retriever.retrieveMessage(app_id_messages, message_id)
    ciphertext_link = response[0]
    getfile = api.cat(ciphertext_link)
    ciphertext_dict = json.loads(getfile)
    sender = response[1]
    if ciphertext_dict['metadata']['process_instance_id'] == int(process_instance_id) \
            and ciphertext_dict['metadata']['message_id'] == message_id \
            and ciphertext_dict['metadata']['sender'] == sender:
        slice_check = ciphertext_dict['header']
        if len(slice_check) == 1:
            actual_decryption(ciphertext_dict['header'][0], public_parameters, user_sk, ciphertext_dict)
        elif len(slice_check) > 1:
            for remaining in slice_check:
                if remaining['Slice_id'] == slice_id:
                    actual_decryption(remaining, public_parameters, user_sk, ciphertext_dict)


if __name__ == '__main__':
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    process_instance_id = int(app_id_box)
    # generate_public_parameters()
    message_id = 17149713040810547922
    slice_id = 6123765222549631388
    main(process_instance_id, message_id, slice_id)
