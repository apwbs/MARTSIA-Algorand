import sqlite3
from flask import Flask, request, jsonify
import json
from decouple import config
from hashlib import sha512
from certifier import Certifier
from MARTSIAClient import MARTSIAClient
from MARTSIAReader import MARTSIAReader
from MARTSIADataOwner import MARTSIADataOwner
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)

    
numberOfAuthorities = 4

def getClientArgs(request):
    """ Read the arguments from the client request

    This function is used to get the arguments from the client request
    and return them in the correct format to be used by the MARTSIAClient

    Args:
        request: the request from the client
    
    Returns:
        reader_address: the address of the reader
        message_id: the id of the message
        slice_id: the id of the slice
        process_id: the id of the process (process_instance_id)
    """
    process_id = request.json.get('process_id')
    reader_address = request.json.get('reader_address')
    gid = request.json.get('gid')

    '''
    print("Reader_address is: " + reader_address)
    print("Message_id is: " + message_id)
    if slice_id is not None:
        print("Slice_id is: " + slice_id)
    print("Process_id is: " + str(process_id))
    '''
    return reader_address, process_id, gid

@app.route('/')
def go_home():
    """ A simple request to the API welcome message

    This function is used to test if the API is working correctly
    during the development phase

    Returns:
        A welcome message
    """
    return 'Welcome to the MARTSIA API', 200

#### Request from client to read ####
@app.route('/read/' , methods=['GET', 'POST'], strict_slashes=False)
def read():
    """
    This function is used to read a file from the reader
    
    Args:
        message_id: the id of the message
        slice_id: the id of the slice
    """

    reader = MARTSIAReader(request.json.get('process_id'), numberOfAuthorities)
    
    if request.json.get('generate'):
        print("Generating public parameters")
        reader.generate_public_parameters()

    message_id = request.json.get('message_id')
    slice_id = request.json.get('slice_id')
    gid = request.json.get('gid')
    if message_id == '' or slice_id == '' or gid == '':
        return "Missing parameters" , 400
    reader.read(message_id, slice_id, gid)
    return "Read completed", 200
    


#### Request from client to SKM Server ####
@app.route('/client/handshake/' , methods=['GET', 'POST'], strict_slashes=False)
def client_handshake():
    """ Request to the SKM Server to handshaking

    This function is used to send a request to the SKM Server
    to make an handshake with the reader
 
    Args:
        reader_address: the address of the reader
        message_id: the id of the message
        process_id: the id of the process (process_instance_id)

    Returns:
        The status of the request, 200 if the handshake is completed
    """
    reader_address, process_id, gid = getClientArgs(request)
    if reader_address == '' or process_id == '' or gid == '':
        return "Missing parameters" , 400   
    for i in range(1, numberOfAuthorities + 1):
        client = MARTSIAClient(reader_address=reader_address, process_instance_id=process_id, gid=gid, authority=i)
        client.handshake()
    #client.disconnect()
    return "Handshake completed" , 200

@app.route('/client/generateKey/' , methods=['POST'], strict_slashes=False)
def generateKey():
    """ Request to the SKM Server to generate a key

    This function is used to send a request to the SKM Server
    to generate a key for the reader.
    The key is generated only if the handshake is completed.
    
    Args:
        reader_address: the address of the reader
        message_id: the id of the message   
        process_id: the id of the process (process_instance_id)
        
    Returns:
        The status of the request, 200 if the key is generated
    """
    reader_address, process_id, gid= getClientArgs(request)
    if reader_address == '' or process_id == '' or gid == '':
        return "Missing parameters" , 400   
    for i in range(1, numberOfAuthorities + 1):
        client = MARTSIAClient(reader_address=reader_address, process_instance_id=process_id, gid=gid, authority=i)
        client.generate_key()
    return "Key generated", 200

##### Request from Data Owner to SDM Server #####

@app.route('/dataOwner/generate_pp_pk/' , methods=['POST'], strict_slashes=False)
def data_owner_handshake():
    """ Request to the SDM Server to handshaking

    This function is used to send a request to the SDM Server
    to make an handshake with the MANUFACTURER

    Args:
        process_id: the id of the process (process_instance_id)
    
    Returns:
        The status of the request, 200 if the handshake is completed
    """
    data_owner = MARTSIADataOwner(process_instance_id=request.json.get('process_id'))
    data_owner.generate_pp_pk()
    return "Handshake completed"

@app.route('/dataOwner/cipher/', methods=['POST'], strict_slashes=False)
def cipher():
    """ Request to the SDM Server to cipher the message from the Manufacturer

    This function is used to send a request to the SDM Server
    to cipher the message from the Manufacturer, setting the policy
    of the decryption.

    Args:
        message: the message to cipher, it's a string read from a json file
        entries:  a list of list of label of the message that has the same policy
        policy: a list containing for each group of label the process_id associated
            and the policy, defining which actors can access the data

    Returns:
        The status of the request, 200 if the cipher is completed
    """
    message = request.json.get('message')
    if len(message) == 0:
        return "Missing parameters (message)" , 401
    entries = request.json.get('entries')
    policy = request.json.get('policy')
    if len(entries) == 0:
        return "Missing parameters (entries)" , 402
    if len(policy) == 0:
        return "Missing parameters (policy)" , 403
    #TODO: Check if it is mandatory
    if len(entries) != len(policy):
        print("Entries and policy legth doesn't match")
        print("Entries: " + str(len(entries)))
        print(entries)
        print("Policy: " + str(len(policy)))
        print(policy)
        return "Entries and policy legth doesn't match" , 410 

    #entries_string = '###'.join(str(x) for x in entries)
    #policy_string = '###'.join(str(x) for x in policy)

    row_id = request.json.get('id')
    if row_id == None:
        row_id = -1
    else:
        row_id = int(row_id)
    data_owner = MARTSIADataOwner(process_instance_id=request.json.get('process_id'))
    data_owner.cipher_data(message, entries, policy)
    return "Cipher completed"

    
@app.route('/certification/', methods=['POST'],strict_slashes=False)
def certification():
    """ Request to to certify the actors
    
    This function is used to send a request read the actors' public keys,
    the skm's public key and to certify the actors involved in the process

    Args:
        actors: the list of actors involved in the process
        roles: a dictionary that contains for each actor the list of roles associated
    
    Returns:
        The process instance id of the certification process and
        the status of the request, 200 if the certification is completed
    """
    actors = request.json.get('actors')
    roles = request.json.get('roles')
    process_instance_id = Certifier.certify(actors, roles)
    return str(process_instance_id), 200

@app.route('/certification/readpublickey/', methods=['POST'], strict_slashes=False)
def read_public_key():
    """ Read the public keys of the actors

    This function is used to read the public keys of the actors
    that are involved in the process
    
    Args:
        actors: the list of actors involved in the process
        roles: a dictionary that contains for each actor the list of roles associated

    Returns:
        The status of the request, 200 if the keys are read correctly
    """
    actors = request.json.get('actors')
    #roles = request.json.get('roles')
    Certifier.read_public_key(actors)
    return "Public keys read"

@app.route('/certification/attributecertification/', methods=['POST'], strict_slashes=False)
def attribute_certification():
    """ Certificate the actors

    This function is used to certificate the actors
    that are involved in the process
    
    Args:
        actors: the list of actors involved in the process
        roles: a dictionary that contains for each actor the list of roles associated
        
    Returns:
        The process instance id of the certification process and
        the status of the request, 200 if the certification is completed
    """
    #actors = request.json.get('actors')
    roles = request.json.get('roles')
    process_instance_id =  Certifier.attribute_certification(roles)
    return str(process_instance_id), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8888")
