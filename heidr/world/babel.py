import hashlib
from dataclasses import dataclass

from heidr.contracts import Key, Material
from heidr.registry import world

# The Library of Babel is not a store of pages; it is a bijection. An address is
# mapped to text by an invertible function, and the same function run backwards
# turns any text into the address where it has always been. The construction is
# Jonathan Basile's, described at
# https://github.com/librarianofbabel/libraryofbabel.info-algo — an invertible
# affine step followed by a diffusion pass. The constants here are ours, so
# these pages are not the pages on his site.

ALPHABET = "abcdefghijklmnopqrstuvwxyz ,."
DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)
PAGE = 3200

WALLS, SHELVES, VOLUMES, PAGES = 4, 5, 32, 410
MODULUS = BASE**PAGE

def spread(label: bytes) -> int:
    """A page-wide constant whose digits carry no pattern of their own.

    A short multiplier would leave almost every digit of a small address
    untouched, so neighbouring pages would read alike. A regular one, built from
    a formula, would stamp its own period onto the text. Hashing a counter gives
    a constant that is both full width and featureless, and it is written down
    here rather than drawn, so every copy of the library is the same library.
    """
    digits: list[int] = []
    block = 0
    while len(digits) < PAGE:
        stream = hashlib.sha512(label + block.to_bytes(4, "big")).digest()
        digits.extend(byte % BASE for byte in stream)
        block += 1

    number = 0
    for digit in digits[:PAGE]:
        number = number * BASE + digit
    # Coprime with the modulus, which for a power of 29 only means the value is
    # not a multiple of 29.
    return number + 1 if number % BASE == 0 else number


MULTIPLIER = spread(b"heidr/babel/multiplier")
INCREMENT = spread(b"heidr/babel/increment")
INVERSE = pow(MULTIPLIER, -1, MODULUS)


@dataclass(frozen=True)
class Address:
    hexagon: int
    wall: int
    shelf: int
    volume: int
    page: int

    @property
    def name(self) -> str:
        return base36(self.hexagon)

    def __str__(self) -> str:
        return f"{self.name}.{self.wall}.{self.shelf}.{self.volume}.{self.page}"

    def short(self) -> str:
        name = self.name
        head = name if len(name) <= 12 else f"{name[:8]}…{name[-4:]}"
        return f"{head}.{self.wall}.{self.shelf}.{self.volume}.{self.page}"


def base36(number: int) -> str:
    if number == 0:
        return "0"
    letters = []
    while number:
        number, digit = divmod(number, 36)
        letters.append(DIGITS[digit])
    return "".join(reversed(letters))


def encode(location: int) -> str:
    number = (MULTIPLIER * location + INCREMENT) % MODULUS
    letters = []
    for _ in range(PAGE):
        number, digit = divmod(number, BASE)
        letters.append(ALPHABET[digit])
    return "".join(letters)


def decode(text: str) -> int:
    number = 0
    for character in reversed(text):
        number = number * BASE + ALPHABET.index(character)
    return ((number - INCREMENT) * INVERSE) % MODULUS


def to_address(location: int) -> Address:
    location, page = divmod(location, PAGES)
    location, volume = divmod(location, VOLUMES)
    location, shelf = divmod(location, SHELVES)
    hexagon, wall = divmod(location, WALLS)
    return Address(hexagon, wall + 1, shelf + 1, volume + 1, page + 1)


def clean(word: str) -> str:
    return "".join(character for character in word.lower() if character in ALPHABET)


def page_beginning_with(word: str) -> str:
    return (word + " " * PAGE)[:PAGE]


@world("babel", defaults={"excerpt": 240})
def run(ctx, key: Key) -> Material:
    anchor = clean(key.anchors[0]) if key.anchors else ""
    if anchor:
        # Reverse lookup: the word is already on some page, and this is where.
        text = page_beginning_with(anchor)
        location = decode(text)
    else:
        location = key.seed % MODULUS
        text = encode(location)

    address = to_address(location)
    ctx.emit("stage", f"babel {address.short()}")

    excerpt = text[: int(ctx.settings["excerpt"])].strip()
    return Material(
        text=excerpt,
        numbers=(address.wall, address.shelf, address.volume, address.page),
        source="babel",
        extra={"address": str(address), "anchor": anchor},
    )
