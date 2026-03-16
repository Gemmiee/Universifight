import random
import pygame, sys
import button

# ------------ IMPORT PY ARXEIA -----------
from options import Options, fade_out
import game_state
from resting import start_camp
from walking_scene import walking
from party_layout import (
    restore_party_layout,
    save_party_layout,
    freeze_targets_at_current,
    reflow_alive_into_front,
    PARTY_SLOTS,
)
# -----------------------------------------

current_fighter = 1

bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Game')

clock = pygame.time.Clock()
fps = 60
stress_chance = 0.4

# GAME FONTS
font = pygame.font.SysFont('Times New Roman', 26)
small_font = pygame.font.SysFont('Times New Roman', 20)

# XRWMATA
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
background_img2 = pygame.image.load('assets/Stages/Stage2/3.png').convert_alpha()
background_img3 = pygame.image.load('assets/Stages/Stage3/4.png').convert_alpha()
panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()
victory_img = pygame.image.load('img/Icons/victory.png').convert_alpha()
defeat_img = pygame.image.load('img/Icons/defeat.png').convert_alpha()
sword_img = pygame.image.load('img/Icons/sword.png').convert_alpha()
go_to_camp_normal_img = pygame.image.load('img/Tutorials/tut6.png')
go_to_camp_img = pygame.transform.scale(go_to_camp_normal_img, (230, 90))
back_img = pygame.image.load('img/Icons/back.png').convert_alpha()
quit_img = pygame.image.load('img/Icons/quit.png').convert_alpha()
options_img = pygame.image.load('img/Icons/options.png').convert_alpha()
restart_img = pygame.image.load('img/Icons/restart.png').convert_alpha()



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
        eff_atk = getattr(current_fighter, "get_strength", lambda: current_fighter.strength)()
        atk_line = f"ATK: {eff_atk}"

        if getattr(current_fighter, "buff_rounds", 0) > 0:
            atk_line += f" (+{current_fighter.buff_bonus}) [{current_fighter.buff_rounds}]"

        # auto einai gia reposition
        atk_x = 200
        atk_y = screen_height - bottom_panel + 86
        draw_text(atk_line, small_font, yellow, atk_x, atk_y)

        # --- Stressed badge (deuterh seira) ---
        if getattr(current_fighter, "stress", 0) >= 100:
            stressed_text = "stressed -50%"
            # POSITION OF THE STRESS TEXT
            stressed_y = atk_y + small_font.get_height() + 2
            draw_text(stressed_text, small_font, light_blue, atk_x, stressed_y)
    else:
        draw_text('Enemy turn', font, red, 20, screen_height - bottom_panel + 10)

    # show names and hp
    for count, i in enumerate(bandit_list):
        draw_text(f'{i.name} HP: {i.hp}', font, red,
                  440, (screen_height - bottom_panel + 10) + count * 60)




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
        self.buff_bonus = 0  # active bonus tou buff
        self.buff_rounds = 0  # an buff_rounds > 3 to buff feugei
        self.target = pygame.math.Vector2(x, y)
        self.slide_speed = 8  # reflow slide speed
        self.order = 0  # original party order
        self.reflowed = False  # flag when someone dies, einai gia to reflow
        self.show_on_death = False  # gia ta death animations
        self.death_hold_ms = 300
        self._death_done_time = None

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

        # LOAD ANIMATIONS
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
        # MISSING FRAMES gia debug:
        for anim_name in self.action_dict:
            num_frames = animation_types.get(anim_name, 0)
            if num_frames == 0:
                print(f"WARNING: No frames found for {self.name} animation: {anim_name}")

    def update(self):
        animation_cooldown = 100

        # --- STRESS KILL ---
        if self.alive and self.max_stress > 0 and self.stress >= self.max_stress:
            self.stress = self.max_stress
            self.alive = False
            self.death()

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

                # After Attack or Hurt, go back to Agro
                elif self.action in [self.action_dict['Attack'], self.action_dict['Hurt']]:
                    if 'Agro' in self.action_dict:
                        self.action = self.action_dict['Agro']
                        self.frame_index = 0
                    else:
                        self.action = self.action_dict['Idle']
                        self.frame_index = 0

                else:
                    self.frame_index = 0

        # Reset frame index if somehow out of range
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
        damage = self.get_strength() + rand  # random gia to attack me bash to strength tou enemy
        target.hp -= damage

        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            target.death()
        else:
            target.hurt()

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
        self.show_on_death = True
        self._death_done_time = None


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

    def get_strength(self):
        base = self.base_strength + getattr(self, "buff_bonus", 0)
        if getattr(self, "stress", 0) >= 100:
            base = max(1, int(base * 0.5))
        return base


