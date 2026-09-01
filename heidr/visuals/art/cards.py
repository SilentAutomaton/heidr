from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, blank, centre, lines

# A card turning over. The width of the card shrinks to nothing and opens out
# again, which is how a flip looks when you only have columns to work with.
HEIGHT = 7
WIDEST = 11
BACK = "/"
FACE = " "
TURN = 12


def card(width: int, face_up: bool) -> list[str]:
    inner = max(0, width - 2)
    fill = FACE if face_up else BACK
    top = "+" + "-" * inner + "+"
    middle = "|" + fill * inner + "|"
    return [top] + [middle] * (HEIGHT - 2) + [top]


class Cards(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        place = frame.tick % TURN
        # Half the turn closing, half opening, and the face changes at the edge.
        half = TURN // 2
        closing = place < half
        step = place if closing else place - half
        width = WIDEST - step * (WIDEST - 2) // half if closing else 2 + step * (WIDEST - 2) // half
        return lines(centre(blank(frame.width, frame.height), card(max(2, width), not closing)))


@animation("cards", glyphs="ascii", fps=6)
class PlainCards(Cards):
    ramp = ASCII


@animation("cards", glyphs="blocks", fps=6)
class BlockCards(Cards):
    ramp = BLOCKS
