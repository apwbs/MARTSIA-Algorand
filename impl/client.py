import socket
import ssl
from decouple import config

HEADER = 64
PORT = 5065
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
        # with open('files/reader/user_sk1_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk2_' + str(process_instance_id) + '.txt', 'w') as text_file:
        #     text_file.write(receive)
        # with open('files/reader/user_sk3_' + str(process_instance_id) + '.txt', "w") as text_file:
        #     text_file.write(receive)
        with open('files/reader/user_sk4_' + str(process_instance_id) + '.txt', "w") as text_file:
            text_file.write(receive)


manufacturer = config('READER_ADDRESS_MANUFACTURER')
electronics = config('READER_ADDRESS_SUPPLIER1')
mechanics = config('READER_ADDRESS_SUPPLIER2')
reader_address = mechanics
process_instance_id = 1387640806
gid = "bob"
# send("Auth1 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address)
# send("Auth2 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address)
# send("Auth3 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address)
send("Auth4 - Generate your part of my key||" + gid + '||' + str(process_instance_id) + '||' + reader_address)
# exit()
# input()

send(DISCONNECT_MESSAGE)