class Enemy(Fighter):
    def __init__(self, x, y, name, max_hp, strength, potions, scale):
        # ANIMATION FRAMES FOR THE ENEMY
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
            # --- STRESS auto mpainei mono stous heroes,ta enemies den exoune stress ---
            if getattr(target, "max_stress", 0) > 0:
                target.stress += damage
                if target.stress >= target.max_stress:
                    target.stress = target.max_stress
                    if target.alive:
                        target.alive = False
                        target.death()
                else:
                    damage_text = DamageText(target.rect.centerx, target.rect.y + 20, str(damage), light_blue)
                    damage_text_group.add(damage_text)
            # an enas den exei stress, dhladh enemy, pame pali sto hp damage
            else:
                target.hp -= damage
                if target.hp <= 0:
                    target.hp = 0
                    target.alive = False
                    target.death()
                else:
                    target.hurt()
                damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
                damage_text_group.add(damage_text)
        else:
            # --- HP DAMAGE ---
            target.hp -= damage
            if target.hp <= 0:
                target.hp = 0
                target.alive = False
                target.death()
                if not hasattr(target, "show_on_death"): target.show_on_death = True
                target._death_done_time = None
                if not hasattr(target, "death_hold_ms"): target.death_hold_ms = 300
            else:
                target.hurt()
            damage_text = DamageText(target.rect.centerx, target.rect.y, str(damage), red)
            damage_text_group.add(damage_text)

    def attack(self, target):
        rand = random.randint(-5, 5)
        damage = self.get_strength() + rand
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

    def draw(self, hp, max_hp=None):
        self.hp = hp
        if max_hp is not None:
            self.max_hp = max_hp
        ratio = 0 if self.max_hp <= 0 else self.hp / self.max_hp
        pygame.draw.rect(screen, red, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, green, (self.x, self.y, int(150 * min(max(ratio, 0), 1)), 20))

class StressBar():
    def __init__(self, x, y, st, max_st):
        self.x = x
        self.y = y
        self.st = st
        self.max_st = max_st

    def draw(self, st, max_st=None):
        self.st = st
        if max_st is not None:
            self.max_st = max_st
        ratio = 0 if self.max_st <= 0 else self.st / self.max_st
        pygame.draw.rect(screen, white, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, light_blue, (self.x, self.y, int(150 * min(max(ratio, 0), 1)), 20))


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

turn_order = []
turn_index = 0

def roll_turn_order(all_fighters):
    order = []
    for fighter in all_fighters:
        if fighter.alive:
            roll = random.randint(1, 20)  # to zari
            order.append((roll, fighter))
    order.sort(key=lambda x: x[0], reverse=True)
    print("\n--- New Round ---")
    for roll, fighter in order:
        print(f"{fighter.name} rolled {roll}")
    return [f for _, f in order]


