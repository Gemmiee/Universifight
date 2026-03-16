import random
from symtable import Class
import pygame, sys, pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame.transform import scale
import button

# ------------ IMPORT PY ARXEIA -----------
from start_screen import Start
from chest_scene import chest
from boss_battles import engineering_boss, mathematics_boss, biology_boss
from mini_monsters1 import mini_monsters1, mini_monsters2, mini_monsters3
from walking_scene import walking, first
from resting import start_camp
from options import *
from intro import play_intro
# -----------------------------------------

pygame.init()

clock = pygame.time.Clock()
fps = 60

# game window
bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel

screen = pygame.display.get_surface()
if screen is None:
    screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Game')

brightness_level = 1.0

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Foithths Fight nyaa ^w^')

back_img = pygame.image.load('img/Icons/back.png').convert_alpha()
quit_img = pygame.image.load('img/Icons/quit.png').convert_alpha()
options_img = pygame.image.load('img/Icons/options.png').convert_alpha()

# ----------------------  KSEKINAEI TO STARTING SCREEN KAI TO INTRO  -----------------------
menu = Start()
menu.main_menu()
fade_in(screen, 400)
status, brightness_level = play_intro(brightness_level)
if status == "SKIP":
    # AN KANEI SKIP TO INTRO
    fade_out(screen, 400)
    fade_in(screen, 400)
    pass
# ------------------------------------------------------------------------------------------

# FONTS
font = pygame.font.SysFont('Times New Roman', 26)

# COLORS
red = (255, 0, 0)
green = (0, 255, 0)
white = (255, 255, 255)
black = (0, 0, 0)
yellow = (255, 215, 0)
dark_red = (100, 30, 30)
dark_green = (30, 100, 30)
light_blue = (173, 216, 230)


# IMAGES
background_img = pygame.image.load('assets/Stages/Stage1/1.png').convert_alpha()
panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()
restart_img = pygame.image.load('img/Icons/restart.png').convert_alpha()
victory_img = pygame.image.load('img/Icons/victory.png').convert_alpha()
defeat_img = pygame.image.load('img/Icons/defeat.png').convert_alpha()
sword_img = pygame.image.load('img/Icons/sword.png').convert_alpha()
tutorial_img = pygame.image.load('img/Background/background.png').convert_alpha()


# draw the text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, colour):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, colour)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        # move damage text up
        self.rect.y -= 1
        # delete the text after a few seconds
        self.counter += 1
        if self.counter > 30:
            self.kill()


damage_text_group = pygame.sprite.Group()


class Fighter():
    def __init__(self, x, y, name, max_hp, strength, potions,stress,max_stress, scale=0.15,action_wait_time=90):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.strength = strength
        self.base_strength = strength
        self.start_potions = potions
        self.potions = potions
        self.stress = stress
        self.max_stress = max_stress
        self.alive = True
        self.scale = scale
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        self.action_wait_time = action_wait_time
        self.buff_bonus = 0  # how much bonus is active
        self.buff_rounds = 0
        self.strength = strength
        self.base_strength = strength  # source of truth for ATK

        if self.name == 'Rogue' or self.name == 'Warrior' or self.name == 'Arbalest' or self.name == 'Elf':
            self.action_dict = {
                'Idle': 0,
                'Attack': 1,
                'Hurt': 2,
                'Death': 3,
                'Run': 4,
                'Agro': 5
            }
            animation_types = {
                'Idle': 8,
                'Attack': 4,
                'Hurt': 4,
                'Death': 6,
                'Run': 4,
                'Agro': 8
            }
        else:
            self.action_dict = {
                'Idle': 0,
                'Attack': 1,
                'Hurt': 2,
                'Death': 3
            }
            animation_types = {
                'Idle': 10,
                'Attack': 5,
                'Hurt': 4,
                'Death': 6
            }

        # Load animations
        for anim_name in self.action_dict:
            temp_list = []
            num_frames = animation_types.get(anim_name, 0)
            for i in range(num_frames):
                img = pygame.image.load(f'img/{self.name}/{anim_name}/{i}.png')
                img = pygame.transform.scale(img,(img.get_width() * self.scale, img.get_height() * self.scale))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        # for debug in case of missiing frames
        for anim_name in self.action_dict:
            num_frames = animation_types.get(anim_name, 0)
            if num_frames == 0:
                print(f"WARNING: No frames found for {self.name} animation: {anim_name}")

    def update(self):
        animation_cooldown = 100

        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1


            if self.frame_index >= len(self.animation_list[self.action]):
                # Stay on last frame if dead
                if self.action == self.action_dict['Death']:
                    self.frame_index = len(self.animation_list[self.action]) - 1

                # Loop Agro animation
                elif self.action == self.action_dict.get('Agro'):
                    self.frame_index = 0

                # After Attack or Hurt, go back to Agro (looping)
                elif self.action in [self.action_dict['Attack'], self.action_dict['Hurt']]:
                    if 'Agro' in self.action_dict:
                        self.action = self.action_dict['Agro']
                        self.frame_index = 0
                    else:
                        self.action = self.action_dict['Idle']
                        self.frame_index = 0

                # All other actions (like Idle), loop
                else:
                    self.frame_index = 0

        # Failsafe: reset frame index if somehow out of range
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

        # Set current image
        self.image = self.animation_list[self.action][self.frame_index]

    def idle(self):
        if self.action != 0:
            self.action = 0
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()


    def agro(self):
        if self.action != self.action_dict['Agro']:
            self.action = self.action_dict['Agro']
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()


    def get_strength(self):
        """Base + buff; halve if stress >= 100."""
        base = self.base_strength + getattr(self, "buff_bonus", 0)
        if getattr(self, "stress", 0) >= 100:
            base = max(1, int(base * 0.5))
        return base


    def attack(self, target):
        rand = random.randint(-5, 5)
        damage = self.get_strength() + rand  # debuffed atk
        target.hp -= damage
        target.hurt()
        if target.hp < 1:
            target.hp = 0
            target.alive = False
            target.death()
        damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
        damage_text_group.add(damage_text)
        self.action = 1
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()


    def hurt(self):
        self.action = 2
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()


    def death(self):
        self.action = 3
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()


    def run(self):
        if len(self.animation_list) > 4 and self.action != 4:
            self.action = 4
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()


    def reset(self):
        self.alive = True
        self.potions = self.start_potions
        self.hp = self.max_hp
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()


    def draw(self):
        screen.blit(self.image, self.rect)

