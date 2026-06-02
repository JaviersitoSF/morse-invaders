import random
import sys
from array import array
from math import pi, sin

import pygame

from Invader import Invader
from levels import DEFAULT_WPM, WPM_MAX, WPM_MIN, get_word_bank


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 640
FPS = 60
MAX_INVADERS = 3

BG = (10, 14, 24)
PANEL = (21, 29, 44)
WHITE = (238, 244, 255)
MUTED = (137, 150, 173)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
YELLOW = (250, 204, 21)
CYAN = (56, 189, 248)


class MorsePlayer:
    LETTER_GAP_UNITS = 3
    WORD_GAP_UNITS = 7

    def __init__(self, wpm):
        self.enabled = pygame.mixer.get_init() is not None
        self.queue = []
        self.next_at = 0
        self.set_wpm(wpm)

    def set_wpm(self, wpm):
        self.wpm = max(1, int(wpm))
        self.unit_ms = 1200 / self.wpm

        if not self.enabled:
            return

        self.dot = self.create_tone(self.unit_ms)
        self.dash = self.create_tone(self.unit_ms * 3)
        self.symbol_gap = self.unit_ms
        self.letter_gap = self.unit_ms * self.LETTER_GAP_UNITS
        self.word_gap = self.unit_ms * self.WORD_GAP_UNITS

    def create_tone(self, duration_ms, frequency=720, volume=0.35):
        sample_rate = pygame.mixer.get_init()[0]
        sample_count = int(sample_rate * duration_ms / 1000)
        amplitude = int(32767 * volume)
        samples = array("h")

        for index in range(sample_count):
            wave = sin(2 * pi * frequency * index / sample_rate)
            samples.append(int(amplitude * wave))

        return pygame.mixer.Sound(buffer=samples)

    def play(self, morse_code):
        if not self.enabled:
            return

        self.queue = self.build_queue(morse_code)
        self.next_at = pygame.time.get_ticks()
        self.update()

    def build_queue(self, morse_code):
        queue = []
        letters = morse_code.split(" ")

        for letter_index, letter in enumerate(letters):
            if letter == "/":
                queue.append((None, self.word_gap))
                continue

            for symbol_index, symbol in enumerate(letter):
                queue.append((self.dot if symbol == "." else self.dash, 0))

                if symbol_index < len(letter) - 1:
                    queue.append((None, self.symbol_gap))

            if letter_index < len(letters) - 1:
                queue.append((None, self.letter_gap))

        return queue

    def update(self):
        if not self.enabled or not self.queue:
            return

        now = pygame.time.get_ticks()

        if now < self.next_at:
            return

        sound, gap = self.queue.pop(0)

        if sound is None:
            self.next_at = now + gap
            return

        sound.play()
        self.next_at = now + int(sound.get_length() * 1000)

    def is_playing(self):
        if not self.enabled:
            return False

        return bool(self.queue) or pygame.time.get_ticks() < self.next_at


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Morse Invaders")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.Font(None, 52)
        self.font = pygame.font.Font(None, 34)
        self.font_small = pygame.font.Font(None, 24)

        self.running = True
        self.state = "menu"
        self.selected_wpm = DEFAULT_WPM
        self.wpm = DEFAULT_WPM
        self.spawn_interval_ms = self.word_interval_for_wpm(self.selected_wpm)
        self.next_spawn_at = 0
        self.score = 0
        self.lives = 3
        self.invaders = []
        self.active = None
        self.message = "Choose a WPM and press Enter"
        self.morse_player = MorsePlayer(self.selected_wpm)
        self.word_bag = []

    @staticmethod
    def word_interval_for_wpm(wpm):
        return max(250, int(60000 / max(1, wpm)))

    @staticmethod
    def fall_speed_for_wpm(wpm):
        return 60 + (wpm * 2.5)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()

            if self.state == "playing":
                self.update(dt)

            self.draw()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.state == "playing":
                self.select_invader(event.pos)

    def handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.running = False
            return

        if self.state == "menu":
            self.handle_menu_key(event)
        elif self.state == "game_over":
            self.handle_game_over_key(event)
        elif self.state == "playing":
            self.handle_playing_key(event)

    def handle_menu_key(self, event):
        if event.key in (pygame.K_LEFT, pygame.K_DOWN, pygame.K_a):
            self.adjust_wpm(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_UP, pygame.K_d):
            self.adjust_wpm(1)
        elif event.key == pygame.K_RETURN:
            self.start_game()

    def handle_game_over_key(self, event):
        if event.key == pygame.K_RETURN:
            self.start_game()
        elif event.key == pygame.K_m:
            self.state = "menu"
            self.message = "Choose a WPM and press Enter"

    def handle_playing_key(self, event):
        if event.unicode and event.unicode.isalnum():
            self.answer(event.unicode)
        elif event.key == pygame.K_BACKSPACE and self.active:
            self.active.backspace()
        elif event.key == pygame.K_TAB:
            self.cycle_target()

    def adjust_wpm(self, delta):
        self.selected_wpm = max(WPM_MIN, min(WPM_MAX, self.selected_wpm + delta))
        self.message = f"Selected WPM {self.selected_wpm}"

    def start_game(self):
        self.state = "playing"
        self.wpm = self.selected_wpm
        self.score = 0
        self.lives = 3
        self.invaders.clear()
        self.active = None
        self.word_bag.clear()
        self.morse_player = MorsePlayer(self.wpm)
        self.spawn_interval_ms = self.word_interval_for_wpm(self.wpm)
        self.next_spawn_at = pygame.time.get_ticks()
        self.message = f"{self.wpm} WPM"
        self.spawn_invader()

    def update(self, dt):
        now = pygame.time.get_ticks()
        self.morse_player.update()

        if now >= self.next_spawn_at and not self.morse_player.is_playing():
            self.spawn_invader()

        for invader in self.invaders[:]:
            invader.move(dt)

            if invader.has_landed(SCREEN_HEIGHT):
                self.invaders.remove(invader)
                self.lives -= 1
                self.message = f"{invader.label} reached the ground"

                if self.active is invader:
                    self.active = None

        if self.lives <= 0:
            self.state = "game_over"
            self.message = "Press Enter to restart or M for menu"

        if self.active not in self.invaders:
            self.active = None

    def spawn_invader(self):
        if len(self.invaders) >= MAX_INVADERS:
            self.next_spawn_at = pygame.time.get_ticks() + self.spawn_interval_ms
            return

        word = self.next_word()
        invader = Invader(word, self.fall_speed_for_wpm(self.wpm), SCREEN_WIDTH)
        self.invaders.append(invader)
        self.next_spawn_at = pygame.time.get_ticks() + self.spawn_interval_ms
        self.morse_player.play(invader.hint)

    def next_word(self):
        if not self.word_bag:
            self.word_bag = get_word_bank()
            random.shuffle(self.word_bag)

        return self.word_bag.pop()

    def answer(self, char):
        if self.state != "playing":
            return

        candidates = self.matching_invaders(char)

        if not candidates:
            for invader in self.invaders:
                invader.shake_timer = 10
            self.message = "Decoded key does not match any signal"
            return

        for invader in candidates:
            invader.accept(char)

        target = self.best_target(candidates)
        self.active = target
        self.message = f"Decoding {target.typed}"

        destroyed = [invader for invader in candidates if invader.is_destroyed()]

        if destroyed:
            reward = sum(20 + len(invader.text) * 10 for invader in destroyed)
            self.score += reward
            self.message = f"{', '.join(invader.label for invader in destroyed)} decoded +{reward}"

            for invader in destroyed:
                self.invaders.remove(invader)

            self.active = None

    def matching_invaders(self, char):
        return [invader for invader in self.invaders if invader.can_accept(char)]

    def best_target(self, candidates):
        if self.active in candidates:
            return self.active

        return max(candidates, key=lambda invader: (len(invader.typed), invader.y))

    def select_invader(self, pos):
        for invader in reversed(self.invaders):
            if invader.hitbox(self.font_small).collidepoint(pos):
                self.active = invader
                self.message = "Targeting selected signal"
                return

    def cycle_target(self):
        if not self.invaders:
            self.active = None
            return

        if self.active not in self.invaders:
            self.active = self.invaders[0]
            return

        index = (self.invaders.index(self.active) + 1) % len(self.invaders)
        self.active = self.invaders[index]
        self.message = "Targeting next signal"

    def draw(self):
        self.screen.fill(BG)
        self.draw_stars()

        if self.state == "menu":
            self.draw_menu()
        else:
            self.draw_hud()

            for invader in self.invaders:
                self.draw_invader(invader)

            if self.state == "game_over":
                self.draw_game_over()

        pygame.display.flip()

    def draw_stars(self):
        for x, y in ((80, 120), (210, 84), (350, 168), (510, 110), (720, 150), (830, 82)):
            pygame.draw.circle(self.screen, (45, 58, 82), (x, y), 2)

    def draw_menu(self):
        self.text("Morse Invaders", self.font_big, WHITE, SCREEN_WIDTH // 2, 150)
        self.text("Choose starting speed", self.font, MUTED, SCREEN_WIDTH // 2, 206)
        self.draw_wpm_slider()
        self.text(f"{self.selected_wpm} WPM", self.font_big, YELLOW, SCREEN_WIDTH // 2, 326)
        self.text("Left and right change the speed", self.font_small, MUTED, SCREEN_WIDTH // 2, 394)
        self.text("Press Enter to begin", self.font_small, MUTED, SCREEN_WIDTH // 2, 424)

    def draw_wpm_slider(self):
        bar_left = 210
        bar_top = 276
        bar_width = 480
        bar_height = 12
        percent = (self.selected_wpm - WPM_MIN) / max(1, WPM_MAX - WPM_MIN)
        fill_width = int(bar_width * percent)
        knob_x = bar_left + fill_width

        pygame.draw.rect(self.screen, (33, 44, 66), (bar_left, bar_top, bar_width, bar_height), border_radius=6)
        pygame.draw.rect(self.screen, CYAN, (bar_left, bar_top, fill_width, bar_height), border_radius=6)
        pygame.draw.circle(self.screen, WHITE, (knob_x, bar_top + bar_height // 2), 10)
        self.text(f"{WPM_MIN} WPM", self.font_small, MUTED, bar_left, bar_top + 28, center=False)
        self.text(f"{WPM_MAX} WPM", self.font_small, MUTED, bar_left + bar_width, bar_top + 28, center=False, right=True)

    def draw_hud(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, SCREEN_WIDTH, 86))
        self.text("Morse Invaders", self.font, WHITE, 24, 18, center=False)
        self.text(f"Score {self.score}", self.font_small, GREEN, 24, 54, center=False)
        self.text(f"Lives {self.lives}", self.font_small, RED, 140, 54, center=False)
        self.text(f"WPM {self.wpm}", self.font_small, YELLOW, 230, 54, center=False)
        self.text(self.message, self.font_small, MUTED, SCREEN_WIDTH - 24, 54, center=False, right=True)

    def draw_invader(self, invader):
        active = invader is self.active
        x = invader.x + (4 if invader.shake_timer % 2 else 0)
        y = int(invader.y)
        width = max(120, self.font.size(invader.hint)[0] + 18)
        top = y - 28
        progress_left = x - width // 2
        progress_top = top + 58

        pygame.draw.rect(self.screen, (33, 44, 66), (progress_left, progress_top, width, 5), border_radius=3)
        pygame.draw.rect(
            self.screen,
            CYAN if active else GREEN,
            (progress_left, progress_top, int(width * invader.progress), 5),
            border_radius=3,
        )

        self.text(invader.hint, self.font, CYAN if active else WHITE, x, top)
        decoded, remaining = invader.decoded_hint
        answer = decoded + remaining
        color = GREEN if decoded else MUTED
        self.text(answer, self.font_small, color, x, top + 30)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.text("Game Over", self.font_big, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 56)
        self.text(f"Final score {self.score}", self.font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 4)
        self.text(f"Last WPM {self.wpm}", self.font_small, YELLOW, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 36)
        self.text("Enter restarts at the same WPM", self.font_small, MUTED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 68)
        self.text("M returns to the WPM menu", self.font_small, MUTED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 92)

    def text(self, text, font, color, x, y, center=True, right=False):
        surface = font.render(text, True, color)
        rect = surface.get_rect()

        if right:
            rect.midright = (x, y)
        elif center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)

        self.screen.blit(surface, rect)


if __name__ == "__main__":
    Game().run()