def draw_turn_order(bandit_list):
    x_offset = 30
    y_offset = 10
    box_width = 140
    box_height = 40
    padding = 10

    for i, fighter in enumerate(turn_order):
        if not fighter.alive:
            continue  # skip dead fighters

        # Highlight for current turn (yellow)
        bg_color = yellow if i == turn_index else (dark_red if fighter in bandit_list else dark_green)

        # Box + border
        pygame.draw.rect(screen, bg_color, (x_offset, y_offset, box_width, box_height))
        pygame.draw.rect(screen, black, (x_offset, y_offset, box_width, box_height), 2)

        # Portrait or name alla otan den yparxei to portrai den deixnei kati
        if hasattr(fighter, "portrait") and fighter.portrait:
            portrait = pygame.transform.scale(fighter.portrait, (box_width - 4, box_height // 2))
            screen.blit(portrait, (x_offset + 2, y_offset + 2))
        else:
            draw_text(fighter.name[:11], font, white, x_offset + 5, y_offset + 5)

        x_offset += box_width + padding


def party_offscreen_right(heroes, threshold_x=900):
    """Return True when every *alive* hero has moved past threshold_x."""
    alive = [h for h in heroes if getattr(h, "alive", True)]
    if not alive:
        return False
    return all(h.rect.centerx > threshold_x for h in alive)


def slide_entity_toward_target(ent, speed=8):
    """Slide any entity toward ent.target if present."""
    if not hasattr(ent, "target"):
        return
    current = pygame.math.Vector2(ent.rect.center)
    delta = ent.target - current
    dist = delta.length()
    if dist > 0.5:
        step = min(speed, dist)
        ent.rect.center = (current + delta.normalize() * step)


def check_and_reflow_once_per_death(hero_list):
    """
    If any hero just died (alive==False) and we haven't reflowed since that death,
    trigger a reflow exactly once per death.
    """
    need_reflow = False
    for h in hero_list:
        if not h.alive and not getattr(h, "reflowed", False):
            h.reflowed = True
            need_reflow = True
    if need_reflow:
        reflow_alive_into_front(hero_list)


def draw_turn_indicator(entity):
    """Draw a yellow triangle above the entity's head to show it's their turn."""
    if not getattr(entity, "alive", True):
        return
    head_x, head_y = entity.rect.midtop
    offset = 7  # poso panw apo to kefali tous tha einai to trigono pou deixnei thn seira
    tri = [
        (head_x,     head_y - offset),        # down
        (head_x - 12, head_y - offset - 18),  # left
        (head_x + 12, head_y - offset - 18),  # right
    ]
    pygame.draw.polygon(screen, yellow, tri)
    pygame.draw.polygon(screen, black, tri, 2)  # ena mikro outline


def _fallback_reflow_alive_into_front(hero_list):
    alive = [h for h in hero_list if h.alive]
    for i, h in enumerate(alive):
        h.target = pygame.math.Vector2(PARTY_SLOTS[i])



# ----------------------------------------- GAME LOOP ------------------------------------------

def engineering_boss(hero_list,brightness_level):
    action_cooldown = 0
    potion_effect = 15
    clicked = False
    moving_right = False
    moving_left = False
    game_over = 0
    camp_yes = True   # sto teleutaio boss, den theloume na emfanizetai to "go to camp" opote auto tha ginei false


    # THIS IS FOR STRESS TESTING, MANUALLY PUTS STRESS INTO CHARACTERS
    #for h in hero_list:
        #if h.name == "Warrior":
            #h.stress = 120


    for h in hero_list:
        h.strength = h.base_strength + getattr(h, "buff_bonus", 0)
        if h.hp <= 0:
            h.hp = 0
            h.alive = False
            h.death()
        for h in hero_list:
            if not hasattr(h, "show_on_death"): h.show_on_death = False
            if not hasattr(h, "death_hold_ms"): h.death_hold_ms = 300
            if not hasattr(h, "_death_done_time"): h._death_done_time = None


    # Restore last known layout
    restore_party_layout(hero_list)
    reflow_alive_into_front(hero_list)
    if not all(hasattr(h, "target") for h in hero_list if h.alive):
        _fallback_reflow_alive_into_front(hero_list)

    # Snap every hero to whatever target reflow decided
    for h in hero_list:
        if hasattr(h, "target"):
            h.rect.center = (int(h.target.x), int(h.target.y))
        # agro pose mono only on alive heroes
        if h.alive:
            if 'Agro' in h.action_dict:
                h.agro()
            else:
                h.idle()


    # ENEMY/ ENEMIES
    Engineering = Enemy(600, 200, 'Brassan, the Engineer', 500, 50, 0, 0.25)
    Engineering.hp_bar_offset = (10, 310)

    bandit_list = [Engineering]

    hero = hero_list[0]

    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero.hp, hero.max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero.stress, hero.max_stress)
    engineering_health_bar = HealthBar(550, screen_height - bottom_panel + 40, Engineering.hp, Engineering.max_hp)

    # BUTTONS
    potion_button = button.Button(screen, 120, screen_height - bottom_panel + 80, potion_img, 50, 50)
    options_button = button.Button(screen, 650, 365, options_img, 120, 30)
    restart_button = button.Button(screen, 300, 240, restart_img, 200, 60)

    global turn_order, turn_index,  current_fighter

    all_fighters = hero_list + bandit_list
    total_fighters = len(all_fighters)

    turn_order = roll_turn_order(all_fighters)
    turn_index = 0
    run = True

    while run:
        clock.tick(fps)
        # draw background
        draw_bg()
        current_actor = turn_order[turn_index]
        # draw panel
        draw_panel(current_actor,hero_list,bandit_list)
        if current_actor in hero_list:
            hero_health_bar.draw(current_actor.hp, current_actor.max_hp)
            hero_stress_bar.draw(current_actor.stress, current_actor.max_stress)

        engineering_health_bar.draw(Engineering.hp)
        # draw fighters and their mini HP bars
        for fighter in hero_list:
            fighter.update()
            if getattr(fighter, "alive", True) is False and getattr(fighter, "show_on_death", False):
                try:
                    death_idx = fighter.action_dict.get('Death')
                    if fighter.action == death_idx:
                        last_frame = len(fighter.animation_list[death_idx]) - 1
                        if fighter.frame_index >= last_frame:
                            if getattr(fighter, "_death_done_time", None) is None:
                                fighter._death_done_time = pygame.time.get_ticks()
                            elif pygame.time.get_ticks() - fighter._death_done_time >= getattr(fighter, "death_hold_ms",
                                                                                               300):
                                fighter.show_on_death = False
                except Exception:
                    pass

            alive = getattr(fighter, "alive", True)
            show_corpse = getattr(fighter, "show_on_death", False)
            if (not alive) and (not show_corpse):
                continue  # skip only if dead AND not showing corpse

            if game_over == 0 and not moving_right and getattr(fighter, "alive", True):   # an to battle exei teleiwsei den theloume oi xarakthres na kanoun shift
                slide_entity_toward_target(fighter, speed=8)                              # an pethanei enas, oi prohgoumenoi klironomoun thn thesi tou, san allisida
            fighter.draw()
            if not getattr(fighter, "alive", True):
                continue  # SKIP THE DEAD, OI NEKROI DEN EXOUN MINI HP BARS

            bar_width = 50
            bar_height = 6

            offset_x, offset_y = getattr(fighter, "hp_bar_offset", (0, -10))

            bar_x = fighter.rect.centerx - bar_width // 2 + offset_x
            bar_y = fighter.rect.top + offset_y

            # red background gia to mini hp bar
            pygame.draw.rect(screen, red, (bar_x, bar_y, bar_width, bar_height))
            # green foreground for the HP
            hp_ratio = fighter.hp / fighter.max_hp
            stress_ratio = fighter.stress / fighter.max_stress
            pygame.draw.rect(screen, green, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
            pygame.draw.rect(screen, white, (bar_x, bar_y + bar_height + 2, bar_width, bar_height))
            pygame.draw.rect(screen, light_blue, (bar_x, bar_y + bar_height + 2, int(bar_width * stress_ratio), bar_height))

        for bandit in bandit_list:  # Loop through all bandits
            bandit.update()
            bandit.draw()

        # draw the damage text
        damage_text_group.update()
        damage_text_group.draw(screen)

        # control player actions
        # reset action variables
        attack = False
        potion = False
        target = None
        # make sure mouse is visible giati kapoies fores kanei kati perierga
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()
        for count, bandit in enumerate(bandit_list):
            if bandit.rect.collidepoint(pos):
                # hide mouse
                pygame.mouse.set_visible(False)
                # show sword in place of mouse cursor
                screen.blit(sword_img, pos)
                if clicked == True and bandit.alive == True:
                    attack = True
                    target = bandit_list[count]

        if options_button.draw():
            initial_slider_value = brightness_level * 100
            options_menu = Options(screen, screen_width, screen_height, font, back_img, quit_img,current_brightness=initial_slider_value)
            brightness_level = options_menu.run(draw_bg, draw_text, brightness_level)

        if current_actor in hero_list:
            if potion_button.draw():
                potion = True
            # show number of potions remaining
            draw_text(str(current_actor.potions), font, red, 175, screen_height - bottom_panel + 100)

            # if all fighters have had a turn then reset
            if current_fighter > total_fighters:
                current_fighter = 1


        if game_over == 0:
            draw_turn_order(bandit_list)
            # TRIGONO GIA THN SEIRA PAIKSIMATOS
            draw_turn_indicator(current_actor)
            current_actor = turn_order[turn_index]

            if current_actor.alive:
                action_cooldown += 1
                if action_cooldown >= current_actor.action_wait_time:

                    if current_actor in hero_list:
                        # Player's turn
                        if attack and target is not None:
                            current_actor.attack(target)
                            check_and_reflow_once_per_death(hero_list)
                            turn_index += 1
                            action_cooldown = 0
                            attack = False  # reset after use
                            clicked = False
                        elif potion:
                            if current_actor.potions > 0:
                                heal_amount = 50
                                current_actor.hp += heal_amount
                                current_actor.potions -= 1
                                damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y,
                                                         str(heal_amount),
                                                         green)
                                damage_text_group.add(damage_text)
                            turn_index += 1
                            action_cooldown = 0
                            potion = False  # reset after use

                    else:
                        # Enemy's turn
                        if (current_actor.hp / current_actor.max_hp) < 0.5 and current_actor.potions > 0:
                            heal_amount = min(potion_effect, current_actor.max_hp - current_actor.hp)
                            current_actor.hp += heal_amount
                            current_actor.potions -= 1
                            damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y, str(heal_amount),
                                                     green)
                            damage_text_group.add(damage_text)
                        else:
                            living_heroes = [h for h in hero_list if h.alive]
                            if living_heroes:
                                target_hero = random.choice(living_heroes)
                                current_actor.attack(target_hero)
                                check_and_reflow_once_per_death(hero_list)
                        turn_index += 1
                        action_cooldown = 0
            else:
                turn_index += 1  # skip dead fighter

            # --- End of round check ---
            if turn_index >= len(turn_order):
                # check the buff meta apo kathe gyro
                for hero in hero_list:
                    if getattr(hero, "buff_rounds", 0) > 0:
                        hero.buff_rounds -= 1
                        if hero.buff_rounds == 0:
                            hero.buff_bonus = 0
                            hero.strength = hero.base_strength
                        else:
                            # keep strength correct while buff still active
                            hero.strength = hero.base_strength + hero.buff_bonus

                # Start a new round
                turn_order = roll_turn_order(all_fighters)
                turn_index = 0

        # check if all bandits are dead
        alive_bandits = 0
        for bandit in bandit_list:
            if bandit.alive == True:
                alive_bandits += 1
        if alive_bandits == 0:
            game_over = 1
            # Freeze targets at current positions so reflow doesn’t yank them back
            for h in hero_list:
                freeze_targets_at_current(hero_list)

        # Check if all heroes are dead
        alive_heroes = 0
        for hero in hero_list:
            if hero.alive == True:
                alive_heroes += 1
        if alive_heroes == 0:
            game_over = -1

        # check if game is over
        if game_over != 0:
            if game_over == 1:
                screen.blit(victory_img, (250, 50))
                if camp_yes:
                    screen.blit(go_to_camp_img, (550, 80))

                for hero in hero_list:
                    if hero.alive:
                        if moving_right:
                            hero.run()
                            hero.rect.x += 6
                        elif moving_left:
                            hero.run()
                            hero.rect.x -= 3
                        else:
                            hero.idle()

            if game_over == -1:
                screen.blit(defeat_img, (290, 50))
                if restart_button.draw():
                    # restart an pethanan
                    return ("RESTART", brightness_level)


        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_d:  # koumpi D
                    moving_right = True
                if event.key == pygame.K_a:  # koumpi A gia pisw
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

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            else:
                clicked = False

        if party_offscreen_right(hero_list, 900):
            # an oi 4 perpatisoun ektos othonhs, ginetai save to layout tous
            for i, h in enumerate(hero_list):
                slot_x, slot_y = PARTY_SLOTS[i]
                h.target = pygame.math.Vector2(slot_x, slot_y)
                h.rect.center = (slot_x, slot_y)
            save_party_layout(hero_list)
            run = False

        Options.apply_brightness_overlay(screen, brightness_level)

        pygame.display.update()



    return brightness_level


