import sys

import pygame
import button
from options import Options

# ----------------- IMPORT PY ARXEIA ---------------
from party_layout import reflow_alive_into_front, save_party_layout
# --------------------------------------------------

pygame.init()

clock = pygame.time.Clock()
fps = 60

# screen setup
bottom_panel = 150
screen_width = 800
screen_height = 400 + bottom_panel
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Camp')
TUTORIAL_SHOWN_MINI = False
CAMP_BAR_MAX_WIDTH = 120      # how wide the camp bars should look
CAMP_BAR_REF_HP    = 200      # full width for hp
CAMP_BAR_REF_ST    = 200      # full width for stress


# FONTS
font = pygame.font.SysFont('Times New Roman', 26)

# COLORS
red = (255, 0, 0)
green = (0, 255, 0)
yellow = (255, 255, 0)
light_blue = (173, 216, 230)   # sexy xroma epeidh mou aresei TI THA KANEIS GIA AUTO (stress)

# OLD STATIC BACKGROUND
#background_img = pygame.image.load('img/Background/Camp/camp.png').convert_alpha()
#background_img = pygame.transform.scale(background_img, (screen_width, screen_height - bottom_panel))

panel_img = pygame.image.load('img/Icons/panel.png').convert_alpha()
potion_img = pygame.image.load('img/Icons/potion.png').convert_alpha()


# HEALING BUTTON ICONS
heal_hp_1 = pygame.image.load('img/Icons/Camp/CampIcon3.png').convert_alpha()
heal_hp_1_used = pygame.image.load('img/Icons/Camp/CampIcon3_used.png').convert_alpha()
heal_hp_2 = pygame.image.load('img/Icons/Camp/CampIcon4.png').convert_alpha()
heal_hp_2_used = pygame.image.load('img/Icons/Camp/CampIcon4_used.png').convert_alpha()
heal_stress_1 = pygame.image.load('img/Icons/Camp/CampIcon1.png').convert_alpha()
heal_stress_1_used = pygame.image.load('img/Icons/Camp/CampIcon1_used.png').convert_alpha()
heal_stress_2 = pygame.image.load('img/Icons/Camp/CampIcon2.png').convert_alpha()
heal_stress_2_used = pygame.image.load('img/Icons/Camp/CampIcon2_used.png').convert_alpha()
continue_img = pygame.image.load('img/Icons/Camp/continues.png').convert_alpha()

camp_tutorial_img = pygame.image.load('img/Tutorials/tut4.png')
scaled_camp_tut_img = pygame.transform.scale(camp_tutorial_img, (550, 400))



# SCALING FOR THE BUTTON ICONS
heal_small_hp_img = pygame.transform.scale(heal_hp_1, (64, 64))
heal_large_hp_img = pygame.transform.scale(heal_hp_2, (64, 64))
heal_small_st_img = pygame.transform.scale(heal_stress_1, (64, 64))
heal_large_st_img = pygame.transform.scale(heal_stress_2, (64, 64))


dummy_img = pygame.transform.scale(potion_img, (64, 64))
flicker_surf = pygame.Surface((200, 200), pygame.SRCALPHA)


# game variables
potion_effect = 15
clicked = False
selected_fighter = None  # track which character is selected


# --- Load animated background frames for the campfire ---
bg_frames = []
bg_frame_index = 0
bg_frame_timer = 0
bg_frame_speed = 7

for i in range(17):  # 0 to 16
    img = pygame.image.load(f'img/Background/Camp/Fire/{i}.png').convert_alpha()
    img = pygame.transform.scale(img, (screen_width, screen_height - bottom_panel))
    bg_frames.append(img)



def draw_bg():
    global bg_frame_index, bg_frame_timer
    # Update frame timer
    bg_frame_timer += 1
    if bg_frame_timer >= bg_frame_speed:
        bg_frame_timer = 0
        bg_frame_index = (bg_frame_index + 1) % len(bg_frames)  # Loop back to start
    # Draw current frame
    screen.blit(bg_frames[bg_frame_index], (0, 0))


