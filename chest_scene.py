import random
from resting import *
from options import Options

# ----------------- IMPORT PY ARXEIA ---------------
# party layout persistence
from party_layout import restore_party_layout, save_party_layout
import game_state
# --------------------------------------------------

pygame.init()

clock = pygame.time.Clock()
fps = 60

bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel

# oi xarakthres kanoun spawn ektos skhnhs
CHEST_OFFSCREEN_SLOTS = [(-50, 250), (-145, 260), (-230, 260), (-310, 260)]
TUTORIAL_SHOWN_CHEST = False  #auto einai gia to tutorial
passes = 0
font = pygame.font.SysFont('Times New Roman', 26)
small_font = pygame.font.SysFont('Times New Roman', 20)


brightness_level = 1.0

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Game')

def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)

BG = pygame.image.load("assets/Background.png")
BG = pygame.transform.scale(BG, (800, 550))
play_b = pygame.image.load("assets/Play_Rect.png")
quit_b = pygame.image.load("assets/Quit_Rect.png")

back_img = pygame.image.load('img/Icons/back.png').convert_alpha()
quit_img = pygame.image.load('img/Icons/quit.png').convert_alpha()
options_img = pygame.image.load('img/Icons/options.png').convert_alpha()
chest_open_img = pygame.image.load('img/Tutorials/tut5.png').convert_alpha()
chest_open_img = pygame.transform.scale(chest_open_img, (250, 150))


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
background_img = pygame.image.load('assets/Stages/Stage1/3.png').convert_alpha()
background_img2 = pygame.image.load('assets/Stages/Stage2/4.png').convert_alpha()
background_img3 = pygame.image.load('assets/Stages/Stage3/2.png').convert_alpha()
panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()
defeat_img = pygame.image.load('img/Icons/defeat.png').convert_alpha()
sword_img = pygame.image.load('img/Icons/sword.png').convert_alpha()



# DRAW THE TEXT
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


# DRAW PANEL
def draw_panel(current_fighter, hero_list, bandit_list):
    # draw panel rectangle
    screen.blit(panel_img, (0, screen_height - bottom_panel))

    if current_fighter in hero_list:

        face = pygame.image.load(f'img/FaceIcons/{current_fighter.name}.png').convert_alpha()
        face_scaled = pygame.transform.scale(face, (200, 100))
        screen.blit(face_scaled, (-40, 440))

        # stats
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

        atk_x = 200
        atk_y = screen_height - bottom_panel + 86
        draw_text(atk_line, small_font, yellow, atk_x, atk_y)

        # --- Stressed badge (deuterh seira) ---
        if getattr(current_fighter, "stress", 0) >= 100:
            stressed_y = atk_y + small_font.get_height() + 2
            draw_text("stressed -50%", small_font, light_blue, atk_x, stressed_y)

    else:
        draw_text('Enemy turn', font, red, 20, screen_height - bottom_panel + 10)

    for count, i in enumerate(bandit_list):
        draw_text(f'{i.name} HP: {i.hp}', font, red,
                  550, (screen_height - bottom_panel + 10) + count * 60)



class Fighter():
    def __init__(self, x, y, name, max_hp, strength, potions,stress,max_stress, scale=2):
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
        self.base_strength = strength
        self.strength = strength
        self.buff_bonus = 0  # active buff tou bonus
        self.buff_rounds = 0

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
        # debug for missing frames
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

                elif self.action in [self.action_dict['Attack'], self.action_dict['Hurt']]:
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
    def __init__(self, x, y, name, max_hp, strength, potions, scale=3):
        # specific animation frames gia ton enemy
        animation_types = {
            'Idle': 8,
            'Attack': 8,
            'Hurt': 3,
            'Death': 10
        }
        if name == 'Knight':
            animation_types['Run'] = 9

        super().__init__(x, y, name, max_hp, strength, potions, 0, 0, scale)

        # enemy specific attributes
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
        # attack alla mono gia ton enemy
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


def apply_chest_buff(hero_list, bonus=20, rounds=3):
    for hero in hero_list:
        hero.buff_bonus = bonus
        hero.buff_rounds = rounds
        hero.strength = hero.base_strength + hero.buff_bonus


def party_offscreen_right(heroes, threshold_x=900):
    """Return True when every *alive* hero has moved past threshold_x."""
    alive = [h for h in heroes if getattr(h, "alive", True)]
    if not alive:
        return False
    return all(h.rect.centerx > threshold_x for h in alive)


# --------------------------------- GAME LOOP -------------------------------------


# BUTTONS
potion_button = button.Button(screen, 120, screen_height - bottom_panel + 80, potion_img, 50, 50)
options_button = button.Button(screen, 650, 365, options_img, 120, 30)


