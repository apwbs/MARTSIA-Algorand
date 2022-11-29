import socket
import ssl
import threading
import authority2_keygeneration
import authority_keyretrieve
from decouple import config
authority2_address = config('AUTHORITY2_ADDRESS')

HEADER = 64
PORT = 5055
server_cert = 'client-server/Keys/server.crt'
server_key = 'client-server/Keys/server.key'
client_certs = 'client-server/Keys/client.crt'
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

"""
creation and connection of the secure channel using SSL protocol
"""
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(certfile=server_cert, keyfile=server_key)
context.load_verify_locations(cafile=client_certs)
bindsocket = socket.socket()
bindsocket.bind(ADDR)
bindsocket.listen(5)

"""
function triggered by the client handler. Here starts the ciphering of the message with the policy.
"""


def retrieve_public_key_auth2(process_instance_id):
    return authority_keyretrieve.retrieve_public_key(process_instance_id, authority2_address)


def retrieve_public_params_auth2(process_instance_id):
    return authority_keyretrieve.retrieve_public_parameters(process_instance_id, authority2_address)


def generate_key_auth2(gid, process_instance_id, reader_address):
    return authority2_keygeneration.generate_user_key(gid, process_instance_id, reader_address)


"""
function that handles the requests from the clients. There is only one request possible, namely the 
ciphering of a message with a policy.
"""


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                connected = False
            # print(f"[{addr}] {msg}")
            # conn.send("Msg received!".encode(FORMAT))
            message = msg.split('||')
            if message[0] == "Auth2 - Send me the public keys of all the authorities and the public parameters":
                pp_pk2 = retrieve_public_key_auth2(message[1])
                conn.send(pp_pk2[0] + b'\n' + pp_pk2[1])
            if message[0] == "Auth2 - Send me the public parameters":
                pp2 = retrieve_public_params_auth2(message[1])
                conn.send(pp2[0] + b'\n' + pp2[1])
            if message[0] == "Auth2 - Generate your part of my key":
                user_sk2 = generate_key_auth2(message[1], message[2], message[3])
                conn.send(user_sk2)

    conn.close()


"""
main function starting the server. It listens on a port and waits for a request from a client
"""


def start():
    bindsocket.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        newsocket, fromaddr = bindsocket.accept()
        conn = context.wrap_socket(newsocket, server_side=True)
        thread = threading.Thread(target=handle_client, args=(conn, fromaddr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[STARTING] server is starting...")
start()