# draw text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# draw panel
def draw_panel():
    screen.blit(panel_img, (0, screen_height - bottom_panel))

    if selected_fighter:
        try:
            face = pygame.image.load(f'img/FaceIcons/{selected_fighter.name}.png').convert_alpha()
            face_scaled = pygame.transform.scale(face, (200, 100))
            screen.blit(face_scaled, (-40, 440))
        except:
            if selected_fighter.icon:
                screen.blit(selected_fighter.icon, (-40, 440))

        # Stats
        draw_text(f'{selected_fighter.name}', font, (255,255,255), 20, screen_height - bottom_panel + 15)
        draw_text(f'HP: {selected_fighter.hp}', font, red, 280, screen_height - bottom_panel + 20)
        draw_text(f'ST: {getattr(selected_fighter, "stress", 0)}', font, light_blue, 280, screen_height - bottom_panel + 50)

        # Draw HP and Stress bars
        hp_bar = HealthBar(
            120, screen_height - bottom_panel + 25,
            selected_fighter.hp, selected_fighter.max_hp,
            width=CAMP_BAR_MAX_WIDTH, reference_max=CAMP_BAR_REF_HP
        )
        hp_bar.draw(selected_fighter.hp, selected_fighter.max_hp)

        if hasattr(selected_fighter, "max_stress"):
            stress_bar = StressBar(
                120, screen_height - bottom_panel + 55,
                getattr(selected_fighter, "stress", 0), selected_fighter.max_stress,
                width=CAMP_BAR_MAX_WIDTH, reference_max=CAMP_BAR_REF_ST
            )
            stress_bar.draw(getattr(selected_fighter, "stress", 0), selected_fighter.max_stress)


class Fighter():
    def __init__(self, x, y, base_img_path, name, max_hp, strength, potions, scale=1.0, icon_path=None):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.stress = 0
        self.max_stress = 200
        self.strength = strength
        self.potions = potions
        self.scale = scale


        # Main sprite
        self.base_image = self.load_scaled_image(base_img_path)
        self.selected_image = self.load_scaled_image(base_img_path.replace('.png', '_selected.png'))
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.x = x
        self.y = y
        self.selected = False

        # Icon for UI panel
        if icon_path:
            icon_img = pygame.image.load(icon_path).convert_alpha()
            self.icon = pygame.transform.scale(icon_img, (200, 100))
        else:
            self.icon = None

    def load_scaled_image(self, path):
        image = pygame.image.load(path).convert_alpha()
        width = int(image.get_width() * self.scale)
        height = int(image.get_height() * self.scale)
        return pygame.transform.scale(image, (width, height))

    def draw(self):
        # Swap image depending on selection
        self.image = self.selected_image if self.selected else self.base_image
        self.rect.center = (self.x, self.y)
        screen.blit(self.image, self.rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def heal(self, amount):
        if self.hp < self.max_hp:
            heal_amount = min(amount, self.max_hp - self.hp)
            self.hp += heal_amount
            return heal_amount
        return 0



class HealthBar():
    def __init__(self, x, y, hp, max_hp, width=120, reference_max=200, height=20,
                 bg_color=(255, 0, 0), fill_color=(0, 255, 0)):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = max_hp
        self.width = width
        self.height = height
        self.reference_max = max(1, reference_max)
        self.bg_color = bg_color
        self.fill_color = fill_color

    def draw(self, hp, max_hp=None):
        self.hp = hp
        if max_hp is not None:
            self.max_hp = max_hp
        ratio = max(0.0, min(1.0, self.hp / self.reference_max))
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.fill_color, (self.x, self.y, int(self.width * ratio), self.height))


class StressBar():
    def __init__(self, x, y, st, max_st, width=120, reference_max=200, height=20,
                 bg_color=(255, 255, 255), fill_color=(173, 216, 230)):
        self.x = x
        self.y = y
        self.st = st
        self.max_st = max_st
        self.width = width
        self.height = height
        self.reference_max = max(1, reference_max)
        self.bg_color = bg_color
        self.fill_color = fill_color

    def draw(self, st, max_st=None):
        self.st = st
        if max_st is not None:
            self.max_st = max_st
        ratio = max(0.0, min(1.0, self.st / self.reference_max))
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.fill_color, (self.x, self.y, int(self.width * ratio), self.height))



# Floating heal text
class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage, colour):
        super().__init__()
        self.image = font.render(str(damage), True, colour)
        self.rect = self.image.get_rect(center=(x, y))
        self.counter = 0

    def update(self):
        self.rect.y -= 1
        self.counter += 1
        if self.counter > 30:
            self.kill()

damage_text_group = pygame.sprite.Group()

def heal_hp(fighter, amount):
    if fighter:
        healed_amount = min(fighter.max_hp - fighter.hp, amount)
        fighter.hp += healed_amount
        if healed_amount > 0:
            damage_text_group.add(DamageText(fighter.x, fighter.y - 50, f'+{healed_amount} HP', green))

def reduce_stress(fighter, amount):
    if fighter:
        reduced_amount = min(fighter.stress, amount)
        fighter.stress -= reduced_amount
        if reduced_amount > 0:
            damage_text_group.add(DamageText(fighter.x, fighter.y - 50, f'-{reduced_amount} ST', yellow))

