# intro.py – panel fill fix + proper typewriter + “appear_on” overlay triggers
import os
import pygame

try:
    from options import Options
    USE_BRIGHTNESS = True
except Exception:
    USE_BRIGHTNESS = False

# h othonh mas
BOTTOM_PANEL = 150
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400 + BOTTOM_PANEL

# variables
MUSIC_PATH = "assets/TES V Skyrim Soundtrack - Far Horizons.mp3"
PANEL_IMAGE_PATH = "img/Background/Box.png"    # panel image
PANEL_FILL_COLOR = (12, 12, 12)
FIT_MODE = "cover"
TYPEWRITER_CPS = 45
FAST_CPS = 180
LINE_HEIGHT = 26
PANEL_PADDING = 16
TEXT_COLOR = (240, 240, 240)
OUTLINE = (30, 30, 30)
FADE_MS_BG = 400         # fade duration when BG changes
FADE_MS_OVERLAY = 250    # soft fade when overlays first appear
HELP_TEXT = "SPACE: fast • ENTER/CLICK: next • ESC/S: skip"

# --------- SCENES ----------
SCENES = [
    ("img/Background/hamlet2.png",
     "Once upon a time, in the heart of a peaceful forest, lay a small hamlet filled with hope and laughter."),

    ("img/Background/hamlet2.png",
     "But beyond its borders, rumors whispered of a darker half of the woods... where fear itself had taken form."),

    ("img/Background/forest.png",
     "Strange beings now dwell there — not mere beasts, but trials born from doubt, stress, and the weight of study."),

    ("img/Background/forest.png",
     "They are living lessons twisted into monsters, feeding on the mind’s fear of failure and the burden of challenge."),

    ("img/Background/hamlet2.png",
     "Yet, four brave souls have stepped forward to face them..."),
    {
        "bg": "img/Background/hamlet2.png",
        "text": (
            "A cunning rogue... "
            "a steadfast warrior... "
            "a wise elf mage... "
            "and a vigilant arbalest."
        ),
        "overlays": [
            {"path": "img/FaceIcons/RogueBust.png",    "pos": (120, 400), "anchor": "midbottom", "scale": 0.6, "appear_on": "rogue"},
            {"path": "img/FaceIcons/WarriorBust.png",  "pos": (320, 400), "anchor": "midbottom", "scale": 0.6, "appear_on": "warrior"},
            {"path": "img/FaceIcons/ElfBust.png",      "pos": (520, 400), "anchor": "midbottom", "scale": 0.6, "appear_on": "elf"},
            {"path": "img/FaceIcons/ArbalestBust.png", "pos": (700, 400), "anchor": "midbottom", "scale": 0.6, "appear_on": "arbalest"},
        ],
    },

    ("img/Background/hamlet2.png",
     "Together they march, proving that even the hardest lessons can be faced — and overcome — when you stand tall."),

    ("img/Background/hamlet2.png",
     "Every monster, like every class, is but a challenge. And with courage, teamwork, and persistence, each one can be conquered."),

    ("img/Background/hamlet2.png",
     "To rise against your fears... to master the trials ahead... and to emerge stronger than before. This is your fight.")
]
# ---------------------------------------------------


def _get_screen():
    surf = pygame.display.get_surface()
    if surf is None:
        pygame.display.set_caption("Intro")
        surf = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    return surf

def _load_image(path):
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        img = pygame.Surface((64, 64), pygame.SRCALPHA)
        img.fill((10, 10, 10, 255))
    return img

