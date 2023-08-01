from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk import transaction
import argparse
from decouple import config

algod_address = config('ALGOD_ADDRESS')
algod_token = config('ALGOD_TOKEN')
headers = {
   "X-API-Key": algod_token,
}

DATAOWNERS = ['MANUFACTURER']
READER = ['SUPPLIER1', 'SUPPLIER2']

num_of_authoryties = 4
num_of_attributes_certifier = 4

algod_client = algod.AlgodClient(algod_token, algod_address, headers)


def generate_algorand_keypair(role = "My", verbose = True):
    private_key, address = account.generate_account()
    if verbose:
        print(role + " address: {}".format(address))
        print(role +" private key: {}".format(private_key))
        print(role +" passphrase: {}".format(mnemonic.from_private_key(private_key)))
        print("\n")
    return address, private_key

def add_address_to_env(name: str, overwrite : bool, pass_phrase : bool = False):
    with open('.env', 'r', encoding='utf-8') as file:
        data = file.readlines()
        skip = False
        for line in data:
            if line.startswith(name + '_ADDRESS'):
                if overwrite:
                    data.remove(line)
                else:
                    skip = True
                break
        for line in data:
            if line.startswith(name + '_PRIVATEKEY'):
                if overwrite:
                    data.remove(line)
                else:
                    skip = True
                break
        if skip:
            return
        address, private_key =  generate_algorand_keypair(role + "'", args.verbose)
        line = name + "_ADDRESS='" + address + "'\n"
        data.append(line)
        line = name + "_PRIVATEKEY='" + private_key + "'\n"
        data.append(line)
        with open('.env', 'w', encoding='utf-8') as file:
            file.writelines(data)
        if not pass_phrase:
            return
        passphrase = mnemonic.from_private_key(private_key)
        for line in data:
            if line.startswith('PASSPHRASE_' + name):
                data.remove(line)
                break
        line = "PASSPHRASE_CREATOR=" + passphrase + "'\n"  
        data.append(line)
        with open('.env', 'w', encoding='utf-8') as file:
            file.writelines(data)



parser = argparse.ArgumentParser()
parser.add_argument('-A' ,'--all', action='store_true')
parser.add_argument('-v' ,'--verbose', action='store_true')
parser.add_argument('-o', '--overwrite', action='store_true')

args = parser.parse_args()

overwrite = args.overwrite

if args.all:
    if input("This operation will reset address and private key stored in .env, press y to continue or any other key to abort: ").lower() != 'y':
        exit()
    with open('.env', 'r', encoding='utf-8') as file:
        data = file.readlines()
    if data[-1] != '\n':
        data.append("\n")
        with open('.env', 'w', encoding='utf-8') as file:
            file.writelines(data)
    for role in DATAOWNERS:
        add_address_to_env(name = 'DATAOWNER_'+ role, overwrite = overwrite)
    for role in READER:
        add_address_to_env(name = 'READER_' + role, overwrite = overwrite)
    for i in range(1, num_of_authoryties + 1):
        add_address_to_env(name = 'AUTHORITY' + str(i), overwrite = overwrite)
    for i in range(1, num_of_attributes_certifier + 1):
        add_address_to_env(name = 'CERTIFIER' + str(i), overwrite = overwrite)
    add_address_to_env(name = 'CREATOR', overwrite = overwrite, pass_phrase = True)
    print("All addresses and private keys are updated in .env")

else:
    generate_algorand_keypair()

#My address: LK7F5TUSXIEKLHN7SXJ6STLHVZEPT5AJKE5LEBM6FVZMZGCCHXYSII35C4
#My private key: mgvW3xKXsHwmCuLpmy1s5Pok6xzmjgLL+QbSg/pWwF1avl7OkroIpZ2/ldPpTWeuSPn0CVE6sgWeLXLMmEI98Q==
#My passphrase: infant flag husband illness gentle palace eye tilt large reopen current purity enemy depart couch moment gate transfer address diamond vital between unlock able cave