def draw_camp_scene():
    draw_bg()
    draw_panel()
    for fighter in fighters:
        fighter.draw()
    for btn_data in heal_buttons:
        screen.blit(btn_data["normal_img"] if not btn_data["used"] else btn_data["used_img"],
                    btn_data["button"].rect.topleft)
    damage_text_group.update()
    damage_text_group.draw(screen)


fighters = [
    Fighter(340, 210, 'img/Background/Camp/arbalest.png', 'Arbalest', 200, 8, 1, scale=0.9, icon_path='img/FaceIcons/Arbalest.png'),
    Fighter(350, 210, 'img/Background/Camp/knight.png', 'Warrior', 200, 10, 1, scale=0.9, icon_path='img/FaceIcons/Warrior.png'),
    Fighter(460, 220, 'img/Background/Camp/rogue.png', 'Rogue', 200, 9, 1, scale=0.9, icon_path='img/FaceIcons/Rogue.png'),
    Fighter(470, 220, 'img/Background/Camp/elf.png', 'Elf', 200, 11, 1, scale=0.9, icon_path='img/FaceIcons/Elf.png'),
]


# HITBOXES MALAKES DE KSERETE POSH WRA MOU PHRE
gen_buttons = [
    button.Button(screen, 70, 180, None, 100, 170),   # Arbalest
    button.Button(screen, 190, 130, None, 80, 170),  # Knight
    button.Button(screen, 530, 130, None, 100, 170),  # Rogue
    button.Button(screen, 665, 180, None, 100, 170),  # Elf
]

continue_buttn = button.Button(screen, 580, 20, continue_img, 200, 40)

# Healing button definitions (x, y, normal_img, used_img, heal_amount, is_hp, name)
heal_button_defs = [
    (450, screen_height - bottom_panel + 30, heal_hp_1, heal_hp_1_used, 50, True, "RTFM :D +50 HP"),
    (530, screen_height - bottom_panel + 30, heal_hp_2, heal_hp_2_used, 100, True, "Teacher's notes +100 HP"),
    (610, screen_height - bottom_panel + 30, heal_stress_1, heal_stress_1_used, 50, False, "Scratch -50 stress"),
    (690, screen_height - bottom_panel + 30, heal_stress_2, heal_stress_2_used, 100, False, "Afternoon nap -100 stress"),
]

heal_buttons = []
for x, y, img, used_img, amount, is_hp, name in heal_button_defs:
    button_obj = button.Button(screen, x, y, img, 64, 64)
    heal_buttons.append({
        "button": button_obj,
        "normal_img": pygame.transform.scale(img, (64, 64)),
        "used_img": pygame.transform.scale(used_img, (64, 64)),
        "used": False,
        "amount": amount,
        "is_hp": is_hp,
        "name": name,  # store custom name
    })


# Healing amounts
heal_amounts = [50, 100, 100, 50]


def _sync_back_and_save(camp_fighters, battle_heroes):
    for cf in camp_fighters:
        dst = getattr(cf, "source", None)
        if not dst:
            name_map = {h.name: h for h in battle_heroes}
            dst = name_map.get(cf.name)
            if not dst:
                continue

        # Copy stats with clamping
        dst.hp = max(0, min(dst.max_hp, cf.hp))
        if hasattr(dst, "max_stress"):
            dst.stress = max(0, min(dst.max_stress, getattr(cf, "stress", 0)))

        # Revive if healed above 0
        was_dead = not getattr(dst, "alive", True)
        dst.alive = dst.hp > 0
        if dst.alive and was_dead:
            dst.frame_index = 0
            dst.action = dst.action_dict.get("Idle", 0)
            setattr(dst, "reflowed", False)

    reflow_alive_into_front(battle_heroes)
    save_party_layout(battle_heroes)





# -------------------- AUTO TO DEF EINAI POU ENWNEI TO MAIN.PY ME TO CAMP --------------------------


