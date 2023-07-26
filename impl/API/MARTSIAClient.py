from decouple import config
from hashlib import sha512
from MARTSIABridge import MARTSIABridge

### This class is equivalent to the content of ../client.py
class MARTSIAClient(MARTSIABridge):
    """A client to communicate with the MARTSIA SKM server

    A class to manage the communication with the MARTSIA SKM server

    Attributes:
        message_id (str): message id
        reader_address (str): reader address
        slice_id (str): slice id
    """
    def __init__(self, process_instance_id = config('PROCESS_INSTANCE_ID'), message_id = "", reader_address = "", gid = "", authority = 0):
        """Initialize the MARTSIAClient class
        
        Args:
            process_instance_id (int, optional): process instance id. Defaults to config('PROCESS_INSTANCE_ID').
            message_id (str, optional): message id. Defaults to "".
            reader_address (str, optional): reader address. Defaults to "".
            slice_id (str, optional): slice id. Defaults to "".
            
        """
        super().__init__(path_to_db='files/reader/reader.db', port=5060 + authority - 1, process_instance_id=process_instance_id)
        self.__setArgs__(message_id, reader_address, gid, authority)
        return

    def __setArgs__(self, message_id, reader_address, gid, authority):
        """Set the arguments of the class

        Set the message id, the reader address and the slice id of the class

        Args:
            message_id (str): message id
            reader_address (str): reader address
            gid (str): gid.
            authority (int): number of the authority to contact.
        """
        self.message_id = message_id
        self.reader_address = reader_address
        self.gid = gid
        if authority != 0:
            self.authority = 'Auth-' + str(authority)
        else: 
            self.authority = ''
        return

    def send(self, msg):
        """Send a message to the MARTSIA SKM server

        Send a message to the MARTSIA SKM server and receive a response

        Args:
            msg (str): message to send
        """
        message = msg.encode(self.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b' ' * (self.HEADER - len(send_length))
        self.conn.send(send_length)
        # print(send_length)
        self.conn.send(message)
        receive = self.conn.recv(6000).decode(self.FORMAT)
        if len(receive) != 0:
            if receive.startswith('number to sign:'):
                self.x.execute("INSERT OR IGNORE INTO handshake_number VALUES (?,?,?)",
                        (str(self.process_instance_id), self.authority, receive[16:]))
                self.connection.commit()
                return True
            #     x.execute("INSERT OR IGNORE INTO handshake_number VALUES (?,?,?)",
            #               (process_instance_id, authority, receive[16:]))
            #     connection.commit()
            self.x.execute("INSERT OR IGNORE INTO authorities_generated_decription_keys VALUES (?,?,?)",
                    (str(self.process_instance_id), self.authority, receive))
            self.connection.commit()
    
    def handshake(self):
        """Start the handshake with the MARTSIA SKM server"""
        self.send(self.authority + " - Start handshake§" + str(self.process_instance_id) + '§' + self.reader_address)
        self.disconnect()
        return
    
    def generate_key(self):
        """Generate the key for the reader"""
        signature_sending = self.sign_number(self.authority)
        self.send(self.authority + " - Generate your part of my key§" + self.gid + '§' + str(self.process_instance_id) + '§' + self.reader_address
        + '§' + str(signature_sending))
        self.disconnect()
        return


    def sign_number(self, authority_invoked):
        self.x.execute("SELECT * FROM handshake_number WHERE process_instance=? AND authority_name=?",
                (str(self.process_instance_id), authority_invoked))
        result = self.x.fetchall()
        number_to_sign = result[0][2]

        self.x.execute("SELECT * FROM rsa_private_key WHERE reader_address=?", (self.reader_address,))
        result = self.x.fetchall()
        private_key = result[0]

        private_key_n = int(private_key[1])
        private_key_d = int(private_key[2])

        msg = bytes(str(number_to_sign), 'utf-8')
        hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
        signature = pow(hash, private_key_d, private_key_n)
        # print("Signature:", hex(signature))
        return signature
