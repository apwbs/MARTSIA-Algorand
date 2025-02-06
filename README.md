# MARTSIA-Algorand

**Multi-Authority Approach to Transaction Systems for Interoperating Applications**  
****

This repository contains the Algorand implementation of the MARTSIA approach presented in the paper entitled: "[MARTSIA: Enabling Data Confidentiality for Blockchain-based Process Execution](https://arxiv.org/abs/2303.17977)".

In this version, the request and transmission of key segments between the Reader and Authorities are performed via **TLS connections**.

## Guide

### Requirements
There are two ways to run the system. The first one is to download the corresponding Docker Image for the Algorand implementation stored at the [Docker Hub](https://hub.docker.com/repository/docker/apwbs/martsia/general). This is the simplest and fastest way to run the system.

Otherwise (not so much recommended), install Docker and create a new image running Ubuntu 18.04 and then start one
or more containers from that image. To do this, firstly use the DockerFile running `docker build -t image_name PATH_TO_THE_DOCKERFILE/DockerFiles/`
to create a docker image. Then run `docker run -it -v PATH_TO_MARTSIA-AlgorandFOLDER/MARTSIA-Algorand/:/MARTSIA-Algorand image_name`
to create a container starting from the image created in the previous step. To run the first instance of a container run
`docker start container_name`, then run `docker attach container_name`. To run other independent instances of the same container run
`docker exec -it container_name bin/bash`. Running other instances (from the second on) of the same container with 
`docker start` and `docker attach` will not make them independent. Every command in one instance will be applied also in the
other instances. Using `docker exec` you can open as many independent containers as you like.

The following libraries must be installed inside the container: python3.6, python3.10, [charm](https://github.com/JHUISI/charm), 
[rsa](https://pypi.org/project/rsa/), [web3](https://web3py.readthedocs.io/en/stable/quickstart.html) (python-version), 
[python-decouple](https://pypi.org/project/python-decouple/), [PyTeal](https://pyteal.readthedocs.io/en/stable/installation.html) (version 0.20.1 or 0.23.0 for python3.10), 
[Algorand-sdk](https://py-algorand-sdk.readthedocs.io/en/latest/)(for python3.10), sqlite3 (python3 -m pip install sqlite3), 
ipfs (for local node) run:
1. python3.6 -m pip install ipfshttpclient
2. wget https://dist.ipfs.io/go-ipfs/v0.7.0/go-ipfs_v0.7.0_linux-amd64.tar.gz
3. tar -xvzf go-ipfs_v0.7.0_linux-amd64.tar.gz
4. cd go-ipfs
5. sudo bash install.sh
6. ipfs init
7. ipfs daemon (in another terminal window).


If the installation of 'charm' fails, try running these commands: 
1. sudo apt-get install libgmp3-dev libssl-dev
2. wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz
3. tar xvf pbc-0.5.14.tar.gz
4. cd pbc-0.5.14
5. ("sudo apt-get install flex bison" may be necessary, depending on what you already have on your system)
6. ./configure
7. make
8. sudo make install
9. pip install sovrin

If the installation fails again, try these commands too:
1. sudo apt-get git
2. sudo apt-get install m4
3. git clone https://github.com/JHUISI/charm.git
4. cd charm
5. sudo ./configure.sh
6. sudo make
7. sudo make install
8. sudo ldconfig
9. sudo -H pip install sovrin

In order to check if 'charm' is successfully installed, try run `python3.6` (inside the container) and then `import charm`. 
If there are no errors displayed, the package is correctly installed.

### Contracts deployment

The first thing to do is to deploy the smart contracts (applications id) on the blockchain (we use the testnet). 
To do that, create an Algorand account running `python3.10 account_creation.py`. To obtain an 'algod_address' and 
an algo_token, create an account on [PureStake](https://developer.purestake.io/). Then, fund the account with the 
[Algorand dispenser for the testnet](https://bank.testnet.algorand.network/).

For actually create the contracts, in the Main files of the application_ids (smart contracts that you can find in the blockchain folder), 
modify the 'algod_address' constant with the testnet-algorand API (ps2) and copy your token in the 'algo_token' constant. 
Change the mnemonic constant with the one obtained during the generation of the account.
Run the contractMainCreation file with `python3.10 name_of_contractMainCreation.py` to generate the '.teal' and '.json' files 
and to generate, upload and fund the contract. Once obtained all the application ids, copy them in the right constant in the
'.env' file.
For the box contract, firstly generate the '.teal' and '.json' files running `python3.10 BoxContract.py`. Then run the
MainCreation script to obtain an application id and the change the one obtained in the 'fund_program' function to fund it.
Remember to properly comment and uncomment the `###1st run###` and `###2nd run###` lines in the `__main__`.

### Database creation

When these passages are completed, the databases for all the actors involved in the process need to be created. 
Move in the 'files' folder and create/copy the folders you need. To create a database run `sqlite3 name_of_the_database.db`.
When inside that database run `.read database.sql` to instantiate the database with the right tables.

### Key pairs generation

Once all these preliminary steps are completed, you can start running the actual code. An '.env' file must be created in order
to store all the necessary values of the constants. This file must be put in the 'architecture' or 'implementation' folder.

The first thing to do is provide a pair of private and public keys to the readers. Open a container terminal and move in the 
architecture or implementation folder and run `python3.6 rsa_public_keys.py`. In the file, specify the actors you want 
to give a key pair.

### Attributes assignment

Next, open the attribute certifier file and write down the attributes that you intend to give to the actors of the system.
Then run `python3.6 attribute_certifier.py` to store those values both in the certifier db and on chain. Copy the resulting
process_instance_id number in the .env file.

### Authorities instantiation

In order to instantiate the four authorities with multi-party computation, open authority1.py, authority2.py
authority3.py and authority4.py. Consider the lines highlighted with `###LINES###` in the files.
Run the function 'save_authorities_names()' for all the authorities. Then, after all the authorities have completed this step,
run 'initial_parameters_hashed()' for all the authorities. Then run the other three functions with the same procedure, namely
run the third function for all the authorities, then the fourth function of all the authorities and so on. At the end of this 
procedure, the authorities are instantiated via multi-party computation, and they are ready to generate keys for the users.

### Message ciphering and delivering

To cipher a message and store it on the blockchain, open the 'data_owner.py' file. Firstly, run 'generate_pp_pk()' to 
instantiate the data owner, then modify the file 'data.json' with the data you want to cipher. Then, run the main() function, but
remember to modify the access policy and the entries that you need to cipher with a particular policy: 
lines highlighted with `###LINES###` in the file.

### Key requests

To obtain a key from the authorities there are two ways. The first one (the one in the main) is to send a request using an SLL client-server connection,
the second option is to send a key request on chain and get an IPFS link on chain to open. To send a request via SSL, open
the 'client.py' file, specify the constants like 'reader_address', 'gid' etc. and then run `python3.6 server_authority*.py`. 
Then, run `python3.6 client.py` to firstly start the handshake function and then to ask for a key. Send these two messages in different
moments just commenting the action that you do not want to perform. 

To use the second way (the one in the 'key_on_block' branch) to ask for a key, you need to run the 'send_key_request()'
function specifying the authority_address you want to invoke. Then, run `python3.6 server_monitor_auth*.py` to let the 
authorities monitor the blockchain and react to a key request. The authority is going to read the key request, generate a key
and store it on chain. The user, in order to get the key, has to run `python3.6 server_monitor_reader.py` script specifying the 
authority address invoked. The script is going to retrieve the key and store it in a private database. After having obtained 
all the key parts, just run the 'reader.py' script as described below.

### Message reading

Once you have obtained a part of a key from all the authorities,
open the 'reader.py' file and run the generate_public_parameters() function. Then put the right values in the 'message_id' and
'slice_id' constants and run the main() function to read the message.

## MARTSIA main GitHub page
For more details about MARTSIA, refer to the [main MARTSIA GitHub page](https://github.com/apwbs/MARTSIA).