def start_camp(fighters_from_battle,brightness_level):
    global selected_fighter, run, TUTORIAL_SHOWN_MINI
    selected_fighter = None
    pygame.mouse.set_visible(True)
    tutorial_step = 1  # DEIXNEI TO TUTORIAL, YES!


    battle_by_name = {h.name: h for h in fighters_from_battle}

    # Link each camp fighter to the real battle object and copy stats
    for f in fighters:
        src = battle_by_name.get(f.name)
        f.source = src
        if src:
            f.hp = src.hp
            f.stress = min(getattr(src, 'stress', 0), f.max_stress)
        else:
            f.source = None


    # RESET TA HP POT KOUMPIA MESA STO CAMP
    for btn_data in heal_buttons:
        btn_data["used"] = False

    # Game loop
    run = True
    while run:
        clock.tick(fps)
        draw_bg()
        draw_panel()

        for fighter in fighters:
            fighter.draw()

        # ---------- TUTORIAL PAUSE ----------
        if tutorial_step:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if tutorial_step == 1:
                        tutorial_step = 0  # DONE WITH TUTORIAL
                        TUTORIAL_SHOWN_MINI = True  # NEVER SHOW AGAIN AFTER ONE TIME

            img = scaled_camp_tut_img
            rect = img.get_rect(center=(400, 250))
            screen.blit(img, rect)

            Options.apply_brightness_overlay(screen, brightness_level)
            pygame.display.update()
            continue
        # ---------- END TUTORIAL PAUSE ----------


        # --- Draw heal buttons ---
        for btn_data in heal_buttons:
            if not btn_data["used"]:
                screen.blit(btn_data["normal_img"], btn_data["button"].rect.topleft)
            else:
                screen.blit(btn_data["used_img"], btn_data["button"].rect.topleft)


        # Remove selection logic from here:
        for i, btn in enumerate(gen_buttons):
            btn.draw()


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _sync_back_and_save(fighters, fighters_from_battle)
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                clicked_on_fighter = False

                # Check UI buttons first
                for i, btn in enumerate(gen_buttons):
                    if btn.rect.collidepoint(mouse_pos):
                        if selected_fighter == fighters[i]:
                            fighters[i].selected = False
                            selected_fighter = None
                        else:
                            for f in fighters:
                                f.selected = False
                            fighters[i].selected = True
                            selected_fighter = fighters[i]
                        clicked_on_fighter = True
                        break

                # Check healing buttons
                for i, btn_data in enumerate(heal_buttons):
                    if btn_data["button"].rect.collidepoint(mouse_pos) and selected_fighter and not btn_data["used"]:
                        if btn_data["is_hp"]:
                            healed = selected_fighter.heal(btn_data["amount"])
                            if healed > 0:
                                damage_text_group.add(
                                    DamageText(selected_fighter.x, selected_fighter.y - 40, f"+{healed}", green)
                                )
                        else:
                            reduced = min(selected_fighter.stress, btn_data["amount"])
                            selected_fighter.stress -= reduced
                            if reduced > 0:
                                damage_text_group.add(
                                    DamageText(selected_fighter.x, selected_fighter.y - 40, f"-{reduced} ST", light_blue)
                                )

                        # Mark this button as used
                        btn_data["used"] = True


        damage_text_group.update()
        damage_text_group.draw(screen)

        # hovering logic

        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(gen_buttons):
            if btn.rect.collidepoint(mouse_pos):
                name = fighters[i].name
                name_x = mouse_pos[0] + 15
                name_y = mouse_pos[1] - 10

                # Render the text surface first
                name_surface = font.render(name, True, yellow)
                name_rect = name_surface.get_rect(topleft=(name_x, name_y))

                # Draw the hovering box
                padding = 4
                bg_rect = pygame.Rect(
                    name_rect.x - padding,
                    name_rect.y - padding,
                    name_rect.width + padding * 2,
                    name_rect.height + padding * 2
                )
                pygame.draw.rect(screen, (50, 50, 50), bg_rect)
                pygame.draw.rect(screen, yellow, bg_rect, 1)  # Optional border

                # Blit the name on top
                screen.blit(name_surface, name_rect)

        # hover over heal buttons
        for btn_data in heal_buttons:
            if btn_data["button"].rect.collidepoint(mouse_pos):
                if btn_data["used"]:
                    tooltip_text = "Already used!"
                else:
                    tooltip_text = btn_data["name"]  # custom name

                # Render text
                tooltip_surface = font.render(tooltip_text, True, yellow)
                tooltip_rect = tooltip_surface.get_rect(topleft=(mouse_pos[0] - 190, mouse_pos[1] + 20))

                # Background rectangle (dark gray with padding)
                padding = 4
                bg_rect = pygame.Rect(
                    tooltip_rect.x - padding,
                    tooltip_rect.y - padding,
                    tooltip_rect.width + padding * 2,
                    tooltip_rect.height + padding * 2
                )
                pygame.draw.rect(screen, (50, 50, 50), bg_rect)
                pygame.draw.rect(screen, yellow, bg_rect, 1)

                # Blit text
                screen.blit(tooltip_surface, tooltip_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if continue_buttn.draw():
            _sync_back_and_save(fighters, fighters_from_battle)
            run = False

        Options.apply_brightness_overlay(screen, brightness_level)

        pygame.display.update()

    return brightness_level

