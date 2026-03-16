import random
import sys

import pygame
import button

# ------------ IMPORT PY ARXEIA -----------
from options import Options
# party layout persistence
from party_layout import restore_party_layout, save_party_layout, freeze_targets_at_current
import game_state
# -----------------------------------------

pygame.init()

clock = pygame.time.Clock()
fps = 60

bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel
SHOW_TUTORIAL_MINI = False
tutorial_step = 1           # DEIXNEI TO TUTORIAL, YES!


font = pygame.font.SysFont('Times New Roman', 26)
small_font = pygame.font.SysFont('Times New Roman', 20)


# Walking formations for spawn
WALKING_OFFSCREEN_SLOTS = [(-50, 250), (-145, 260), (-230, 260), (-310, 260)]
WALKING_ONSCREEN_SLOTS  = [(310, 250), (215, 260), (130, 260), (50, 260)]  # used by first()


screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Game')

back_img = pygame.image.load('img/Icons/back.png').convert_alpha()
quit_img = pygame.image.load('img/Icons/quit.png').convert_alpha()
options_img = pygame.image.load('img/Icons/options.png').convert_alpha()
tutorial_img1 = pygame.image.load("img/Tutorials/tut1.png").convert_alpha()
scaled_tut1 = pygame.transform.scale(tutorial_img1, (550, 400))


# variables gia to paixnidi kai thn maxh
current_fighter = 1
action_wait_time = 90
stress_chance = 0.2



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
background_img = pygame.image.load('assets/Stages/Stage1/4.png').convert_alpha()
background_img2 = pygame.image.load('assets/Stages/Stage2/1.png').convert_alpha()
background_img3 = pygame.image.load('assets/Stages/Stage3/1.png').convert_alpha()
panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()
restart_img = pygame.image.load('img/Icons/restart.png').convert_alpha()
victory_img = pygame.image.load('img/Icons/victory.png').convert_alpha()
defeat_img = pygame.image.load('img/Icons/defeat.png').convert_alpha()
sword_img = pygame.image.load('img/Icons/sword.png').convert_alpha()


# DRAW TEXT
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# DRAW BACKGROUND, gia enallagh background xrisimopoioume metablhtes apo to "game_state"
def draw_bg():
    if game_state.stage == 0:
        screen.blit(background_img, (0, 0))
    elif game_state.stage == 1:
        screen.blit(background_img2, (0, 0))
    else:
        screen.blit(background_img3, (0, 0))


# DRAW THE PANEL
def draw_panel(current_fighter, hero_list, bandit_list):
    screen.blit(panel_img, (0, screen_height - bottom_panel))

    if current_fighter in hero_list:
        face = pygame.image.load(f'img/FaceIcons/{current_fighter.name}.png').convert_alpha()
        face_scaled = pygame.transform.scale(face, (200, 100))
        screen.blit(face_scaled, (-40, 440))

        # HERO STATS
        draw_text(f'{current_fighter.name}', font, white, 20, screen_height - bottom_panel + 15)
        draw_text(f'HP: {current_fighter.hp}', font, red, 280, screen_height - bottom_panel + 20)
        draw_text(f'ST: {current_fighter.stress}', font, light_blue, 280, screen_height - bottom_panel + 50)

        # --- ATK + buff (prwth seira) ---
        base = getattr(current_fighter, "base_strength", current_fighter.strength)
        buff = getattr(current_fighter, "buff_bonus", 0)
        eff_atk = base + buff
        if getattr(current_fighter, "stress", 0) >= 100:
            eff_atk = max(1, int(eff_atk * 0.5))

        atk_line = f"ATK: {eff_atk}"
        if getattr(current_fighter, "buff_rounds", 0) > 0:
            atk_line += f" (+{buff}) [{current_fighter.buff_rounds}]"

        # auto einai gia reposition
        atk_x = 200
        atk_y = screen_height - bottom_panel + 86
        draw_text(atk_line, small_font, yellow, atk_x, atk_y)

        # --- Stressed badge (deuterh seira) ---
        if getattr(current_fighter, "stress", 0) >= 100:
            stressed_y = atk_y + small_font.get_height() + 2
            draw_text("stressed -50%", small_font, light_blue, atk_x, stressed_y)

    else:
        draw_text('Enemy turn', font, red, 20, screen_height - bottom_panel + 10)

    # show names and hp
    for count, i in enumerate(bandit_list):
        draw_text(f'{i.name} HP: {i.hp}', font, red,
                  550, (screen_height - bottom_panel + 10) + count * 60)



