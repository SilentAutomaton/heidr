import hashlib
import re

ALPHABETS = (
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "abcdefghijklmnopqrstuvwxyz",
)
VOWELS = "аеёиоуыэюяaeiouy"
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# How often each letter turns up in ordinary writing, roughly. Only the order
# matters here: it decides which word of a question is the odd one.
COMMON = "оеаинтсрвлкмдпуяыьгзбчйхжшюцщэфъ" + "etaoinshrdlcumwfgypbvkjxqz"


def words(text: str) -> list[str]:
    return WORD.findall(text.lower())


def letter_value(character: str) -> int:
    for alphabet in ALPHABETS:
        position = alphabet.find(character)
        if position >= 0:
            return position + 1
    return 0


def digest_seed(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode()).digest(), "big")


def rarity(word: str) -> float:
    """How unusual a word's letters are, without carrying a dictionary."""
    scores = [COMMON.find(letter) for letter in word if COMMON.find(letter) >= 0]
    return sum(scores) / len(scores) if scores else 0.0
