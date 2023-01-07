from charm.toolbox.pairinggroup import *
from maabe_class import *
from decouple import config
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import json
import sys
import retriever
import sqlite3

app_id_attribute = config('APPLICATION_ID_CERTIFIER')


def retrieve_public_parameters(process_instance_id):
    # Connection to SQLite3 authority1 database
    conn = sqlite3.connect('files/authority1/authority1.db')
    x = conn.cursor()

    x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (process_instance_id,))
    result = x.fetchall()
    public_parameters = result[0][2].encode()

    # with open('files/authority1/public_parameters_authority1_' + str(process_instance_id) + '.txt', 'rb') as ppa2:
    #     public_parameters = ppa2.read()

    return public_parameters


def generate_user_key(gid, process_instance_id, reader_address):
    # Connection to SQLite3 authority1 database
    conn = sqlite3.connect('files/authority1/authority1.db')
    x = conn.cursor()

    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

    response = retrieve_public_parameters(process_instance_id)
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F

    # with open('files/authority1/private_key_au1_' + str(process_instance_id) + '.txt', 'rb') as sk1r:
    #     sk1 = sk1r.read()
    # sk1 = bytesToObject(sk1, groupObj)

    x.execute("SELECT * FROM private_keys WHERE process_instance=?", (process_instance_id,))
    result = x.fetchall()
    sk1 = result[0][1]
    sk1 = bytesToObject(sk1, groupObj)

    # keygen Bob
    attributes_ipfs_link = retriever.retrieveReaderAttributes(app_id_attribute, process_instance_id)
    getfile = api.cat(attributes_ipfs_link)
    getfile = getfile.split(b'\n')
    attributes_dict = json.loads(getfile[1].decode('utf-8'))
    user_attr1 = attributes_dict[reader_address]
    user_attr1 = [k for k in user_attr1 if k.endswith('@UT')]
    user_sk1 = maabe.multiple_attributes_keygen(public_parameters, sk1, gid, user_attr1)
    user_sk1_bytes = objectToBytes(user_sk1, groupObj)
    return user_sk1_bytes
