import socket
import ssl
from decouple import config
from Crypto.PublicKey import RSA
from hashlib import sha512
import sqlite3
import argparse

# Connection to SQLite3 reader database
connection = sqlite3.connect('files/reader/reader.db')
x = connection.cursor()

app_id_box = config('APPLICATION_ID_BOX')

"""
creation and connection of the secure channel using SSL protocol
"""


def sign_number(authority_invoked):
    x.execute("SELECT * FROM handshake_number WHERE process_instance=? AND authority_name=?",
              (process_instance_id, authority_invoked))
    result = x.fetchall()  
    print("result:  \t", result)
    number_to_sign = result[0][2]
    # with open('files/reader/number to sign_' + authority_invoked + '.txt', 'r') as r:
    #     number_to_sign = r.read()
    # number_to_sign = int(number_to_sign)

    x.execute("SELECT * FROM rsa_private_key WHERE reader_address=?", (reader_address,))
    result = x.fetchall()
    private_key = result[0]

    # with open('files/keys_readers/handshake_private_key_' + str(reader_address) + '.txt', 'r') as pk:
    #     private_key = pk.read()
    #     private_key = private_key.split('###')

    private_key_n = int(private_key[1])
    private_key_d = int(private_key[2])

    msg = bytes(str(number_to_sign), 'utf-8')
    hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
    signature = pow(hash, private_key_d, private_key_n)
    # print("Signature:", hex(signature))
    return signature


"""
function to handle the sending and receiving messages.
"""


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)
    receive = conn.recv(6000).decode(FORMAT)
    if len(receive) != 0:
        if receive.startswith('number to sign:'):
            x.execute("INSERT OR IGNORE INTO handshake_number VALUES (?,?,?)",
                    (str(process_instance_id), authority, receive[16:]))
            connection.commit()
            return True
        x.execute("INSERT OR IGNORE INTO authorities_generated_decription_keys VALUES (?,?,?)",
                  (process_instance_id, authority, receive))
        connection.commit()

        # with open('files/reader/user_sk1_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk2_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk3_' + str(process_instance_id) + '.txt', "w") as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk4_' + str(process_instance_id) + '.txt', "w") as text_file:
        #     text_file.write(receive)


manufacturer = p('DATAOWNER_MANUFACTURER_ADDRESS')
electronics = config('READER_SUPPLIER1_ADDRESS')
mechanics = config('READER_SUPPLIER2_ADDRESS')
reader_address = manufacturer
process_instance_id = int(app_id_box)
gid = "bob"

parser = argparse.ArgumentParser(description="Client request details", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-g', '--gid', type=str, default=gid, help='Slice ID')
parser.add_argument('-rd', '--reader_address', type=str, default=reader_address, help='Reader address')
parser.add_argument('-a', '--authority', type=int, default=1, help='Authority')
parser.add_argument('-hs', '--handshake', action='store_true', help='Handshake')
parser.add_argument('-gk', '--generate_key', action='store_true', help='Generate key')
args = parser.parse_args()

gid = args.gid
reader_address = args.reader_address

authority = 'Auth-' + str(args.authority)

HEADER = 64
PORT = 5060 + args.authority - 1
FORMAT = 'utf-8'
server_sni_hostname = 'Sapienza'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "172.17.0.2"
ADDR = (SERVER, PORT)
server_cert = 'client-server/Keys/server.crt'
client_cert = 'client-server/Keys/client.crt'
client_key = 'client-server/Keys/client.key'

"""
creation and connection of the secure channel using SSL protocol
"""

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=server_cert)
context.load_cert_chain(certfile=client_cert, keyfile=client_key)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn = context.wrap_socket(s, server_side=False, server_hostname=server_sni_hostname)
conn.connect(ADDR)

if args.handshake:
    send(authority + " - Start handshake§" + str(process_instance_id) + '§' + reader_address)

elif args.generate_key:
    signature_sending = sign_number(authority)
    send(authority + " - Generate your part of my key§" + gid + '§' + str(process_instance_id) + '§' + reader_address
        + '§' + str(signature_sending))

# exit()
# input()

send(DISCONNECT_MESSAGE)