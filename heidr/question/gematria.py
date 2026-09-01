from heidr.contracts import Key
from heidr.registry import question

ALPHABETS = (
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "abcdefghijklmnopqrstuvwxyz",
)


def letter_value(character: str) -> int:
    for alphabet in ALPHABETS:
        position = alphabet.find(character)
        if position >= 0:
            return position + 1
    return 0


@question("gematria", visual="hexlib")
def run(ctx, text: str) -> Key:
    total = sum(letter_value(character) for character in text.lower())
    words = sorted(text.split(), key=len, reverse=True)
    return Key(seed=total, anchors=tuple(words[:2]))
