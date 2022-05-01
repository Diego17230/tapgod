import pygame
from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    MOUSEBUTTONDOWN,
)
import sys
import socket
from ast import literal_eval
from config import IP, PORT, SCREEN_HEIGHT, SCREEN_WIDTH


class PlayerBar(pygame.sprite.Sprite):
    def __init__(self):
        self.surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT / 2))
        self.rect = self.surf.get_rect(topleft=(0, SCREEN_HEIGHT / 2))
        self.surf.fill("White")

    def handle_click(self, click_pos: tuple) -> bool:
        if self.rect.collidepoint(click_pos):
            return True
        return False


class Network:
    """
    A component to attach to clients of a server.

    Attributes
    ----------
    client : socket
        The socket server to set up a connection to.
    host : str
        The server ip to connect to.
    port : int
        The port to bind to on the server.
    addr : tuple
        The complete address to bind to.
    id : int
        The id number for the client.
    bytes : int
        The byte limit of data to decode.

    Methods
    -------
    connect()
        Get the client id and connect to the server.
    send(data)
        Encodes data to send to the server.
    """

    def __init__(self, ip: str, port: int, byte_limit: int):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = port
        self.addr = (self.host, self.port)
        self.id = self.connect()
        self.bytes = byte_limit

    def connect(self):
        """
        Connect to the server and return a client id.

        Returns
        -------
        int
            A number for the id of the client.
        """
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
        """
        Send data to the server.

        Parameters
        ----------
        data : str
            The data to encode and send to the server.

        Returns
        -------
        str
            The other client's reply after going through the server.
        """
        try:
            self.client.send(data.encode())
            return self.client.recv(self.bytes).decode()
        except socket.error as e:
            return str(e)


class Game:
    def __init__(self):
        # -Setup-
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("TapGod")

        # -Multiplayer-
        self.network = Network(
                IP,
                PORT,
                128)

        # -Game Stuff-
        self.player_bar = PlayerBar()
        self.clicked = False

    def send_clicked(self, debug=False):
        formatted = f"{self.network.id}:{int(self.clicked)}"
        reply = self.network.send(formatted)
        self.clicked = False
        if debug:
            print(reply)
        return literal_eval(reply)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False

                elif event.type == MOUSEBUTTONDOWN:
                    mouse_position = pygame.mouse.get_pos()
                    if self.player_bar.handle_click(mouse_position):
                        self.clicked = True

            # Sends the clicked status to the server
            reply = self.send_clicked()
            for player, score in reply.items():
                # print(player, score)
                pass

            self.screen.blit(self.player_bar.surf, self.player_bar.rect)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        pygame.display.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
