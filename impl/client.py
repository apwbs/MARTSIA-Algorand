import socket
import ssl
from decouple import config
from Crypto.PublicKey import RSA
from hashlib import sha512

app_id_box = config('APPLICATION_ID_BOX')

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
server_sni_hostname = 'example.com'
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


def sign_number(authority_invoked):
    with open('files/reader/number to sign_' + authority_invoked + '.txt', 'r') as r:
        number_to_sign = r.read()
    number_to_sign = int(number_to_sign)

    with open('files/keys_readers/handshake_private_key_' + str(reader_address) + '.txt', 'r') as pk:
        private_key = pk.read()
        private_key = private_key.split('###')

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
        if receive[:15] == 'number to sign:':
            with open('files/reader/number to sign_' + authority + '.txt', "w") as text_file:
                text_file.write(receive[16:])
        # with open('files/reader/user_sk1_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk2_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk3_' + str(process_instance_id) + '.txt', "w") as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk4_' + str(process_instance_id) + '.txt', "w") as text_file:
        #     text_file.write(receive)


manufacturer = config('READER_ADDRESS_MANUFACTURER')
electronics = config('READER_ADDRESS_SUPPLIER1')
mechanics = config('READER_ADDRESS_SUPPLIER2')
reader_address = manufacturer
process_instance_id = int(app_id_box)
gid = "bob"

authority = 'Auth1'

send("Auth1 - Start handshake||" + reader_address)
# send("Auth2 - Start handshake||" + reader_address)
# send("Auth3 - Start handshake||" + reader_address)
# send("Auth4 - Start handshake||" + reader_address)

# signature_sending = sign_number(authority)

# send("Auth1 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address + '||' +
#      str(signature_sending))
# send("Auth2 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address + '||' +
#      str(signature_sending))
# send("Auth3 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address + '||' +
#      str(signature_sending))
# send("Auth4 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address + '||' +
#      str(signature_sending))
# exit()
# input()

send(DISCONNECT_MESSAGE)
