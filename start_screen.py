import pygame, sys
import button
from options import fade_out

pygame.init()

screen_width = 800
screen_height = 550
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Game')

def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

# LOAD IMAGES
BG = pygame.image.load("assets/Background.png")
BG = pygame.transform.scale(BG, (800, 550))
play_b = pygame.image.load("assets/Play_Rect.png")
quit_b = pygame.image.load("assets/Quit_Rect.png")
back_img = pygame.image.load('img/Icons/back.png').convert_alpha()
quit_img = pygame.image.load('img/Icons/quit.png').convert_alpha()
options_img = pygame.image.load('img/Icons/options.png').convert_alpha()

MENU_TEXT = get_font(80).render("Universifight", True, "#b68f40")
MENU_RECT = MENU_TEXT.get_rect(center=(400, 140))

# Buttons
PLAY_BUTTON = button.Button(screen, 215, 230, play_b, 370, 109)
QUIT_BUTTON = button.Button(screen, 223, 350, quit_b, 354, 109)


def loading_screen():
    loading_bar_width = 300
    loading_bar_height = 20
    loading_bar_x = (screen_width - loading_bar_width) // 2
    loading_bar_y = screen_height // 2 + 50

    for i in range(101):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((255, 255, 255))
        loading_text = get_font(50).render("Loading... ;)", True, (0, 0, 0))
        loading_text_rect = loading_text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(loading_text, loading_text_rect)

        pygame.draw.rect(screen, (0, 0, 0), (loading_bar_x, loading_bar_y, loading_bar_width, loading_bar_height), 2)
        fill_width = (i / 100) * (loading_bar_width - 4)
        pygame.draw.rect(screen, (0, 255, 0),
                         (loading_bar_x + 2, loading_bar_y + 2, fill_width, loading_bar_height - 4))

        pygame.display.flip()
        pygame.time.delay(20)

    fade_out(screen, 400)


class Start:
    run = True

    @staticmethod
    def draw_bg():
        screen.blit(BG, (0, 0))
        screen.blit(MENU_TEXT, MENU_RECT)

    @classmethod
    def play(cls):
        cls.run = False

    @classmethod
    def main_menu(cls):
        while cls.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            cls.draw_bg()

            if PLAY_BUTTON.draw():
                cls.play()

            if QUIT_BUTTON.draw():
                pygame.quit()
                sys.exit()

            pygame.display.update()

        loading_screen()