class Fighter():
    def __init__(self, x, y, name, max_hp, strength, potions,stress,max_stress, scale=0.15,action_wait_time=90):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.strength = strength
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

        # Load animations in order of action_dict
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
        # Inside your __init__, you could log missing animations:
        for anim_name in self.action_dict:
            num_frames = animation_types.get(anim_name, 0)
            if num_frames == 0:
                print(f"WARNING: No frames found for {self.name} animation: {anim_name}")

    def update(self):
        animation_cooldown = 100

        # Time-based frame update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # If animation finished, handle based on action type
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

                # All other actions (like Idle), just loop
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


    def attack(self, target):
        rand = random.randint(-5, 5)
        damage = self.strength + rand
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


class Enemy(Fighter):
    def __init__(self, x, y, name, max_hp, strength, potions, scale):
        # enemy animations
        animation_types = {
            'Idle': 8,
            'Attack': 8,
            'Hurt': 3,
            'Death': 10
        }
        if name == 'Knight':
            animation_types['Run'] = 9

        #
        super().__init__(x, y, name, max_hp, strength, potions, 0, 0, scale=scale,action_wait_time=90)
        self.stress = 0
        self.max_stress = 0

    def handle_stress_or_damage(self, damage, target):
        global stress_chance
        if random.random() <= stress_chance:
            target.stress += damage
            if target.stress > target.max_stress:
                target.stress = target.max_stress
            damage_text = DamageText(target.rect.centerx, target.rect.y + 20, str(damage), light_blue)
            damage_text_group.add(damage_text)
        else:
            target.hp -= damage
            if target.hp < 1:
                target.hp = 0
                target.alive = False
                target.death()
            target.hurt()
            damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
            damage_text_group.add(damage_text)

    def attack(self, target):
        rand = random.randint(-5, 5)
        damage = self.strength + rand
        self.handle_stress_or_damage(damage, target)
        self.action = 1
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

    def run(self):
        if len(self.animation_list) > 4 and self.action != 4:
            self.action = 4
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()



class HealthBar():
    def __init__(self, x, y, hp, max_hp):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = max_hp

    def draw(self, hp):
        self.hp = hp
        ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, red, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, green, (self.x, self.y, 150 * ratio, 20))


class StressBar():
    def __init__(self, x, y, st, max_st):
        self.x = x
        self.y = y
        self.st = st
        self.max_st = max_st

    def draw(self, st):
        self.st = st
        ratio = self.st / self.max_st
        pygame.draw.rect(screen, white, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, light_blue, (self.x, self.y, 150 * ratio, 20))



class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, colour):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, colour)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        self.rect.y -= 1
        self.counter += 1
        if self.counter > 30:
            self.kill()


damage_text_group = pygame.sprite.Group()





def roll_turn_order(all_fighters):
    order = []
    for fighter in all_fighters:
        if fighter.alive:
            roll = random.randint(1, 20)   # to zari
            order.append((roll, fighter))
    order.sort(key=lambda x: x[0], reverse=True)
    print("\n--- New Round ---")
    for roll, fighter in order:
        print(f"{fighter.name} rolled {roll}")
    return [f for _, f in order]