def init_party():
    warrior = Fighter(310, 250, 'Warrior', 200, 15, 1, 0, 200, scale=0.17, action_wait_time=30); warrior.hp_bar_offset = (4, 222)
    rogue   = Fighter(215, 260, 'Rogue',   200, 11, 2, 0, 200, scale=0.15, action_wait_time=30); rogue.hp_bar_offset   = (3, 200)
    elf     = Fighter(130, 260, 'Elf',     200, 10, 4, 0, 200, scale=0.15, action_wait_time=30); elf.hp_bar_offset     = (4, 201)
    arbalest= Fighter( 50, 260, 'Arbalest',200, 9, 3, 0, 200, scale=0.15, action_wait_time=30); arbalest.hp_bar_offset= (5, 201)
    return [warrior, rogue, elf, arbalest]

def reset_module_flags():
    try:
        import mini_monsters1 as mm; mm.TUTORIAL_SHOWN_MINI = False
    except Exception: pass
    try:
        import chest_scene as cs; cs.TUTORIAL_SHOWN_CHEST = False
    except Exception: pass

def run_scene(fn, *args):
    result = fn(*args)
    if isinstance(result, tuple) and result[0] == "RESTART":
        return "RESTART", result[1]
    return "OK", result


MAIN_THEME = "assets/Dusk at the Market.mp3"
CAMP_THEME = "assets/The Lachrimae Pavan on Lute.mp3"
STAGE3_THEME = "assets/Annbjørg Lien - Den Bortkomne Sauen.mp3"
STAGE2_THEME = "assets/The City Gates.mp3"
ENDING_THEME = "assets/Suonatore di Liuto - Kevin MacLeod.mp3"


CURRENT_WORLD_THEME = MAIN_THEME

def set_world_theme(theme_path, volume=1.0):
    """Switch background/world music now and remember it for later resumes."""
    global CURRENT_WORLD_THEME
    CURRENT_WORLD_THEME = theme_path
    play_music(theme_path, crossfade_ms=800, fade_ms=800, volume=volume)
    return theme_path

def switch_theme(theme_path, volume=1.0):
    """Return a 'scene' function that only switches music (fits into your scenes list)."""
    def _fn(hero_list, brightness_level):
        set_world_theme(theme_path, volume=volume)
        return brightness_level
    return _fn


def camp_wrapper(hero_list, brightness_level):
    # switch to camp music
    play_music(CAMP_THEME, crossfade_ms=800, fade_ms=800, volume=0.95)
    result = start_camp(hero_list, brightness_level)
    # restore world theme
    play_music(CURRENT_WORLD_THEME, crossfade_ms=800, fade_ms=800, volume=1.0)
    return result



# --- Victory Scene ---