def _fit_image(img, target_rect, mode="contain"):
    w, h = img.get_size()
    tw, th = target_rect.size
    if mode == "cover":
        scale = max(tw / w, th / h)
    else:
        scale = min(tw / w, th / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    scaled = pygame.transform.smoothscale(img, new_size)
    if mode == "cover":
        sx, sy = scaled.get_size()
        x = max(0, (sx - tw) // 2)
        y = max(0, (sy - th) // 2)
        return scaled.subsurface(pygame.Rect(x, y, tw, th)).copy()
    return scaled

def _draw_image_area(surface, image):
    view_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_PANEL)
    surface.fill((0, 0, 0), view_rect)
    img_rect = image.get_rect(center=view_rect.center)
    surface.blit(image, img_rect)
    return view_rect

def _draw_panel(surface, panel_img):
    """Covers the entire bottom with a solid fill, then draws the scaled panel image on top."""
    panel_rect = pygame.Rect(0, SCREEN_HEIGHT - BOTTOM_PANEL, SCREEN_WIDTH, BOTTOM_PANEL)

    # fill the entire area
    fill = pygame.Surface(panel_rect.size).convert()
    fill.fill(PANEL_FILL_COLOR)
    surface.blit(fill, panel_rect.topleft)

    if panel_img:
        # scale
        scaled = pygame.transform.smoothscale(panel_img, panel_rect.size)
        surface.blit(scaled, panel_rect.topleft)

    pygame.draw.rect(surface, OUTLINE, panel_rect, 2)
    return panel_rect

def _wrap_to_width(text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def _render_typewriter(surface, font, lines, visible_chars, panel_img):
    panel_rect = _draw_panel(surface, panel_img)
    max_w = panel_rect.width - 2 * PANEL_PADDING
    x = panel_rect.left + PANEL_PADDING
    y = panel_rect.top + PANEL_PADDING + 20
    full_text = "\n".join(lines)
    partial = full_text[:max(0, visible_chars)]
    for i, line in enumerate(partial.split("\n")):
        surface.blit(font.render(line, True, TEXT_COLOR), (x, y + i * LINE_HEIGHT))
    return full_text, partial  # return both for keyword triggers

def _fade_black(surface, clock, start_alpha, end_alpha, duration_ms):
    if duration_ms <= 0:
        return
    overlay = pygame.Surface(surface.get_size()).convert()
    overlay.fill((0, 0, 0))
    t = 0
    while t < duration_ms:
        dt = clock.tick(60)
        t += dt
        a = int(start_alpha + (end_alpha - start_alpha) * min(1.0, t / duration_ms))
        overlay.set_alpha(max(0, min(255, a)))
        surface.blit(overlay, (0, 0))
        pygame.display.update()

def _scene_to_dict(scene):
    """Accept (bg, text) tuples or rich dict scenes; normalize to dict."""
    if isinstance(scene, dict):
        return {
            "bg": scene.get("bg", ""),
            "text": scene.get("text", ""),
            "overlays": scene.get("overlays", []) or [],
        }
    bg, text = scene
    return {"bg": bg, "text": text, "overlays": []}

def _place_overlay(surf, img, pos, anchor, scale=1.0, alpha=255):
    if scale != 1.0:
        w, h = img.get_size()
        img = pygame.transform.smoothscale(img, (max(1, int(w*scale)), max(1, int(h*scale))))
    if alpha is not None:
        img = img.copy()
        img.set_alpha(alpha)
    rect = img.get_rect()
    setattr(rect, anchor if hasattr(rect, anchor) else "topleft", pos)
    surf.blit(img, rect)

def _compose_scene(view_rect, bg_img, overlays, overlay_cache, overlay_alpha_map):
    """Return a new surface with background + overlays drawn."""
    frame = pygame.Surface(view_rect.size, pygame.SRCALPHA)
    frame.blit(bg_img, bg_img.get_rect(center=frame.get_rect().center))

    for ov in overlays:
        path = ov.get("path", "")
        if not path:
            continue
        pos = ov.get("pos", (0, 0))
        anchor = ov.get("anchor", "topleft")
        scale = float(ov.get("scale", 1.0))
        base_alpha = int(ov.get("alpha", 255))
        img = overlay_cache.get(path)
        if img is None:
            img = _load_image(path)
            overlay_cache[path] = img
        a = min(base_alpha, overlay_alpha_map.get(path, base_alpha))
        _place_overlay(frame, img, pos, anchor, scale, a)

    return frame

# --------------------- MAIN LOOP -------------------
def play_intro(brightness_level=1.0):
    if not pygame.get_init():
        pygame.init()
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception:
            pass

    screen = _get_screen()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Times New Roman", 25)

    # music
    try:
        if os.path.exists(MUSIC_PATH):
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.play(loops=0)
    except Exception:
        pass

    # panel image
    panel_img = pygame.image.load(PANEL_IMAGE_PATH).convert_alpha() if os.path.exists(PANEL_IMAGE_PATH) else None

    # normalize scenes
    norm_scenes = [_scene_to_dict(s) for s in SCENES]

    # preload kai fit gia ta backgrounds
    view_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT - BOTTOM_PANEL)
    bg_fitted = {}
    for s in norm_scenes:
        p = s["bg"]
        if p and p not in bg_fitted:
            raw = _load_image(p)
            bg_fitted[p] = _fit_image(raw, view_rect, FIT_MODE)

    overlay_cache = {}

    wrapped = []
    max_text_width = SCREEN_WIDTH - 2 * PANEL_PADDING
    for s in norm_scenes:
        lines = []
        for para in s["text"].split("\n"):
            lines.extend(_wrap_to_width(para, font, max_text_width))
        wrapped.append(lines)

    help_surf = font.render(HELP_TEXT, True, (200, 200, 200))

    cur = 0
    char_progress = 0.0
    visible_chars = 0

    # BG tracking
    cur_bg_path = norm_scenes[0]["bg"] if norm_scenes else ""
    cur_bg_img = bg_fitted.get(cur_bg_path, pygame.Surface(view_rect.size))

    # overlays that persist across scenes once “unlocked”
    persistent_overlays = []   # list of overlay dicts (with pos/anchor/scale/alpha)
    unlocked_paths = set()     # which overlay paths are already unlocked

    # alpha control for fades
    overlay_alpha_map = {}     # path -> current alpha
    overlay_targets   = {}     # path -> target alpha

    # arxiko fade in
    _fade_black(screen, clock, 255, 0, FADE_MS_BG)

    while cur < len(norm_scenes):
        dt = clock.tick(60) / 1000.0
        cps = FAST_CPS if pygame.key.get_pressed()[pygame.K_SPACE] else TYPEWRITER_CPS

        scene = norm_scenes[cur]
        lines = wrapped[cur]

        # increment char progress smoothly
        char_progress += cps * dt
        # clamp at total length after rendering
        full_text = "\n".join(lines)
        total_chars = len(full_text)
        visible_chars = min(total_chars, int(char_progress))

        # BG change with fade
        if scene["bg"] != cur_bg_path:
            _fade_black(screen, clock, 0, 255, FADE_MS_BG)
            cur_bg_path = scene["bg"]
            cur_bg_img = bg_fitted.get(cur_bg_path, cur_bg_img)
            _fade_black(screen, clock, 255, 0, FADE_MS_BG)


        active_overlays = list(persistent_overlays)


        for ov in scene.get("overlays", []):
            if ov.get("appear_on"):  # skip triggered ones for now
                continue
            if ov not in active_overlays:
                active_overlays.append(ov)

        # trigger overlays with appear_on when the keyword is visible in the text
        _, partial_text = _render_typewriter(screen, font, lines, visible_chars, panel_img)
        partial_low = partial_text.lower()

        for ov in scene.get("overlays", []):
            keyword = ov.get("appear_on")
            if not keyword:
                continue
            path = ov.get("path", "")
            if not path:
                continue
            if path in unlocked_paths:
                # once unlocked, ensure it’s included in persistent overlays
                if ov not in persistent_overlays:
                    persistent_overlays.append(ov)
                if ov not in active_overlays:
                    active_overlays.append(ov)
                continue
            # first-time trigger: when the keyword appears in visible text
            if keyword.lower() in partial_low:
                unlocked_paths.add(path)
                # start from alpha 0 and fade to target
                overlay_alpha_map[path] = 0
                overlay_targets[path] = int(ov.get("alpha", 255))
                persistent_overlays.append(ov)
                active_overlays.append(ov)

        # animate alpha for all overlays that are present
        for ov in active_overlays:
            path = ov.get("path", "")
            if not path:
                continue
            target = int(ov.get("alpha", 255))
            tgt = overlay_targets.get(path, target)
            cur_a = overlay_alpha_map.get(path, (0 if path in unlocked_paths else target))

            if cur_a < tgt:
                step = int(255 * dt / max(0.001, FADE_MS_OVERLAY / 1000.0))
                cur_a = min(tgt, cur_a + step)
            elif cur_a > tgt:
                cur_a = max(tgt, cur_a - 15)
            overlay_alpha_map[path] = cur_a

        view_surface = _compose_scene(view_rect, cur_bg_img, active_overlays, overlay_cache, overlay_alpha_map)

        # Draw frame
        screen.fill((0, 0, 0))
        screen.blit(view_surface, (0, 0))
        full_text, partial_text = _render_typewriter(screen, font, lines, visible_chars, panel_img)
        screen.blit(help_surf, (10, 10))

        if USE_BRIGHTNESS:
            try:
                Options.apply_brightness_overlay(screen, brightness_level)
            except Exception:
                pass

        pygame.display.update()

        # Inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return ("SKIP", brightness_level)
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_s):
                    return ("SKIP", brightness_level)
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if visible_chars < total_chars:
                        char_progress = total_chars
                        visible_chars = total_chars
                    else:
                        # next scene
                        cur += 1
                        char_progress = 0.0
                        visible_chars = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                if visible_chars < total_chars:
                    char_progress = total_chars
                    visible_chars = total_chars
                else:
                    cur += 1
                    char_progress = 0.0
                    visible_chars = 0

    _fade_black(screen, clock, 0, 255, FADE_MS_BG)
    try:
        pygame.mixer.music.fadeout(300)
    except Exception:
        pass
    return ("OK", brightness_level)


if __name__ == "__main__":
    pygame.init()
    status, _ = play_intro(1.0)
    print("Intro finished:", status)
    pygame.quit()
