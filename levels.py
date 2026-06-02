DIFFICULTIES = [
    {"name": "Beginner", "wpm": 8, "fall_speed": 34, "max_fall_speed": 90},
    {"name": "Intermediate", "wpm": 12, "fall_speed": 46, "max_fall_speed": 115},
    {"name": "Advanced", "wpm": 18, "fall_speed": 60, "max_fall_speed": 140},
]
DEFAULT_DIFFICULTY_INDEX = 1

WORD_BANK = [
    "E",
    "T",
    "I",
    "A",
    "N",
    "M",
    "S",
    "U",
    "R",
    "W",
    "D",
    "K",
    "G",
    "O",
    "C",
    "H",
    "B",
    "F",
    "L",
    "P",
    "J",
    "V",
    "Q",
    "Y",
    "X",
    "Z",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",
    "CAT",
    "DOG",
    "SUN",
    "RUN",
    "CODE",
    "SHIP",
    "MOON",
    "MORSE",
    "SPACE",
    "LASER",
    "ORBIT",
    "SIGNAL",
    "RADIO",
    "PYTHON",
    "INVADER",
    "CAPTAIN",
    "DESTROY",
    "STATION",
]


TRAINING_STAGES = [
    ["E", "T", "I", "A", "N", "M"],
    ["E", "T", "I", "A", "N", "M", "S", "U", "R", "W", "D", "K", "G", "O"],
    [word for word in WORD_BANK if len(word) == 1],
    WORD_BANK,
]


def get_word_bank(score=0):
    stage_index = min(len(TRAINING_STAGES) - 1, score // 120)
    return TRAINING_STAGES[stage_index][:]