def draw_turn_order(bandit_list,turn_order,turn_index):
    x_offset = 20
    y_offset = 10
    box_width = 120
    box_height = 40
    padding = 10

    for i, fighter in enumerate(turn_order):
        if not fighter.alive:
            continue  # skip dead fighters

        # current turn pairnei YELLOW
        bg_color = yellow if i == turn_index else (dark_red if fighter in bandit_list else dark_green)

        # Box kai border
        pygame.draw.rect(screen, bg_color, (x_offset, y_offset, box_width, box_height))
        pygame.draw.rect(screen, black, (x_offset, y_offset, box_width, box_height), 2)

        if hasattr(fighter, "portrait") and fighter.portrait:
            portrait = pygame.transform.scale(fighter.portrait, (box_width - 4, box_height // 2))
            screen.blit(portrait, (x_offset + 2, y_offset + 2))
        else:
            draw_text(fighter.name[:11], font, white, x_offset + 5, y_offset + 5)

        x_offset += box_width + padding


def draw_monsters_scene1(hero_list,bandit_list):
    draw_bg()

    # DRAW HEROES
    for hero in hero_list:
        hero.update()
        hero.draw()

    # DRAW ENEMIES
    for bandit in bandit_list:
        bandit.update()
        bandit.draw()

    # DRAW UI ELEMENTS
    damage_text_group.update()
    damage_text_group.draw(screen)

# BUTTONS
potion_button = button.Button(screen, 120, screen_height - bottom_panel + 80, potion_img, 50, 50)
options_button = button.Button(screen, 650, 365, options_img, 120, 30)


def party_offscreen_right(heroes, threshold_x=900):
    """Return True when every *alive* hero has moved past threshold_x."""
    alive = [h for h in heroes if getattr(h, "alive", True)]
    if not alive:
        return False
    return all(h.rect.centerx > threshold_x for h in alive)



# ---------------------------------------- GAME LOOP ---------------------------------------

def walking(hero_list, brightness_level):
    game_state.passes = game_state.passes + 1
    moving_right = False
    moving_left = False


    restore_party_layout(hero_list, fallback_slots=WALKING_OFFSCREEN_SLOTS)

    alive_in_order = sorted(
        [h for h in hero_list if getattr(h, "alive", True)],
        key=lambda h: getattr(h, "order", 0)
    )
    for i, h in enumerate(alive_in_order):
        slot = WALKING_OFFSCREEN_SLOTS[min(i, len(WALKING_OFFSCREEN_SLOTS) - 1)]
        h.rect.center = slot
        h.target = pygame.math.Vector2(slot)


    bandit_list = []

    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero_list[0].hp, hero_list[0].max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero_list[0].stress, hero_list[0].max_stress)

    run = True

    while run:
        clock.tick(fps)
        draw_monsters_scene1(hero_list, bandit_list)

        current_actor = hero_list[0]
        draw_panel(current_actor, hero_list, bandit_list)
        hero_health_bar.draw(current_actor.hp)
        hero_stress_bar.draw(current_actor.stress)


        for fighter in hero_list:
            fighter.update()
            fighter.draw()
            if not getattr(fighter, "alive", True):
                continue  # SKIP THE DEAD, OI NEKROI DEN EXOUN MINI HP BARS

            bar_width = 50
            bar_height = 6

            offset_x, offset_y = getattr(fighter, "hp_bar_offset", (0, -10))

            bar_x = fighter.rect.centerx - bar_width // 2 + offset_x
            bar_y = fighter.rect.top + offset_y

            pygame.draw.rect(screen, red, (bar_x, bar_y, bar_width, bar_height))
            hp_ratio = fighter.hp / fighter.max_hp
            stress_ratio = fighter.stress / fighter.max_stress
            pygame.draw.rect(screen, green, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
            pygame.draw.rect(screen, white, (bar_x, bar_y + bar_height + 2, bar_width, bar_height))
            pygame.draw.rect(screen, light_blue, (bar_x, bar_y + bar_height + 2, int(bar_width * stress_ratio), bar_height))



        damage_text_group.update()
        damage_text_group.draw(screen)

        attack = False
        potion = False
        target = None
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()


        if options_button.draw():
            options_menu = Options(screen, screen_width, screen_height, font, back_img, quit_img)
            brightness_level = options_menu.run(draw_bg, draw_text, brightness_level)

        if potion_button.draw():
            potion = True
        draw_text(str(hero_list[0].potions), font, red, 175, screen_height - bottom_panel + 100)


        for hero in hero_list:
            if not getattr(hero, "alive", True):
                continue
            if moving_right:
                hero.run()
                hero.rect.x += 6
            elif moving_left:
                hero.run()
                hero.rect.x -= 3
            else:
                hero.idle()


        if party_offscreen_right(hero_list, 850):
            save_party_layout(hero_list)
            run = False

        if game_state.passes == 2:
            game_state.stage = 1
        if game_state.passes == 3:
            game_state.stage = 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_d:       # koumpi D
                    moving_right = True
                if event.key == pygame.K_a:       # koumpi A gia pisw
                    moving_right = False
                    moving_left = True
                if event.key == pygame.K_LEFT:
                    moving_left = True
                    moving_right = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    moving_right = False
                if event.key == pygame.K_d:
                    moving_right = False
                if event.key == pygame.K_a:
                    moving_left = False
                if event.key == pygame.K_LEFT:
                    moving_left = False

        Options.apply_brightness_overlay(screen, brightness_level)
        pygame.display.update()


    return brightness_level


# -------------------------- ARXIKO SCENE, IDANIKO GIA TUTORIAL ------------------------------

def first(hero_list, brightness_level):
    global TUTORIAL_SHOWN_MINI, tutorial_step
    game_state.passesFIRST = game_state.passesFIRST + 1
    moving_right = False
    moving_left = False

    for i in range(4):
        if i == 0:
            hero_list[i].rect.center = (310, 250)
            hero_list[i].action = 0
        elif i == 1:
            hero_list[i].rect.center = (215, 260)
            hero_list[i].action = 0
        elif i == 2:
            hero_list[i].rect.center = (130, 260)
            hero_list[i].action = 0
        else:
            hero_list[i].rect.center = (50, 260)
            hero_list[i].action = 0


    bandit_list = []

    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero_list[0].hp, hero_list[0].max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero_list[0].stress, hero_list[0].max_stress)

    run = True

    while run:
        clock.tick(fps)
        draw_monsters_scene1(hero_list, bandit_list)

        current_actor = hero_list[0]
        draw_panel(current_actor, hero_list, bandit_list)
        hero_health_bar.draw(current_actor.hp)
        hero_stress_bar.draw(current_actor.stress)

        # ------------- TUTORIAL PAUSE -------------
        if tutorial_step:
            # handle only minimal events (quit + click to advance)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if tutorial_step == 1:
                        tutorial_step = 0           # DONE WITH TUTORIAL
                        TUTORIAL_SHOWN_MINI = True  # NEVER SHOW AGAIN AFTER ONE TIME


            img = scaled_tut1
            rect = img.get_rect(center=(400, 250))
            screen.blit(img, rect)

            Options.apply_brightness_overlay(screen, brightness_level)
            pygame.display.update()
            continue
        # -----------------------------------------

        for fighter in hero_list:
            fighter.update()
            fighter.draw()
            if not getattr(fighter, "alive", True):
                continue  # skip mini HP/stress bars for dead characters

            bar_width = 50
            bar_height = 6

            offset_x, offset_y = getattr(fighter, "hp_bar_offset", (0, -10))

            bar_x = fighter.rect.centerx - bar_width // 2 + offset_x
            bar_y = fighter.rect.top + offset_y

            pygame.draw.rect(screen, red, (bar_x, bar_y, bar_width, bar_height))
            hp_ratio = fighter.hp / fighter.max_hp
            stress_ratio = fighter.stress / fighter.max_stress
            pygame.draw.rect(screen, green, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
            pygame.draw.rect(screen, white, (bar_x, bar_y + bar_height + 2, bar_width, bar_height))
            pygame.draw.rect(screen, light_blue, (bar_x, bar_y + bar_height + 2, int(bar_width * stress_ratio), bar_height))



        damage_text_group.update()
        damage_text_group.draw(screen)

        attack = False
        potion = False
        target = None
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()


        if options_button.draw():
            options_menu = Options(screen, screen_width, screen_height, font, back_img, quit_img)
            brightness_level = options_menu.run(draw_bg, draw_text, brightness_level)

        if potion_button.draw():
            potion = True
        draw_text(str(hero_list[0].potions), font, red, 175, screen_height - bottom_panel + 100)


        for hero in hero_list:
            if not getattr(hero, "alive", True):
                continue
            if moving_right:
                hero.run()
                hero.rect.x += 6
            elif moving_left:
                hero.run()
                hero.rect.x -= 3
            else:
                hero.idle()


        if party_offscreen_right(hero_list, 820):
            run = False

        if game_state.passesFIRST == 2:
            game_state.stage = 1
        if game_state.passesFIRST == 3:
            game_state.stage = 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_d:       # koumpi D
                    moving_right = True
                if event.key == pygame.K_a:       # koumpi A gia pisw
                    moving_right = False
                    moving_left = True
                if event.key == pygame.K_LEFT:
                    moving_left = True
                    moving_right = False
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    moving_right = False
                if event.key == pygame.K_d:
                    moving_right = False
                if event.key == pygame.K_a:
                    moving_left = False
                if event.key == pygame.K_LEFT:
                    moving_left = False

        Options.apply_brightness_overlay(screen, brightness_level)
        pygame.display.update()


    return brightness_level
