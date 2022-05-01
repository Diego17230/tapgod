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


class Network:
    def __init__(self, ip: str, port: int, byte_limit: int):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = port
        self.addr = (self.host, self.port)
        self.id = self.connect()
        self.bytes = byte_limit

    def connect(self):
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
        try:
            self.client.send(data.encode())
            return self.client.recv(self.bytes).decode()
        except socket.error as e:
            return str(e)


class PlayerBar(pygame.sprite.Sprite):
    def __init__(self):
        self.surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT / 2))
        self.rect = self.surf.get_rect(topleft=(0, SCREEN_HEIGHT / 2))
        self.surf.fill("White")

    def set_y(self, amount):
        self.surf = pygame.Surface(
                (SCREEN_WIDTH, (SCREEN_HEIGHT / 30) * amount))
        self.surf.fill("White")
        self.rect = self.surf.get_rect(bottom=SCREEN_HEIGHT)

    def handle_click(self, click_pos: tuple) -> bool:
        if self.rect.collidepoint(click_pos):
            return True
        return False


class Game:
    def __init__(self):
        # -Setup-
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Tap God")
        self.network = Network(IP, PORT, 128)

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

    def handle_clicks(self, clicks):
        for player_id, click_total in clicks.items():
            if player_id == int(self.network.id):
                self.player_bar.set_y(click_total)

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
            self.handle_clicks(reply)

            self.screen.fill("Black")
            self.screen.blit(self.player_bar.surf, self.player_bar.rect)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        pygame.display.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