def victory_scene(hero_list, brightness_level, image_path="assets/Victory/finale.png"):
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    fps = 60

    bg = pygame.image.load('img/Background/EndingScene.png').convert()

    # Text setup
    font_small = pygame.font.SysFont("Times New Roman", 22)
    color_main = (255, 255, 255)
    color_shadow = (0, 0, 0)

    lines = [
        "With the final blow, the land falls silent.",
        "Weapons and gears rest; the sun goes down peacefully.",
        "Our heroes walk, smiling, and a little less stressed.",
        "Thanks for playing!"
    ]

    # Typewriter + auto-advance config
    ms_per_char      = 28     # typing speed
    auto_advance_ms  = 1000   # pause after a line finishes
    final_hold_ms    = 800    # small hold before we show restart
    margin_x = 30
    base_y  = 0
    line_h  = 26

    # Buttons
    restart_btn = button.Button(screen, 580, 470, restart_img, 200, 60)

    # Fade in
    screen.blit(bg, (0, 0))
    Options.apply_brightness_overlay(screen, brightness_level)
    fade_in(screen, 450)

    current_line = 0
    typed_len = 0
    start_time = pygame.time.get_ticks()
    line_done_time = None
    finished_time = None  # when the last line finished
    fast_forward = False
    finished = False      # becomes True after the last line completes + hold

    def draw_all(finalize_current=False):
        screen.blit(bg, (0, 0))

        # Draw completed lines
        for i in range(min(current_line, len(lines))):
            text = lines[i]
            img_s = font_small.render(text, True, color_shadow)
            img = font_small.render(text, True, color_main)
            y = base_y + i * line_h
            screen.blit(img_s, (margin_x + 1, y + 1))
            screen.blit(img, (margin_x, y))

        # Draw current line (only if there still is one)
        if current_line < len(lines):
            part = lines[current_line]
            if not finalize_current:
                part = part[:typed_len]
            y = base_y + current_line * line_h
            img_s = font_small.render(part, True, color_shadow)
            img = font_small.render(part, True, color_main)
            screen.blit(img_s, (margin_x + 1, y + 1))
            screen.blit(img, (margin_x, y))

    while True:
        dt = clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    fade_out(screen, 400)
                    return brightness_level
                if event.key == pygame.K_SPACE and not finished:
                    fast_forward = True


        if not finished:
            if current_line < len(lines):
                if line_done_time is None:
                    elapsed = pygame.time.get_ticks() - start_time
                    typed_len = len(lines[current_line]) if fast_forward else min(
                        len(lines[current_line]),
                        int(elapsed / ms_per_char)
                    )
                    if typed_len >= len(lines[current_line]):
                        line_done_time = pygame.time.get_ticks()
                        fast_forward = False
                else:
                    if pygame.time.get_ticks() - line_done_time >= auto_advance_ms:
                        current_line += 1
                        if current_line >= len(lines):
                            finished_time = pygame.time.get_ticks()
                        else:
                            typed_len = 0
                            start_time = pygame.time.get_ticks()
                            line_done_time = None

            if finished_time is not None and pygame.time.get_ticks() - finished_time >= final_hold_ms:
                finished = True

        # --- Draw for this frame ---
        # Draw background + text
        draw_all(finalize_current=(line_done_time is not None))

        # If finished, draw the restart button on bottom
        if finished:
            if restart_btn.draw():
                fade_out(screen, 500)
                return ("RESTART", brightness_level)

        Options.apply_brightness_overlay(screen, brightness_level)
        pygame.display.update()


while True:
    hero_list = init_party()
    brightness_level = 1.0

    # mousikh genikh
    play_music(MAIN_THEME, crossfade_ms=600, fade_ms=800)

    # SKHNES POU THA PAIKSOUN
    scenes = [
        first,             # INTRO WALK
        #mini_monsters1,    # FIRST FIGHT
        #walking,           # THEN WALK
        chest,
        mini_monsters1,
        chest,
        engineering_boss,  # boss fight
        camp_wrapper,      # camp me mousikh

        # STADIO DYO:
        switch_theme(STAGE2_THEME, volume=1.0),

        first,
        chest,
        mini_monsters2,
        walking,
        mini_monsters2,
        mathematics_boss,
        camp_wrapper,

        # STADIO TRIA:
        switch_theme(STAGE3_THEME, volume=1.0),
        first,
        mini_monsters3,
        chest,
        walking,
        mini_monsters3,
        walking,
        biology_boss,
        switch_theme(ENDING_THEME, volume=1.0),
        victory_scene
    ]

    restarted = False
    for scene in scenes:
        status, brightness_level = run_scene(scene, hero_list, brightness_level)
        if status == "RESTART":
            import game_state
            game_state.stage = 0
            game_state.passes = 0
            game_state.passesFIRST = 0
            reset_module_flags()
            restarted = True
            break

    if restarted:
        continue  # rebuild party and re-run from the top
    else:
        break     # finished playthrough without pressing Restart


pygame.quit()
