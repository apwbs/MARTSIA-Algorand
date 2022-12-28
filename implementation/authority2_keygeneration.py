from charm.toolbox.pairinggroup import *
from decouple import config
from maabe_class import *
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import json
import sys
import retriever


app_id_attribute = config('APPLICATION_ID_CERTIFIER')


def retrieve_public_parameters(process_instance_id):
    with open('files/authority2/public_parameters_authority2_' + str(process_instance_id) + '.txt', 'rb') as ppa2:
        public_parameters = ppa2.read()
    return public_parameters


def generate_user_key(gid, process_instance_id, reader_address):
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    response = retrieve_public_parameters(process_instance_id)
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    with open('files/authority2/private_key_ou2_' + str(process_instance_id) + '.txt', 'rb') as sk2r:
        sk2 = sk2r.read()
    sk2 = bytesToObject(sk2, groupObj)

    # keygen Bob
    attributes_ipfs_link = retriever.retrieveReaderAttributes(app_id_attribute, process_instance_id)
    getfile = api.cat(attributes_ipfs_link)
    getfile = getfile.split(b'\n')
    attributes_dict = json.loads(getfile[1].decode('utf-8'))
    user_attr2 = attributes_dict[reader_address]
    user_attr2 = [k for k in user_attr2 if k.endswith('@OU')]
    user_sk2 = maabe.multiple_attributes_keygen(public_parameters, sk2, gid, user_attr2)
    user_sk2_bytes = objectToBytes(user_sk2, groupObj)
    return user_sk2_bytes
