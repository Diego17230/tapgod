import pygame
from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    MOUSEBUTTONDOWN,
)
import sys
import socket
import json
from config import IP, PORT, SCREEN_HEIGHT, SCREEN_WIDTH


class Network:
    def __init__(self, ip: str, port: int):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ip
        self.port = port
        self.addr = (self.host, self.port)
        self.id = self.connect()

    def connect(self):
        self.client.connect(self.addr)
        return self.client.recv(2048).decode()

    def send(self, data):
        try:
            self.client.send(data.encode())
            return self.client.recv(128).decode()
        except socket.error as e:
            return str(e)


class AgainButton(pygame.sprite.Sprite):
    def __init__(self, font: pygame.font.Font, black_background):
        if black_background:
            colors = ("White", "Black")
        else:
            colors = ("Black", "White")
        self.colors = colors
        self.surf = font.render("Again", True, *colors)
        self.rect = self.surf.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150))

        # -Visuals-
        self.border = pygame.Rect(
                (0, 0), self.rect.inflate(20, 20).size)
        # Recenters the border
        self.border.center = self.rect.center
        self.inflate = True
        self.font = font
        self.font_size = 30
        self.timer = 0

    def reset(self):
        black_background = self.colors[0] == "White"
        # Resets button
        self.__init__(
                pygame.font.SysFont("Comic Sans MS", 30),
                black_background)

    def inflate_surf(self, plus: int):
        self.font = pygame.font.SysFont("Comic Sans MS", self.font_size + plus)
        self.font_size += plus
        self.surf = self.font.render("Again", True, *self.colors)
        self.rect = self.surf.get_rect(
                center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150))
        self.border = pygame.Rect(
                (0, 0), self.rect.inflate(20, 20).size)
        self.border.center = self.rect.center

    def update(self):
        if not self.timer % 3:
            if self.inflate:
                self.inflate_surf(2)
            else:
                self.inflate_surf(-2)
        if self.rect.w > 110 or self.rect.w < 60:
            self.inflate = not self.inflate
        self.timer += 1

    def blit(self, screen: pygame.surface.Surface):
        screen.blit(self.surf, self.rect)
        # Draws border
        pygame.draw.rect(screen, self.colors[0], self.border, 5, 10)


class TapParticle:
    def __init__(self, center):
        self.center = center
        self.radius = 2
        self.alive = True
        self.rad_increase = 1

    def draw(self, screen):
        pygame.draw.circle(screen, "Black", self.center, self.radius, 3)
        self.radius += self.rad_increase
        if self.radius <= 40:
            self.rad_increase += 0.25
        else:
            # Slows down radius increase at the end
            self.rad_increase = 0.4
        if self.radius >= 48:
            self.alive = False


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


class Game:
    def __init__(self):
        # -Setup-
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Tap God")
        self.network = Network(IP, PORT)

        # -Game Stuff-
        self.player_bar = PlayerBar()
        self.clicked = False
        self.frozen = True
        self.font = pygame.font.SysFont("Comic Sans MS", 30)
        self.text = None
        self.again_button = None
        self.again = False
        self.particles = []
        self.opening_screen = 0
        self.started = False

    @staticmethod
    def load_response(reply):
        reply = json.loads(reply)
        for key in ("0", "1"):
            reply[int(key)] = reply.pop(key)
        return reply

    def send_clicked(self, debug=False):
        formatted = f"{self.network.id}:{int(self.clicked)}"
        reply = self.network.send(formatted)
        self.clicked = False
        if debug:
            print(reply)
        return self.load_response(reply)

    def send_again(self, debug=False):
        formatted = f"{self.network.id}:-1"
        reply = self.network.send(formatted)
        if debug:
            print(reply)
        return self.load_response(reply)

    def handle_clicks(self, clicks):
        click_total = clicks[int(self.network.id)]
        if click_total == -2:
            click_total = 15
            self.text = self.font.render("Waiting for opponent", True, "Red")
        self.player_bar.set_y(click_total)
        if not click_total and not self.frozen:
            self.end_match(False)
        if not clicks[int(not int(self.network.id))] and not self.frozen:
            self.end_match(True)

    def end_match(self, win):
        self.frozen = True
        if win:
            message = "You win!"
        else:
            message = "You lose..."
        self.text = self.font.render(message, True, "Red")
        self.again_button = AgainButton(self.font, not win)

    @staticmethod
    def center_surf(surf: pygame.surface.Surface) -> tuple:
        return ((SCREEN_WIDTH / 2) - (surf.get_width() / 2),
                (SCREEN_HEIGHT / 2))

    def run(self):
        running = True
        while running:
            mouse_position = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False

                elif event.type == MOUSEBUTTONDOWN:
                    if self.player_bar.rect.collidepoint(mouse_position) and not self.frozen:
                        self.clicked = True
                        self.particles.append(TapParticle(mouse_position))
                    if self.again_button is not None and self.again_button.rect.collidepoint(mouse_position):
                        self.again = True
                        self.again_button = None
                        self.text = self.font.render(
                                "Waiting for opponent",
                                True,
                                "Red")

            if self.started:
                # -Opening Screen-
                if self.opening_screen == 300:
                    self.text = self.font.render("Match begun!", True, "Red")
                for num in (3, 2, 1):
                    frame = 210 + ((num - 3) * 60)
                    if self.opening_screen == frame:
                        self.text = self.font.render(str(num), True, "Red")
                if self.opening_screen == 30:
                    self.text = self.font.render("TAP!", True, "Red")
                if self.opening_screen == 1:
                    self.frozen = False
                    self.text = None
                if self.opening_screen:
                    self.opening_screen -= 1

            if not self.again:
                # Sends the clicked status to the server
                reply = self.send_clicked()
                if any([status == -2 for status in reply.values()]):
                    self.frozen = True
                elif not self.started and all([status == 15 for status in reply.values()]) and not self.opening_screen:
                    self.started = True
                    self.opening_screen = 300
                self.handle_clicks(reply)
            else:
                reply = self.send_again()
                if all([status == -1 for status in reply.values()]) or set(reply.values()) == {-1, 15}:
                    self.again = False
                    self.again_button = None
                    self.text = None
                    self.opening_screen = 300

            self.screen.fill("Black")
            self.screen.blit(self.player_bar.surf, self.player_bar.rect)
            if self.text is not None:
                self.screen.blit(self.text, self.center_surf(self.text))
            if self.again_button is not None:
                if self.again_button.rect.collidepoint(mouse_position):
                    self.again_button.update()
                else:
                    self.again_button.reset()
                self.again_button.blit(self.screen)

            for i, particle in sorted(enumerate(self.particles), reverse=True):
                # The functions applying to particles allows for removal
                # during iteration, which can cause problems if not
                # attended to
                particle.draw(self.screen)
                if not particle.alive:
                    self.particles.pop(i)

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        pygame.display.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
