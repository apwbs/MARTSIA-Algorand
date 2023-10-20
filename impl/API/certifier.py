from decouple import config
from Crypto.PublicKey import RSA
import ipfshttpclient
import sqlite3
import io
import rsa
import random
from datetime import datetime
import json
import os

MULTISIG = config('MULTISIG') == 1

authorities_names = ['UT', 'OU', 'OT', 'TU']


class Certifier():
    """ Manage the certification of the attributes of the actors

    A collectio of static methods to read the public keys of the actors, 
    the public key of the SKM and to certify the attributes of the actors
    """
    def certify(actors, roles):
        """ Read the public keys of actors and SKM, and certify the attributes of the actors

        Read the public keys of each actor in actors, then read the public key of the SKM 
        and certify the attributes of the actors

        Args:
            actors (list): list of actors
            roles (dict): a dict that map each actor to a list of its roles

        Returns:
            int : process instance id
        """
        for actor in actors:
            Certifier.__read_public_key__(actor)
        return Certifier.__attribute_certification__(roles)

    def read_public_key(actors):
        """ Read the public keys of each actor in actors
        
        Args:
            actors (list): list of actors
        """
        for actor in actors:
            Certifier.__read_public_key__(actor)


    def attribute_certification(roles):
        """ Certify the attributes of the actors

        Certify the attributes of the actors on the blockchain.
        The certification is performed by the SKM.

        Args:
            roles (dict): a dict that map each actor to a list of its roles
        
        Returns:
            int : process instance id
        """
        Certifier.__attribute_certification__(roles)


    def __read_public_key__(actor_name):
        """ Read the public and private key of an actor

        Read the public and private key of an actor from .env and store them in a SQLite3 database
        and on the blockchain on the PKReadersContract  

        Args:
            actor_name (str): name of the actor
        """
        api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

        print("Reading keys of " + actor_name)
        reader_address = config(actor_name + '_ADDRESS')
        private_key = config(actor_name + '_PRIVATEKEY')

        # Connection to SQLite3 reader database
        conn = sqlite3.connect('files/reader/reader.db')
        x = conn.cursor()

        # # Connection to SQLite3 data_owner database
        connection = sqlite3.connect('files/data_owner/data_owner.db')
        y = connection.cursor()

        keyPair = RSA.generate(bits=1024)

        f = io.StringIO()
        f.write('reader_address: ' + reader_address + '###')
        f.write(str(keyPair.n) + '###' + str(keyPair.e))
        f.seek(0)

        hash_file = api.add_json(f.read())
        print(f'ipfs hash: {hash_file}')

        # reader address not necessary because each user has one key. Since we use only one 'reader/client' for all the
        # readers, we need a distinction.
        x.execute("INSERT OR IGNORE INTO rsa_private_key VALUES (?,?,?)", (reader_address, str(keyPair.n), str(keyPair.d)))
        conn.commit()

        x.execute("INSERT OR IGNORE INTO rsa_public_key VALUES (?,?,?,?)",
                (reader_address, hash_file, str(keyPair.n), str(keyPair.e)))
        conn.commit()

        if MULTISIG:
            print(os.system('python3.10 blockchain/Controlled/multisig/PublicKeysReadersContract/PKReadersContractMain.py %s '
                        '%s %s' % (
                            private_key, config('APPLICATION_ID_PK_READERS'), hash_file)))
        else:
            print(os.system('python3.10 blockchain/PublicKeysReadersContract/PKReadersContractMain.py %s '
                        '%s %s' % (
                            private_key, config('APPLICATION_ID_PK_READERS'), hash_file)))

    def __store_process_id_to_env__(value):
        name = 'PROCESS_INSTANCE_ID'
        with open('.env', 'r', encoding='utf-8') as file:
            data = file.readlines()
        edited = False
        for line in data:
            if line.startswith(name):
                data.remove(line)
                break
        line = "\n" +  name + "=" + value + "\n"
        data.append(line)

        with open('.env', 'w', encoding='utf-8') as file:
            file.writelines(data)


    def __attribute_certification__(roles):
        """ Certify the attributes of the actors

        Certify the attributes of the actors on the blockchain.
        The certification is performed by the SKM.

        Args:
            roles (dict): a dict that map each actor to a list of its roles

        Returns:
            int : the process instance id of the certification process
        """

        api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001') # Connect to local IPFS node (creo un nodo locale di ipfs)

        #certifier_address = config('CERTIFIER_ADDRESS')
        certifier_private_key = config('CERTIFIER_PRIVATEKEY')

        # Connection to SQLite3 attribute_certifier database
        conn = sqlite3.connect('files/attribute_certifier/attribute_certifier.db') # Connect to the database
        x = conn.cursor()

        now = datetime.now()
        now = int(now.strftime("%Y%m%d%H%M%S%f"))
        random.seed(now)
        process_instance_id = random.randint(1, 2 ** 64)
        print(f'process instance id: {process_instance_id}')

        dict_users = {}
        for actor, list_roles in roles.items():
            dict_users[config(actor + '_ADDRESS')] = [str(process_instance_id)+'@'+name for name in authorities_names] + [role for role in list_roles]
        

        f = io.StringIO()
        dict_users_dumped = json.dumps(dict_users)
        f.write('"process_instance_id": ' + str(process_instance_id) + '####')
        f.write(dict_users_dumped)
        f.seek(0)

        file_to_str = f.read()

        hash_file = api.add_json(file_to_str)
        print(f'ipfs hash: {hash_file}')
        
        x.execute("INSERT OR IGNORE INTO user_attributes VALUES (?,?,?)",
                (str(process_instance_id), hash_file, file_to_str))
        conn.commit()

        print(os.system('python3.10 blockchain/AttributeCertifierContract/AttributeCertifierContractMain.py %s %s %s %s' %
                    (certifier_private_key, config('APPLICATION_ID_CERTIFIER'), process_instance_id, hash_file)))     

        Certifier.__store_process_id_to_env__(str(process_instance_id))

        return process_instance_id
    
    
    