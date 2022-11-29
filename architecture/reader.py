from charm.toolbox.pairinggroup import *
from charm.core.engine.util import objectToBytes, bytesToObject
import cryptocode
from decouple import config
import ipfshttpclient
import json
from maabe_class import *
import sys

sys.path.insert(0, 'blockchain/')
from blockchain.retreiver import *

app_id_public_parameters = config('APPLICATION_ID_PUBLIC_PARAMETERS')
app_id_messages = config('APPLICATION_ID_MESSAGES')


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def generate_public_parameters(api, process_instance_id):
    public_parameters_link = retrievePublicParameters(app_id_public_parameters, process_instance_id)
    getfile = api.cat(public_parameters_link)
    with open('files/reader/public_parameters_reader.txt', 'wb') as ppw:
        ppw.write(getfile)


def retrieve_public_parameters():
    with open('files/reader/public_parameters_reader.txt', 'rb') as ppr:
        public_parameters = ppr.read()
    return public_parameters


def main(groupObj, maabe, message_id, slice_id):
    response = retrieve_public_parameters()
    public_parameters = bytesToObject(response, groupObj)
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
    ciphertext_link = retrieveMessage(app_id_messages, message_id)
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

    process_instance_id = 13781065728986458357
    # generate_public_parameters(api, process_instance_id)
    message_id = 2559868811984323903
    slice_id = 12883135380544938366
    main(groupObj, maabe, message_id, slice_id)
