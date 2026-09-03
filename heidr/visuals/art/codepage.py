from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import blank, lines

# A page of text re-rendered through one wrong encoding after another, the
# glyphs mutating in place while the shape of the paragraph holds. Shown while
# the mojibake module is at work, which reads random bytes through a code page
# they were never written in.
#
# Which is why the letters here are the ones a wrong code page actually
# produces: the accented Latin of a Cyrillic page read as Western European, and
# the box-drawing characters of a DOS page read as anything else.
WRONG = "ÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ¡¢£¤¥¦§¨©ª«¬®¯°±²³´µ¶·¸¹º»¼½¾¿"
BOXES = "─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬▀▄█▌▐░▒▓"
PAGE_EVERY = 7
MARGIN = 6
GAPS = 0.14


def hashed(x: int, y: int, page: int) -> int:
    return ((x * 73856093) ^ (y * 19349663) ^ (page * 83492791)) % 100003


def paint(frame: Frame) -> list[str]:
    grid = blank(frame.width, frame.height)
    # Every few frames the whole page is read through a different code page, so
    # the glyphs change while the words keep their length.
    page = frame.tick // PAGE_EVERY
    alphabet = WRONG if page % 2 else WRONG + BOXES
    top, bottom = 2, max(3, frame.height - 2)

    for row in range(top, bottom):
        # The line lengths belong to the paragraph and never change; only what
        # fills them does. A wrong code page does not move the spaces.
        length = frame.width - 2 * MARGIN - hashed(0, row, 0) % 9
        for column in range(MARGIN, min(frame.width, MARGIN + length)):
            if hashed(column, row, 0) % 100 < GAPS * 100:
                continue
            grid[row][column] = alphabet[hashed(column, row, page) % len(alphabet)]
    return lines(grid)


for level in ("blocks", "braille"):
    animation("codepage", glyphs=level, fps=8)(paint)