def chest(hero_list,brightness_level):
    global passes
    chest = Enemy(600, 310, 'Wooden Chest', 1, 0, 0, scale=2.5)
    chest.hp_bar_offset = (10, 310)
    passes = passes + 1
    chest.buff_given = False
    show_chest_open = False       # GIA TO TUTORIAL TOU CHEST
    tutorial_frames_remaining = 0

    chest_health_bar = HealthBar(550, screen_height - bottom_panel + 40, chest.hp, chest.max_hp)

    bandit_list = [chest]

    # Restore the last known party order/targets
    restore_party_layout(hero_list, fallback_slots=CHEST_OFFSCREEN_SLOTS)

    # !!! spawn heroes at chest scene’s offscreen-left positions while preserving the saved order.
    alive_in_order = sorted(
        [h for h in hero_list if getattr(h, "alive", True)],
        key=lambda h: getattr(h, "order", 0)
    )
    for i, h in enumerate(alive_in_order):
        slot = CHEST_OFFSCREEN_SLOTS[min(i, len(CHEST_OFFSCREEN_SLOTS) - 1)]
        h.rect.center = slot
        h.target = pygame.math.Vector2(slot)
        h.action = 0  # idle/standing animation on enter


    # define game variables
    moving_right = False
    moving_left = False
    action_cooldown = 0
    action_wait_time = 1
    potion_effect = 15
    game_over = 0
    clicked = False

    hero = hero_list[0]
    hero_health_bar = HealthBar(120, screen_height - bottom_panel + 25, hero.hp, hero.max_hp)
    hero_stress_bar = StressBar(120, screen_height - bottom_panel + 55, hero.stress, hero.max_stress)

    all_fighters = hero_list
    total_fighters = len(all_fighters)

    turn_order = roll_turn_order(all_fighters)
    turn_index = 0
    run = True

    while run:
        clock.tick(fps)
        # draw background
        draw_bg()

        if show_chest_open:
            open_rect = chest_open_img.get_rect(center=(500, 180))
            screen.blit(chest_open_img, open_rect)

        # TUTORIAL
        if tutorial_frames_remaining > 0:
            tut_rect = chest_open_img.get_rect(center=(500, 180))
            screen.blit(chest_open_img, tut_rect)
            tutorial_frames_remaining -= 1
            # to tutorial den tha ksana emfanistei
            if tutorial_frames_remaining == 0:
                global TUTORIAL_SHOWN_CHEST
                TUTORIAL_SHOWN_CHEST = True


        current_actor = turn_order[turn_index]
        hero = random.choice(hero_list)
        # draw panel
        draw_panel(current_actor,hero_list,bandit_list)
        if current_actor in hero_list:
            hero_health_bar.draw(current_actor.hp, current_actor.max_hp)
            hero_stress_bar.draw(current_actor.stress, current_actor.max_stress)


        # draw fighters and their mini HP bars
        for fighter in hero_list:
            #if not fighter.alive:
                #continue
            if not getattr(fighter, "alive", True):
                continue  # SKIP THE DEAD, OI NEKROI DEN EXOUN MINI HP BARS
            fighter.update()
            fighter.draw()

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

        for hero in hero_list:
            if not hero.alive:
                continue
            hero.update()
            hero.draw()
            hero_health_bar.draw(hero.hp)
            hero_stress_bar.draw(hero.stress)

        for bandit in bandit_list:
            bandit.update()
            if bandit.name.lower() == "Wooden Chest" and bandit.hp == 0:
                # mia fora mono gia to tutorial
                if not TUTORIAL_SHOWN_CHEST:
                    show_chest_open = True  # deixnei to tutorial
                    TUTORIAL_SHOWN_CHEST = True  # den tha to ksana deiksei
            bandit.draw()


            if bandit.name.lower() == "Wooden Chest" and bandit.hp == 0 and not bandit.buff_given:
                apply_chest_buff(hero_list)
                bandit.buff_given = True


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

        if game_over == 0:
            current_actor = turn_order[turn_index]

            if current_actor.alive:
                action_cooldown += 1
                if action_cooldown >= action_wait_time:

                    if current_actor in hero_list:
                        # Player's turn
                        if attack and target is not None:
                            current_actor.attack(target)
                            turn_index += 1
                            action_cooldown = 0
                            attack = False  # reset after use
                        elif potion:
                            if current_actor.potions > 0:
                                heal_amount = min(potion_effect, current_actor.max_hp - current_actor.hp)
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
                        turn_index += 1
                        action_cooldown = 0
            else:
                turn_index += 1  # skip dead fighter

            # End of round check
            if turn_index >= len(turn_order):
                turn_order = roll_turn_order(all_fighters)
                turn_index = 0



        # an oi exthroi einai akoma zwntanoi
        alive_bandits = 0
        for bandit in bandit_list:
            if bandit.alive:
                alive_bandits += 1

        if alive_bandits == 0 and not chest.buff_given:
            apply_chest_buff(hero_list)
            chest.buff_given = True
            game_over = 1


        # Check if all heroes are dead
        alive_heroes = 0
        for hero in hero_list:
            if hero.alive == True:
                alive_heroes += 1
        if alive_heroes == 0:
            game_over = -1


        for hero in hero_list:
            if not hero.alive:
                continue
            hero.update()
            hero.draw()

            # allow moving during chest scene
            # to check symperiferete san exthros alla den einai. Den kanei attack kai exei 1hp
            if moving_right:
                hero.run()
                hero.rect.x += 6
            elif moving_left:
                hero.run()
                hero.rect.x -= 3
            else:
                hero.idle()



        for event in pygame.event.get():
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

            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = True

        if party_offscreen_right(hero_list, 900):
            save_party_layout(hero_list)
            run = False

        if passes == 3:
            game_state.stage = 1
        if passes == 4:
            game_state.stage = 2
        Options.apply_brightness_overlay(screen, brightness_level)


        pygame.display.update()

    return brightness_level

