import pygame
from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    MOUSEBUTTONDOWN,
)
import sys

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750


class Game:
    def __init__(self):
        # -Setup-
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("TapGod")

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
                    pass

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        pygame.display.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
