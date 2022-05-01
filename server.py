import socket
import json
from _thread import start_new_thread
from sys import exc_info
from config import IP, PORT
from threading import Thread


class Server:
    def __init__(self, ipv4: str, port: int, clients=2):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ipv4
        self.port = port
        self.current_id = "0"
        self.clicked = {0: 15, 1: 15}
        self.clients = clients

        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.server, self.port))
        except socket.error as e:
            print(e)

        self.s.listen(clients)
        print("Waiting for a connection")
        self.accept_conn()

    def threaded_client(self, conn):
        conn.send(self.current_id.encode())
        self.current_id = str(int(self.current_id) + 1)
        while True:
            try:
                data = conn.recv(2048)
                reply = data.decode("utf-8")
                if not data:
                    conn.send("Goodbye".encode())
                    break
                else:
                    if DEBUG:
                        print("Received: " + reply)

                    # Seperates reply into a list [id, clicked]
                    reply = reply.split(":")
                    player_id = int(reply[0])

                    if int(reply[1]) == -1:
                        # -1 is the code for playing again
                        self.clicked[player_id] = -1
                    else:
                        # Will be 0 or 1 depending on if player clicked or not
                        clicked = int(reply[1])

                        # Gets the opponent's id
                        op_id = int(not player_id)
                        self.clicked[player_id] += clicked
                        self.clicked[op_id] += -clicked

                    if DEBUG:
                        print(f"Sending: {self.clicked}")

                conn.sendall(json.dumps(self.clicked).encode())
                # conn.sendall(str(self.clicked).encode())
                # Checks if both players have the -1 code (play again)
                if all([status == -1 for status in self.clicked.values()]) or set(self.clicked.values()) == {-1, 15}:
                    self.clicked = {0: 15, 1: 15}

            except Exception as e:
                # Prints exception with line number
                print(f"{e}, on line {exc_info()[2].tb_lineno}")
                break

        print("Connection Closed")
        conn.close()

    def accept_conn(self):
        while True:
            try:
                conn, addr = self.s.accept()
            except KeyboardInterrupt:
                print("Connection Closed")
                conn.close()
                break
            print("Connected to: ", addr)

            conn_thread = Thread(
                    target=self.threaded_client,
                    args=(conn,),
                    daemon=True)
            conn_thread.start()
            # start_new_thread(self.threaded_client, (conn,))


DEBUG = False
server = Server(IP, PORT, 2)