# ---------------------------------------------------------------------------------------
# apo edw kai pera, ta alla dyo bosses einai copy paste tou arxikou me thn monh diafora na einai to hp kai ta assets
# sthn main kalountai autes oi synarthseis me thn seira
# ---------------------------------------------------------------------------------------


def mathematics_boss(hero_list,brightness_level):
    game_state.stage = 1
    action_cooldown = 0
    potion_effect = 15
    clicked = False
    moving_right = False
    moving_left = False
    game_over = 0
    camp_yes = True   # sto teleutaio boss, den theloume na emfanizetai to "go to camp" opote auto tha ginei false


    # THIS IS FOR STRESS TESTING, MANUALLY PUTS STRESS INTO CHARACTERS
    #for h in hero_list:
        #if h.name == "Warrior":
            #h.stress = 120

    for h in hero_list:
        h.strength = h.base_strength + getattr(h, "buff_bonus", 0)
        if h.hp <= 0:
            h.hp = 0
            h.alive = False
            h.death()
        for h in hero_list:
            if not hasattr(h, "show_on_death"): h.show_on_death = False
            if not hasattr(h, "death_hold_ms"): h.death_hold_ms = 300
            if not hasattr(h, "_death_done_time"): h._death_done_time = None


    restore_party_layout(hero_list)
    reflow_alive_into_front(hero_list)
    if not all(hasattr(h, "target") for h in hero_list if h.alive):
        _fallback_reflow_alive_into_front(hero_list)

    for h in hero_list:
        if hasattr(h, "target"):
            h.rect.center = (int(h.target.x), int(h.target.y))
        # Only put battle pose on living heroes
        if h.alive:
            if 'Agro' in h.action_dict:
                h.agro()
            else:
                h.idle()


    #ENEMY/ ENEMIES
    Engineering = Enemy(600, 240, 'Calxen, the Geometer', 400, 50, 0, 0.25)
    Engineering.hp_bar_offset = (10, 310)

    bandit_list = [Engineering]

    hero = hero_list[0]

    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero.hp, hero.max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero.stress, hero.max_stress)
    engineering_health_bar = HealthBar(550, screen_height - bottom_panel + 40, Engineering.hp, Engineering.max_hp)

    # BUTTONS
    potion_button = button.Button(screen, 120, screen_height - bottom_panel + 80, potion_img, 50, 50)
    options_button = button.Button(screen, 650, 365, options_img, 120, 30)
    restart_button = button.Button(screen, 300, 240, restart_img, 200, 60)

    global turn_order, turn_index,  current_fighter

    all_fighters = hero_list + bandit_list
    total_fighters = len(all_fighters)

    turn_order = roll_turn_order(all_fighters)
    turn_index = 0
    run = True

    while run:
        clock.tick(fps)
        # draw background
        draw_bg()
        current_actor = turn_order[turn_index]
        # draw panel
        draw_panel(current_actor,hero_list,bandit_list)
        if current_actor in hero_list:
            hero_health_bar.draw(current_actor.hp, current_actor.max_hp)
            hero_stress_bar.draw(current_actor.stress, current_actor.max_stress)

        engineering_health_bar.draw(Engineering.hp)
        # draw fighters and their mini HP bars
        for fighter in hero_list:
            fighter.update()
            if getattr(fighter, "alive", True) is False and getattr(fighter, "show_on_death", False):
                try:
                    death_idx = fighter.action_dict.get('Death')
                    if fighter.action == death_idx:
                        last_frame = len(fighter.animation_list[death_idx]) - 1
                        if fighter.frame_index >= last_frame:
                            if getattr(fighter, "_death_done_time", None) is None:
                                fighter._death_done_time = pygame.time.get_ticks()
                            elif pygame.time.get_ticks() - fighter._death_done_time >= getattr(fighter, "death_hold_ms",
                                                                                               300):
                                fighter.show_on_death = False
                except Exception:
                    pass

            alive = getattr(fighter, "alive", True)
            show_corpse = getattr(fighter, "show_on_death", False)
            if (not alive) and (not show_corpse):
                continue  # skip only if dead AND not showing corpse

            if game_over == 0 and not moving_right and getattr(fighter, "alive", True):   # an to battle exei teleiwsei den theloume oi xarakthres na kanoun shift
                slide_entity_toward_target(fighter, speed=8)                              # an pethanei enas, oi prohgoumenoi klironomoun thn thesi tou, san allisida
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

        for bandit in bandit_list:  # Loop through all bandits
            bandit.update()
            bandit.draw()

        # draw the damage text
        damage_text_group.update()
        damage_text_group.draw(screen)

        # control player actions
        # reset action variables
        attack = False
        potion = False
        target = None
        # make sure mouse is visible
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()
        for count, bandit in enumerate(bandit_list):
            if bandit.rect.collidepoint(pos):
                # hide mouse
                pygame.mouse.set_visible(False)
                # show sword in place of mouse cursor
                screen.blit(sword_img, pos)
                if clicked == True and bandit.alive == True:
                    attack = True
                    target = bandit_list[count]

        if options_button.draw():
            initial_slider_value = brightness_level * 100
            options_menu = Options(screen, screen_width, screen_height, font, back_img, quit_img,current_brightness=initial_slider_value)
            brightness_level = options_menu.run(draw_bg, draw_text, brightness_level)

        if current_actor in hero_list:
            if potion_button.draw():
                potion = True
            # show number of potions remaining
            draw_text(str(current_actor.potions), font, red, 175, screen_height - bottom_panel + 100)

            # if all fighters have had a turn then reset
            if current_fighter > total_fighters:
                current_fighter = 1


        if game_over == 0:
            draw_turn_order(bandit_list)
            # TRIGONO GIA THN SEIRA PAIKSIMATOS
            draw_turn_indicator(current_actor)
            current_actor = turn_order[turn_index]

            if current_actor.alive:
                action_cooldown += 1
                if action_cooldown >= current_actor.action_wait_time:

                    if current_actor in hero_list:
                        # Player's turn
                        if attack and target is not None:
                            current_actor.attack(target)
                            check_and_reflow_once_per_death(hero_list)
                            turn_index += 1
                            action_cooldown = 0
                            attack = False  # reset after use
                            clicked = False
                        elif potion:
                            if current_actor.potions > 0:
                                heal_amount = 50
                                current_actor.hp += heal_amount
                                current_actor.potions -= 1
                                damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y,
                                                         str(heal_amount),
                                                         green)
                                damage_text_group.add(damage_text)
                            turn_index += 1
                            action_cooldown = 0
                            potion = False  # reset after use

                    else:
                        # Enemy's turn
                        if (current_actor.hp / current_actor.max_hp) < 0.5 and current_actor.potions > 0:
                            heal_amount = min(potion_effect, current_actor.max_hp - current_actor.hp)
                            current_actor.hp += heal_amount
                            current_actor.potions -= 1
                            damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y, str(heal_amount),
                                                     green)
                            damage_text_group.add(damage_text)
                        else:
                            living_heroes = [h for h in hero_list if h.alive]
                            if living_heroes:
                                target_hero = random.choice(living_heroes)
                                current_actor.attack(target_hero)
                                check_and_reflow_once_per_death(hero_list)
                        turn_index += 1
                        action_cooldown = 0
            else:
                turn_index += 1  # skip dead fighter

            # --- End of round check ---
            if turn_index >= len(turn_order):
                # chest buffs, check for the rounds
                for hero in hero_list:
                    if getattr(hero, "buff_rounds", 0) > 0:
                        hero.buff_rounds -= 1
                        if hero.buff_rounds == 0:
                            hero.buff_bonus = 0
                            hero.strength = hero.base_strength
                        else:
                            # keep strength correct while buff still active
                            hero.strength = hero.base_strength + hero.buff_bonus

                # Start a new round
                turn_order = roll_turn_order(all_fighters)
                turn_index = 0

        # check if all bandits are dead
        alive_bandits = 0
        for bandit in bandit_list:
            if bandit.alive == True:
                alive_bandits += 1
        if alive_bandits == 0:
            game_over = 1
            # Freeze targets at current positions so reflow doesn’t yank them back
            for h in hero_list:
                freeze_targets_at_current(hero_list)

        # Check if all heroes are dead
        alive_heroes = 0
        for hero in hero_list:
            if hero.alive == True:
                alive_heroes += 1
        if alive_heroes == 0:
            game_over = -1

        # check if game is over
        if game_over != 0:
            if game_over == 1:
                screen.blit(victory_img, (250, 50))
                if camp_yes:
                    screen.blit(go_to_camp_img, (550, 80))

                for hero in hero_list:
                    if hero.alive:
                        if moving_right:
                            hero.run()
                            hero.rect.x += 6
                        elif moving_left:
                            hero.run()
                            hero.rect.x -= 3
                        else:
                            hero.idle()

            if game_over == -1:
                screen.blit(defeat_img, (290, 50))
                if restart_button.draw():
                    # restart ama pethanoun
                    return ("RESTART", brightness_level)


        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_d:  # koumpi D
                    moving_right = True
                if event.key == pygame.K_a:  # koumpi A gia pisw
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

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            else:
                clicked = False

        if party_offscreen_right(hero_list, 900):
            for i, h in enumerate(hero_list):
                slot_x, slot_y = PARTY_SLOTS[i]
                h.target = pygame.math.Vector2(slot_x, slot_y)
                h.rect.center = (slot_x, slot_y)
            save_party_layout(hero_list)
            run = False

        Options.apply_brightness_overlay(screen, brightness_level)

        pygame.display.update()



    return brightness_level

