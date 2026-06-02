from dataclasses import dataclass, field
import random

from morse import encode


@dataclass
class Invader:
    text: str
    speed: float
    screen_width: int
    x: int = field(init=False)
    y: float = 42
    typed: str = ""
    shake_timer: int = 0
    age_ms: int = 0
    mistakes: int = 0
    revealed: bool = False

    def __post_init__(self):
        self.text = self.text.upper()
        self.hint = encode(self.text)
        self.x = random.randint(80, self.screen_width - 80)

    def move(self, dt):
        self.age_ms += dt
        self.y += self.speed * (dt / 1000)
        self.shake_timer = max(0, self.shake_timer - 1)

    def hitbox(self, font):
        hint = font.render(self.hint, True, (255, 255, 255))
        width = hint.get_width() + 28
        height = hint.get_height() * 2 + 18
        return hint.get_rect(center=(self.x, self.y)).inflate(width - hint.get_width(), height)

    def can_accept(self, char):
        return self.text.startswith(self.typed + char.upper())

    def accept(self, char):
        candidate = self.typed + char.upper()

        if self.can_accept(char):
            self.typed = candidate
            return True

        self.shake_timer = 10
        return False

    def miss(self, reveal_after):
        self.mistakes += 1
        self.shake_timer = 10

        if self.mistakes >= reveal_after:
            self.revealed = True

    def backspace(self):
        self.typed = self.typed[:-1]

    def has_landed(self, screen_height):
        return self.y >= screen_height - 64

    def is_destroyed(self):
        return self.typed == self.text

    @property
    def progress(self):
        return len(self.typed) / max(1, len(self.text))

    @property
    def label(self):
        return self.text

    @property
    def decoded_hint(self):
        remaining = "_" * (len(self.text) - len(self.typed))
        return self.typed, remaining
