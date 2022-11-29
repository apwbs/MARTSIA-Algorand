from charm.toolbox.pairinggroup import *
from decouple import config
from maabe_class import *
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import json
import sys
import retriever

app_id_attribute = config('APPLICATION_ID_CERTIFIER')


def retrieve_public_parameters():
    with open('files/authority3/public_parameters_authority3.txt', 'rb') as ppa3:
        public_parameters = ppa3.read()
    return public_parameters


def generate_user_key(gid, process_instance_id, reader_address):
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    response = retrieve_public_parameters()
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    with open('files/authority3/private_key_ot3.txt', 'rb') as sk3r:
        sk3 = sk3r.read()
    sk3 = bytesToObject(sk3, groupObj)

    # keygen Bob
    attributes_ipfs_link = retriever.retrieveReaderAttributes(app_id_attribute, process_instance_id)
    getfile = api.cat(attributes_ipfs_link)
    getfile = getfile.split(b'\n')
    attributes_dict = json.loads(getfile[1].decode('utf-8'))
    user_attr3 = attributes_dict[reader_address]
    user_attr3 = [k for k in user_attr3 if k.endswith('@OT')]
    user_sk3 = maabe.multiple_attributes_keygen(public_parameters, sk3, gid, user_attr3)
    user_sk3_bytes = objectToBytes(user_sk3, groupObj)
    return user_sk3_bytes
