import os
import random

from rich.text import Text

from heidr.strings import BANNER_ROWS, NAME

# The one colour in the program. It is the same signal orange the plan page
# uses for the slashes, stepped down to whatever the terminal really has.
TRUECOLOR = "#e08b1e"
INDEXED = "color(214)"
POOR = "yellow"
SLASHES = "//"
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789#@%&$?!"
MOTION_GLYPHS = ("blocks", "braille")


def accent(colours: int) -> str:
    if colours >= 16777216:
        return TRUECOLOR
    if colours >= 256:
        return INDEXED
    return POOR


def wordmark(glyphs: str, colours: int) -> Text:
    """The sign, white, with the slashes in the accent colour and nothing else."""
    colour = accent(colours)
    if glyphs == "ascii":
        mark = Text(NAME)
        mark.stylize(colour, NAME.index(SLASHES), NAME.index(SLASHES) + len(SLASHES))
        return mark

    mark = Text()
    for number, (left, middle, right) in enumerate(BANNER_ROWS):
        if number:
            mark.append("\n")
        mark.append(left)
        mark.append(middle, colour)
        mark.append(right)
    return mark


def can_garble(glyphs: str, settings) -> bool:
    """Three conditions, all checked before the lot is drawn.

    A console without block glyphs turns random Unicode into empty boxes, a
    `dumb` terminal has no business animating anything, and flickering text is
    a thing some people cannot look at, so it can be switched off.
    """
    return (
        glyphs in MOTION_GLYPHS
        and os.environ.get("TERM", "") != "dumb"
        and bool(settings.get("ui.motion", True))
    )


def garble(line: str, tick: int) -> str:
    """The letters change, the shape of the words does not."""
    rng = random.Random(tick)
    return "".join(" " if character == " " else rng.choice(ALPHABET) for character in line)
