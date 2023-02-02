# MARTSIA-Algornd

#### This repository contains the Ethereum-based version of the MARTSIA approach. 

### Guide

In order to run the system, the following libraries must be installed: python3.6, charm https://github.com/JHUISI/charm, rsa, web3 (python-version), python-decouple, truffle, sqlite3, ipfs.
It is recommended to install Docker and create a new image running Ubuntu 18.04 and then start one
or more containers from that image.

If the installation of 'charm' fails, try run these commands: 
1. sudo apt-get install libgmp3-dev libssl-dev
2. wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz
3. tar xvf pbc-0.5.14.tar.gz
4. cd pbc-0.5.14
5. ("sudo apt-get install flex bison" may be necessary, depending on what you already have on your system)
6. ./configure
7. make
8. sudo make install
9. pip install sovrin

If the installation fails, try these commands too:

1. sudo apt-get git
2. sudo apt-get install m4
3. git clone https://github.com/JHUISI/charm.git
4. cd charm
5. sudo ./configure.sh
6. sudo make
7. sudo make install
8. sudo ldconfig
9. sudo -H pip install sovrin

The first thing to do is to deploy the smart contract on the blockchain. 
To do that, create a Metamask wallet and fund an account with some Eth in the Goerli testnet with a Goerli faucet. 
Then create an account on Infura and obtain a key for the Goerli testnet.

Then, move in the 'blockchain' folder and create a '.env' file. Put two constants in there:
1. 'MNEMONIC'=the secret words of the Metamask wallet
2. 'PROJECT_ID'=the project ID obtained from Infura

After doing this, open a terminal and run 'truffle init'. Copy the folders 'contracts' and 'migrations' from the repo
and also the 'truffle-config.js' file. Then run 'truffle migrate --network goerli' and wait for the deployment of the 
contract on chain.

When these passages are completed, the databases for all the actors involved in the process need to be created. 
Move in the 'files' folder and create/copy the folders you need. To create a database run 'sqlite3 name_of_the_database.db'.
When inside that database run '.read database.sql' to instantiate the database with the right tables.

Once all these preliminary steps are completed, you can start running the actual code. And '.env' file must be created in order
to store all the necessary values of the constants. This file must be put in the 'architecture' or 'implementation' folder.

The first thing to do is provide a pair of private and public keys to the readers. Open a terminal and move in the 
architecture or implementation folder and run 'python3 rsa_public_keys.py'. In the file specify the actors
you intend to give a pair of keys to.

Next, open the attribute certifier file and write down the attributes that you intend to give to the actors of the system.
Then run 'python3 attribute_certifier.py' to store those values both in the certifier db and on chain. Copy the resulting
process_instance_id number in the .env file.

In order to instantiate the four authorities with multi-party computation open the four scripts, namely authority1.py, authority2.py
authority3.py and authority4.py. Consider the lines 185-189 of the first file and lines 182-186 of the remaining three.
Run the function 'save_authorities_names()' for all the authorities. Then, after all the authorities have completed this step,
run 'initial_parameters_hashed()' for all the authorities. Then run the other three functions with the same procedure, namely
run the third function for all the authorities, then the fourth function of all the authorities and so on. At the end of this 
procedure, the authorities are instantiated via multi-party computation, and they are ready to generate keys for the users.

To cipher a message and store it on the blockchain, open the 'data_owner.py' file. Firstly, run 'generate_pp_pk()' to 
instantiate the data owner, then modify the file 'data.json' with the data you want to cipher. Then, run the main() function, but
remember to modify the access policy and the entries that you need to cipher with a particular policy: lines 132-139.

To obtain a key from the authorities there are two ways. The first one is to send a request using an SLL client-server connection,
the second option is to send a key request on chain and get an IPFS link on chain to open. To send a request via SSL, open
the 'client.py' file, specify the constants like 'reader_address' and gid etc. and then run 'python 3 server_authority*.py'. Then, run
python3 client.py to firstly start the handshake function and then to ask for a key. Send these two messages in different
moments just commenting the action that you do not want to perform. Once you have obtained a part of a key from all the authorities,
open the 'reader.py' file and run the generate_public_parameters() function. Then put the right values in the message_id and
slice_id constants and run the main() function to read the message.

To use the second way to ask for a key, you need to run the 'send_key_request()'
function specifying the authority_address you want to invoke. Then, run the server_monitor_auth*.py script to let the 
authorities monitor the blockchain and react to a key request. The authority is going to read the key request, generate a key
and store it on chain. The user, in order to get the key, has to run the 'server_monitor_reader.py' script specifying the 
authority address invoked. The script is going to retrieve the key and store it in a private database. After having obtained 
all the key parts, just run the 'reader.py' script as described above.
