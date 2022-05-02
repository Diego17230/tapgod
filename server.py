import socket
import json
from sys import exc_info
from config import IP, PORT
from threading import Thread, active_count


class Server:
    def __init__(self, ipv4: str, port: int):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ipv4
        self.port = port
        self.current_id = "0"
        self.clicked = {0: 15, 1: 15}
        self.conn_ids = []

        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.server, self.port))
        except socket.error as e:
            print(e)

        self.s.listen(2)
        print("Waiting for a connection")
        self.accept_conn()

    def threaded_client(self, conn):
        if self.current_id == "2":
            if active_count() == 2:
                # Resets current id
                self.current_id = "0"
            else:
                self.current_id = str(int(not self.conn_ids[0]))
        conn.send(self.current_id.encode())
        # Sets waiting status to client
        self.clicked[int(self.current_id)] = -2
        if all([status == -2 for status in self.clicked.values()]):
            self.clicked = {0: 15, 1: 15}
        thread_id = int(self.current_id)
        self.conn_ids.append(thread_id)
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
                # Checks if both players have the -1 code (play again)
                if all([status == -1 for status in self.clicked.values()]) or set(self.clicked.values()) == {-1, 15}:
                    self.clicked = {0: 15, 1: 15}
                for id_ in (0, 1):
                    if self.clicked[id_] == -1 and self.clicked[int(not id_)] == -2:
                        self.clicked[id_] = -2

            except Exception as e:
                # Prints exception with line number
                print(f"{e}, on line {exc_info()[2].tb_lineno}")
                break

        print("Connection Closed")
        conn.close()
        self.clicked = {0: -2, 1: -2}
        self.conn_ids.remove(thread_id)

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


DEBUG = True
Server(IP, PORT)
