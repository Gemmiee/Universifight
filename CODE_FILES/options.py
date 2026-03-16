import pygame
import pygame_widgets
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
import sys
import button


pygame.init()
pygame.font.init()

font1 = pygame.font.Font("assets/font.ttf", 40)



class Options:
    def __init__(self, screen, screen_width, screen_height, font, back_img, quit_img,current_brightness=100):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.back_img = back_img
        self.quit_img = quit_img

        self.slider1 = Slider(screen, 150, 300, 500, 30,
                              min=0, max=100, step=1,
                              initial=pygame.mixer.music.get_volume() * 100)
        self.slider2 = Slider(screen, 150, 150, 500, 30,
                              min=0, max=100, step=1,
                              initial=current_brightness)
        self.output1 = TextBox(screen, 670, 300, 60, 30, fontSize=18)
        self.output2 = TextBox(screen, 670, 150, 60, 30, fontSize=18)
        self.output1.disable()
        self.output2.disable()
        self.output2.setText(str(int(current_brightness)))

    @staticmethod
    def apply_brightness_overlay(surface, brightness):
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        final_alpha = min(int((1 - brightness) * 255), 233)
        overlay.fill((0, 0, 0, final_alpha))
        surface.blit(overlay, (0, 0))
        return surface

    def run(self, draw_bg, draw_text, brightness_level):
        options_loop = True
        self.font = font1
        widgets = [self.slider1, self.output1, self.slider2, self.output2]

        while options_loop:
            draw_bg()

            options_panel_overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            options_panel_overlay.fill((255, 255, 255, 90))
            self.screen.blit(options_panel_overlay, (0, 0))

            options_text = self.font.render("Options", True, (0, 0, 0))
            options_rect = options_text.get_rect(center=(self.screen_width / 2, 50))
            self.screen.blit(options_text, options_rect)


            volume_text = self.font.render("Volume", True, (0, 255, 0))
            volume_rect = volume_text.get_rect(center=(self.screen_width / 2, 260))
            self.screen.blit(volume_text, volume_rect)


            brightness_text = self.font.render("Brightness", True, (0, 255, 0))
            brightness_rect = brightness_text.get_rect(center=(self.screen_width / 2, 110))
            self.screen.blit(brightness_text, brightness_rect)

            quit_btn = button.Button(self.screen, 50, 450, self.quit_img, 190, 50)
            options_back = button.Button(self.screen, 560, 450, self.back_img, 190, 50)

            events = pygame.event.get()
            for event_o in events:
                pygame_widgets.update(event_o)
                self.output1.setText(str(int(self.slider1.getValue())))
                self.output2.setText(str(int(self.slider2.getValue())))
                pygame.mixer.music.set_volume(self.slider1.getValue() / 100)
                brightness_level = self.slider2.getValue() / 100

            for widget in widgets:
                widget.draw()

            if quit_btn.draw():
                pygame.quit()
                sys.exit()

            if options_back.draw():
                options_loop = False

            self.apply_brightness_overlay(self.screen, brightness_level)
            pygame.display.update()

        return brightness_level


def play_music(path, *, loop=True, fade_ms=800, crossfade_ms=600, volume=1.0):
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    try:
        # fade out whatever is currently playing
        if crossfade_ms and crossfade_ms > 0:
            try:
                pygame.mixer.music.fadeout(crossfade_ms)
            except Exception:
                pass
            # delay
            pygame.time.delay(int(crossfade_ms * 0.6))

        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        pygame.mixer.music.play(loops=-1 if loop else 0,
                                fade_ms=(fade_ms if fade_ms is not None else 0))
    except Exception as e:
        print("Music error:", e)


def stop_music(fade_ms=300):
    try:
        pygame.mixer.music.fadeout(fade_ms)
    except Exception:
        pass



def fade_black(surface, start_alpha, end_alpha, duration_ms):
    if duration_ms <= 0:
        return
    clock = pygame.time.Clock()
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

def fade_out(surface, ms=400):
    fade_black(surface, 0, 255, ms)

def fade_in(surface, ms=400):
    fade_black(surface, 255, 0, ms)
