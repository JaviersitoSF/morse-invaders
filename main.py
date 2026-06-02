import random
import sys
from array import array
from math import cos, pi, sin

import pygame

from Invader import Invader
from levels import DEFAULT_DIFFICULTY_INDEX, DIFFICULTIES, get_word_bank


SCREEN_WIDTH = 900
SCREEN_HEIGHT = 640
FPS = 60
MAX_INVADERS = 1
REVEAL_AFTER_MISSES = 2

BG = (10, 14, 24)
PANEL = (21, 29, 44)
WHITE = (238, 244, 255)
MUTED = (137, 150, 173)
GREEN = (74, 222, 128)
RED = (248, 113, 113)
YELLOW = (250, 204, 21)
CYAN = (56, 189, 248)
ORANGE = (251, 146, 60)
PURPLE = (167, 139, 250)
SHIP = (125, 211, 252)


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
        self.selected_difficulty_index = DEFAULT_DIFFICULTY_INDEX
        self.difficulty = DIFFICULTIES[self.selected_difficulty_index]
        self.wpm = self.difficulty["wpm"]
        self.spawn_interval_ms = self.word_interval_for_wpm(self.wpm)
        self.next_spawn_at = 0
        self.score = 0
        self.lives = 3
        self.invaders = []
        self.active = None
        self.message = "Choose a difficulty and press Enter"
        self.morse_player = MorsePlayer(self.wpm)
        self.word_bag = []
        self.stars = self.create_stars()
        self.particles = []
        self.beams = []
        self.screen_flash = 0

    def create_stars(self):
        stars = []

        for _ in range(74):
            stars.append(
                {
                    "x": random.randrange(0, SCREEN_WIDTH),
                    "y": random.randrange(0, SCREEN_HEIGHT),
                    "speed": random.uniform(16, 62),
                    "size": random.choice((1, 1, 1, 2, 2, 3)),
                    "phase": random.uniform(0, pi * 2),
                }
            )

        return stars

    @staticmethod
    def word_interval_for_wpm(wpm):
        return max(250, int(60000 / max(1, wpm)))

    def fall_speed_for_score(self, score):
        base_speed = self.difficulty["fall_speed"]
        max_speed = self.difficulty["max_fall_speed"]
        return min(max_speed, base_speed + (score * 0.03))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()

            if self.state == "playing":
                self.update(dt)
            else:
                self.update_animations(dt)

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
            self.adjust_difficulty(-1)
        elif event.key in (pygame.K_RIGHT, pygame.K_UP, pygame.K_d):
            self.adjust_difficulty(1)
        elif event.key == pygame.K_RETURN:
            self.start_game()

    def handle_game_over_key(self, event):
        if event.key == pygame.K_RETURN:
            self.start_game()
        elif event.key == pygame.K_m:
            self.state = "menu"
            self.message = "Choose a difficulty and press Enter"

    def handle_playing_key(self, event):
        if event.key == pygame.K_SPACE:
            self.repeat_signal()
        elif event.unicode and event.unicode.isalnum():
            self.answer(event.unicode)
        elif event.key == pygame.K_BACKSPACE and self.active:
            self.active.backspace()
        elif event.key == pygame.K_TAB:
            self.cycle_target()

    def adjust_difficulty(self, delta):
        self.selected_difficulty_index = max(
            0,
            min(len(DIFFICULTIES) - 1, self.selected_difficulty_index + delta),
        )
        self.difficulty = DIFFICULTIES[self.selected_difficulty_index]
        self.wpm = self.difficulty["wpm"]
        self.message = f"Selected {self.difficulty['name']}"

    def start_game(self):
        self.state = "playing"
        self.difficulty = DIFFICULTIES[self.selected_difficulty_index]
        self.wpm = self.difficulty["wpm"]
        self.score = 0
        self.lives = 3
        self.invaders.clear()
        self.active = None
        self.particles.clear()
        self.beams.clear()
        self.screen_flash = 0
        self.word_bag.clear()
        self.morse_player = MorsePlayer(self.wpm)
        self.spawn_interval_ms = self.word_interval_for_wpm(self.wpm)
        self.next_spawn_at = pygame.time.get_ticks()
        self.message = self.difficulty["name"]
        self.spawn_invader()

    def update(self, dt):
        now = pygame.time.get_ticks()
        self.morse_player.update()
        self.update_animations(dt)

        if now >= self.next_spawn_at and not self.morse_player.is_playing():
            self.spawn_invader()

        for invader in self.invaders[:]:
            invader.move(dt)

            if invader.has_landed(SCREEN_HEIGHT):
                self.invaders.remove(invader)
                self.lives -= 1
                self.add_explosion(invader.x, SCREEN_HEIGHT - 72, RED, 34)
                self.screen_flash = 10
                self.message = f"Missed {invader.label}: {invader.hint}"

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
        invader = Invader(word, self.fall_speed_for_score(self.score), SCREEN_WIDTH)
        # print(f"Spawned word={invader.text} morse={invader.hint} score={self.score} speed={invader.speed:.1f}")
        self.invaders.append(invader)
        self.active = invader
        self.next_spawn_at = pygame.time.get_ticks() + self.spawn_interval_ms
        self.morse_player.play(invader.hint)
        self.add_spawn_burst(invader.x, invader.y)

    def next_word(self):
        if not self.word_bag:
            self.word_bag = get_word_bank(self.score)
            random.shuffle(self.word_bag)

        return self.word_bag.pop()

    def answer(self, char):
        if self.state != "playing":
            return

        candidates = self.matching_invaders(char)

        if not candidates:
            for invader in self.invaders:
                invader.miss(REVEAL_AFTER_MISSES)

            revealed = [invader for invader in self.invaders if invader.revealed]
            if revealed:
                self.message = f"Hint {revealed[0].label}: {revealed[0].hint}"
            else:
                self.message = "No match; listen again"
            self.screen_flash = 5
            return

        for invader in candidates:
            invader.accept(char)
            self.add_beam(invader)
            self.add_sparks(invader.x, invader.y, CYAN, 7)

        target = self.best_target(candidates)
        self.active = target
        self.message = f"Decoding {target.typed}"

        destroyed = [invader for invader in candidates if invader.is_destroyed()]

        if destroyed:
            reward = sum(20 + len(invader.text) * 10 for invader in destroyed)
            self.score += reward
            self.message = f"{', '.join(invader.label for invader in destroyed)} decoded +{reward}"

            for invader in destroyed:
                self.add_explosion(invader.x, invader.y, GREEN, 42)
                self.invaders.remove(invader)

            self.screen_flash = 7
            self.active = None

    def update_animations(self, dt):
        now = pygame.time.get_ticks()

        for star in self.stars:
            star["y"] += star["speed"] * (dt / 1000)
            if star["y"] > SCREEN_HEIGHT:
                star["x"] = random.randrange(0, SCREEN_WIDTH)
                star["y"] = -4
                star["speed"] = random.uniform(16, 62)

        for particle in self.particles[:]:
            particle["age"] += dt
            particle["x"] += particle["vx"] * (dt / 1000)
            particle["y"] += particle["vy"] * (dt / 1000)
            particle["vy"] += particle.get("gravity", 0) * (dt / 1000)

            if particle["age"] >= particle["life"]:
                self.particles.remove(particle)

        for beam in self.beams[:]:
            beam["age"] = now - beam["started_at"]

            if beam["age"] >= beam["life"]:
                self.beams.remove(beam)

        self.screen_flash = max(0, self.screen_flash - 1)

    def add_beam(self, invader):
        self.beams.append(
            {
                "x1": SCREEN_WIDTH // 2,
                "y1": SCREEN_HEIGHT - 54,
                "x2": invader.x,
                "y2": invader.y + 8,
                "started_at": pygame.time.get_ticks(),
                "age": 0,
                "life": 160,
            }
        )

    def add_sparks(self, x, y, color, amount):
        for _ in range(amount):
            angle = random.uniform(0, pi * 2)
            speed = random.uniform(40, 150)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": cos(angle) * speed,
                    "vy": sin(angle) * speed,
                    "age": 0,
                    "life": random.randint(260, 520),
                    "size": random.randint(2, 5),
                    "color": color,
                    "gravity": 45,
                }
            )

    def add_explosion(self, x, y, color, amount):
        self.add_sparks(x, y, color, amount)
        self.add_sparks(x, y, ORANGE, amount // 2)

    def add_spawn_burst(self, x, y):
        for _ in range(22):
            angle = random.uniform(0, pi * 2)
            speed = random.uniform(26, 92)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": cos(angle) * speed,
                    "vy": sin(angle) * speed,
                    "age": 0,
                    "life": random.randint(360, 760),
                    "size": random.randint(1, 4),
                    "color": PURPLE,
                    "gravity": 0,
                }
            )

    def matching_invaders(self, char):
        return [invader for invader in self.invaders if invader.can_accept(char)]

    def repeat_signal(self):
        target = self.active if self.active in self.invaders else None

        if target is None and self.invaders:
            target = self.invaders[0]
            self.active = target

        if target is None:
            return

        self.morse_player.play(target.hint)
        self.message = "Signal repeated"

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
            self.draw_beams()

            for invader in self.invaders:
                self.draw_invader(invader)

            self.draw_particles()
            self.draw_player()

            if self.state == "game_over":
                self.draw_game_over()

        self.draw_flash()
        pygame.display.flip()

    def draw_stars(self):
        now = pygame.time.get_ticks() / 1000

        for star in self.stars:
            shimmer = int(22 * (0.5 + 0.5 * sin(now * 2 + star["phase"])))
            color = (45 + shimmer, 58 + shimmer, 82 + shimmer)
            pygame.draw.circle(self.screen, color, (int(star["x"]), int(star["y"])), star["size"])

    def draw_beams(self):
        for beam in self.beams:
            progress = 1 - (beam["age"] / beam["life"])
            color = (min(255, int(CYAN[0] + 120 * progress)), 230, 255)
            width = max(1, int(7 * progress))
            pygame.draw.line(
                self.screen,
                color,
                (beam["x1"], beam["y1"]),
                (beam["x2"], beam["y2"]),
                width,
            )

    def draw_particles(self):
        for particle in self.particles:
            progress = 1 - (particle["age"] / particle["life"])
            size = max(1, int(particle["size"] * progress))
            color = tuple(max(0, int(channel * progress)) for channel in particle["color"])
            pygame.draw.circle(self.screen, color, (int(particle["x"]), int(particle["y"])), size)

    def draw_player(self):
        now = pygame.time.get_ticks() / 1000
        x = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT - 40
        flame = 6 + int(4 * (0.5 + 0.5 * sin(now * 18)))

        pygame.draw.polygon(self.screen, ORANGE, ((x - 10, y + 14), (x + 10, y + 14), (x, y + 14 + flame)))
        pygame.draw.polygon(self.screen, SHIP, ((x, y - 22), (x - 28, y + 18), (x + 28, y + 18)))
        pygame.draw.polygon(self.screen, CYAN, ((x, y - 12), (x - 11, y + 10), (x + 11, y + 10)))
        pygame.draw.rect(self.screen, WHITE, (x - 4, y - 4, 8, 7), border_radius=3)

    def draw_flash(self):
        if self.screen_flash <= 0:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, self.screen_flash * 12))
        self.screen.blit(overlay, (0, 0))

    def draw_menu(self):
        self.text("Morse Invaders", self.font_big, WHITE, SCREEN_WIDTH // 2, 150)
        self.text("Choose difficulty", self.font, MUTED, SCREEN_WIDTH // 2, 206)
        self.draw_difficulty_selector()
        self.text(self.difficulty["name"], self.font_big, YELLOW, SCREEN_WIDTH // 2, 326)
        self.text(f"{self.difficulty['wpm']} WPM audio", self.font_small, MUTED, SCREEN_WIDTH // 2, 364)
        self.text("Left and right change difficulty", self.font_small, MUTED, SCREEN_WIDTH // 2, 404)
        self.text("Press Enter to begin", self.font_small, MUTED, SCREEN_WIDTH // 2, 424)

    def draw_difficulty_selector(self):
        bar_left = 210
        bar_top = 276
        bar_width = 480
        bar_height = 12
        percent = self.selected_difficulty_index / max(1, len(DIFFICULTIES) - 1)
        fill_width = int(bar_width * percent)
        knob_x = bar_left + fill_width

        pygame.draw.rect(self.screen, (33, 44, 66), (bar_left, bar_top, bar_width, bar_height), border_radius=6)
        pygame.draw.rect(self.screen, CYAN, (bar_left, bar_top, fill_width, bar_height), border_radius=6)
        pygame.draw.circle(self.screen, WHITE, (knob_x, bar_top + bar_height // 2), 10)
        self.text(DIFFICULTIES[0]["name"], self.font_small, MUTED, bar_left, bar_top + 28, center=False)
        self.text(
            DIFFICULTIES[-1]["name"],
            self.font_small,
            MUTED,
            bar_left + bar_width,
            bar_top + 28,
            center=False,
            right=True,
        )

    def draw_hud(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, SCREEN_WIDTH, 86))
        self.text("Morse Invaders", self.font, WHITE, 24, 18, center=False)
        self.text(f"Score {self.score}", self.font_small, GREEN, 24, 54, center=False)
        self.text(f"Lives {self.lives}", self.font_small, RED, 140, 54, center=False)
        self.text(f"{self.difficulty['name']} ({self.wpm} WPM)", self.font_small, YELLOW, 230, 54, center=False)
        self.text(self.message, self.font_small, MUTED, SCREEN_WIDTH - 24, 54, center=False, right=True)

    def draw_invader(self, invader):
        active = invader is self.active
        bob = sin(invader.age_ms / 180) * 5
        wobble = cos(invader.age_ms / 250) * 4
        x = int(invader.x + wobble + (4 if invader.shake_timer % 2 else 0))
        y = int(invader.y + bob)
        signal_label = invader.hint if invader.revealed else "Listen"
        width = max(120, self.font.size(signal_label)[0] + 18)
        top = y - 28
        progress_left = x - width // 2
        progress_top = top + 58
        body_color = PURPLE if active else (95, 111, 255)
        eye_color = YELLOW if active else WHITE

        pulse = 1 + int(3 * (0.5 + 0.5 * sin(invader.age_ms / 130)))
        wing_y = y - 8 + int(4 * sin(invader.age_ms / 120))
        pygame.draw.circle(self.screen, (29, 39, 59), (x, y), 36 + pulse, 2)
        pygame.draw.ellipse(self.screen, body_color, (x - 31, y - 22, 62, 36), 0)
        pygame.draw.polygon(self.screen, body_color, ((x - 24, y - 6), (x - 54, wing_y + 20), (x - 16, y + 12)))
        pygame.draw.polygon(self.screen, body_color, ((x + 24, y - 6), (x + 54, wing_y + 20), (x + 16, y + 12)))
        pygame.draw.rect(self.screen, (11, 18, 32), (x - 17, y - 10, 34, 14), border_radius=7)
        pygame.draw.circle(self.screen, eye_color, (x - 8, y - 3), 3)
        pygame.draw.circle(self.screen, eye_color, (x + 8, y - 3), 3)
        pygame.draw.line(self.screen, CYAN if active else MUTED, (x - 14, y + 17), (x - 28, y + 28), 3)
        pygame.draw.line(self.screen, CYAN if active else MUTED, (x + 14, y + 17), (x + 28, y + 28), 3)

        pygame.draw.rect(self.screen, (33, 44, 66), (progress_left, progress_top, width, 5), border_radius=3)
        pygame.draw.rect(
            self.screen,
            CYAN if active else GREEN,
            (progress_left, progress_top, int(width * invader.progress), 5),
            border_radius=3,
        )

        self.text(signal_label, self.font, CYAN if active else WHITE, x, top)
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