def biology_boss(hero_list,brightness_level):
    game_state.stage = 3
    action_cooldown = 0
    potion_effect = 15
    clicked = False
    moving_right = False
    moving_left = False
    game_over = 0
    camp_yes = False   # sto teleutaio boss, den theloume na emfanizetai to "go to camp" opote auto tha ginei false


    # THIS IS FOR STRESS TESTING, MANUALLY PUTS STRESS INTO CHARACTERS
    #for h in hero_list:
        #if h.name == "Warrior":
            #h.stress = 120

    for h in hero_list:
        h.strength = h.base_strength + getattr(h, "buff_bonus", 0)
        if h.hp <= 0:
            h.hp = 0
            h.alive = False
            h.death()
        for h in hero_list:
            if not hasattr(h, "show_on_death"): h.show_on_death = False
            if not hasattr(h, "death_hold_ms"): h.death_hold_ms = 300
            if not hasattr(h, "_death_done_time"): h._death_done_time = None


    restore_party_layout(hero_list)
    reflow_alive_into_front(hero_list)
    if not all(hasattr(h, "target") for h in hero_list if h.alive):
        _fallback_reflow_alive_into_front(hero_list)

    # Snap every hero to whatever target reflow decided
    for h in hero_list:
        if hasattr(h, "target"):
            h.rect.center = (int(h.target.x), int(h.target.y))
        # agro stous zwntanous
        if h.alive:
            if 'Agro' in h.action_dict:
                h.agro()
            else:
                h.idle()


    # ENEMY/ENEMIES
    Engineering = Enemy(600, 220, 'Helixor, the Blasphemer', 200, 50, 0, 0.27)
    Engineering.hp_bar_offset = (10, 310)

    bandit_list = [Engineering]

    hero = hero_list[0]

    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero.hp, hero.max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero.stress, hero.max_stress)
    engineering_health_bar = HealthBar(550, screen_height - bottom_panel + 40, Engineering.hp, Engineering.max_hp)

    # BUTTONS
    potion_button = button.Button(screen, 120, screen_height - bottom_panel + 80, potion_img, 50, 50)
    options_button = button.Button(screen, 650, 365, options_img, 120, 30)
    restart_button = button.Button(screen, 300, 240, restart_img, 200, 60)

    global turn_order, turn_index,  current_fighter

    all_fighters = hero_list + bandit_list
    total_fighters = len(all_fighters)

    turn_order = roll_turn_order(all_fighters)
    turn_index = 0
    run = True

    while run:
        clock.tick(fps)
        # draw background
        draw_bg()
        current_actor = turn_order[turn_index]
        # draw panel
        draw_panel(current_actor,hero_list,bandit_list)
        if current_actor in hero_list:
            hero_health_bar.draw(current_actor.hp, current_actor.max_hp)
            hero_stress_bar.draw(current_actor.stress, current_actor.max_stress)

        engineering_health_bar.draw(Engineering.hp)
        # draw fighters and their mini HP bars
        for fighter in hero_list:
            fighter.update()
            if getattr(fighter, "alive", True) is False and getattr(fighter, "show_on_death", False):
                try:
                    death_idx = fighter.action_dict.get('Death')
                    if fighter.action == death_idx:
                        last_frame = len(fighter.animation_list[death_idx]) - 1
                        if fighter.frame_index >= last_frame:
                            if getattr(fighter, "_death_done_time", None) is None:
                                fighter._death_done_time = pygame.time.get_ticks()
                            elif pygame.time.get_ticks() - fighter._death_done_time >= getattr(fighter, "death_hold_ms",
                                                                                               300):
                                fighter.show_on_death = False
                except Exception:
                    pass

            alive = getattr(fighter, "alive", True)
            show_corpse = getattr(fighter, "show_on_death", False)
            if (not alive) and (not show_corpse):
                continue  # skip only if dead AND not showing corpse

            if game_over == 0 and not moving_right and getattr(fighter, "alive", True):   # an to battle exei teleiwsei den theloume oi xarakthres na kanoun shift
                slide_entity_toward_target(fighter, speed=8)                              # an pethanei enas, oi prohgoumenoi klironomoun thn thesi tou, san allisida
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

        for bandit in bandit_list:  # Loop through all bandits
            bandit.update()
            bandit.draw()

        # draw the damage text
        damage_text_group.update()
        damage_text_group.draw(screen)

        # control player actions
        # reset action variables
        attack = False
        potion = False
        target = None
        # make sure mouse is visible
        pygame.mouse.set_visible(True)
        pos = pygame.mouse.get_pos()
        for count, bandit in enumerate(bandit_list):
            if bandit.rect.collidepoint(pos):
                # hide mouse
                pygame.mouse.set_visible(False)
                # show sword in place of mouse cursor
                screen.blit(sword_img, pos)
                if clicked == True and bandit.alive == True:
                    attack = True
                    target = bandit_list[count]

        if options_button.draw():
            initial_slider_value = brightness_level * 100
            options_menu = Options(screen, screen_width, screen_height, font, back_img, quit_img,current_brightness=initial_slider_value)
            brightness_level = options_menu.run(draw_bg, draw_text, brightness_level)

        if current_actor in hero_list:
            if potion_button.draw():
                potion = True
            # show number of potions remaining
            draw_text(str(current_actor.potions), font, red, 175, screen_height - bottom_panel + 100)

            # if all fighters have had a turn then reset
            if current_fighter > total_fighters:
                current_fighter = 1


        if game_over == 0:
            draw_turn_order(bandit_list)
            # TRIGONO GIA THN SEIRA PAIKSIMATOS
            draw_turn_indicator(current_actor)
            current_actor = turn_order[turn_index]

            if current_actor.alive:
                action_cooldown += 1
                if action_cooldown >= current_actor.action_wait_time:

                    if current_actor in hero_list:
                        # Player's turn
                        if attack and target is not None:
                            current_actor.attack(target)
                            check_and_reflow_once_per_death(hero_list)
                            turn_index += 1
                            action_cooldown = 0
                            attack = False  # reset after use
                            clicked = False
                        elif potion:
                            if current_actor.potions > 0:
                                heal_amount = 50
                                current_actor.hp += heal_amount
                                current_actor.potions -= 1
                                damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y,
                                                         str(heal_amount),
                                                         green)
                                damage_text_group.add(damage_text)
                            turn_index += 1
                            action_cooldown = 0
                            potion = False  # reset after use

                    else:
                        # Enemy's turn
                        if (current_actor.hp / current_actor.max_hp) < 0.5 and current_actor.potions > 0:
                            heal_amount = min(potion_effect, current_actor.max_hp - current_actor.hp)
                            current_actor.hp += heal_amount
                            current_actor.potions -= 1
                            damage_text = DamageText(current_actor.rect.centerx, current_actor.rect.y, str(heal_amount),
                                                     green)
                            damage_text_group.add(damage_text)
                        else:
                            living_heroes = [h for h in hero_list if h.alive]
                            if living_heroes:
                                target_hero = random.choice(living_heroes)
                                current_actor.attack(target_hero)
                                check_and_reflow_once_per_death(hero_list)
                        turn_index += 1
                        action_cooldown = 0
            else:
                turn_index += 1  # skip dead fighter

            # --- End of round check ---
            if turn_index >= len(turn_order):
                # chest buff check
                for hero in hero_list:
                    if getattr(hero, "buff_rounds", 0) > 0:
                        hero.buff_rounds -= 1
                        if hero.buff_rounds == 0:
                            hero.buff_bonus = 0
                            hero.strength = hero.base_strength
                        else:
                            # keep strength correct while buff still active
                            hero.strength = hero.base_strength + hero.buff_bonus

                # Start a new round
                turn_order = roll_turn_order(all_fighters)
                turn_index = 0

        # check if all bandits are dead
        alive_bandits = 0
        for bandit in bandit_list:
            if bandit.alive == True:
                alive_bandits += 1
        if alive_bandits == 0:
            game_over = 1
            # Freeze targets at current positions so reflow doesn’t yank them back
            for h in hero_list:
                freeze_targets_at_current(hero_list)

        # Check if all heroes are dead
        alive_heroes = 0
        for hero in hero_list:
            if hero.alive == True:
                alive_heroes += 1
        if alive_heroes == 0:
            game_over = -1

        # check if game is over
        if game_over != 0:
            if game_over == 1:
                screen.blit(victory_img, (250, 50))
                if camp_yes:
                    screen.blit(go_to_camp_img, (550, 80))

                for hero in hero_list:
                    if hero.alive:
                        if moving_right:
                            hero.run()
                            hero.rect.x += 6
                        elif moving_left:
                            hero.run()
                            hero.rect.x -= 3
                        else:
                            hero.idle()

            if game_over == -1:
                screen.blit(defeat_img, (290, 50))
                if restart_button.draw():
                    # restart ama pethanoun
                    return ("RESTART", brightness_level)


        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_d:  # koumpi D
                    moving_right = True
                if event.key == pygame.K_a:  # koumpi A gia pisw
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

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True
            else:
                clicked = False

        if party_offscreen_right(hero_list, 900):
            for i, h in enumerate(hero_list):
                slot_x, slot_y = PARTY_SLOTS[i]
                h.target = pygame.math.Vector2(slot_x, slot_y)
                h.rect.center = (slot_x, slot_y)
            save_party_layout(hero_list)
            run = False
            fade_out(screen, 400)

        Options.apply_brightness_overlay(screen, brightness_level)

        pygame.display.update()



    return brightness_level
