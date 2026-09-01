from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines, stamp

# A chain of blocks moving right to left, each carrying a run of hexadecimal.
# Shown while the block chain is being read.
HEX = "0123456789abcdef"
BLOCK = ("+------+", "|      |", "+------+")
GAP = 3
SPEED = 1


def block_art(seed: int) -> list[str]:
    digits = "".join(HEX[(seed * 7 + index * 13) % 16] for index in range(6))
    return [BLOCK[0], f"|{digits}|", BLOCK[2]]


class ChainBlocks(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        stride = len(BLOCK[0]) + GAP
        top = max(0, (frame.height - len(BLOCK)) // 2)
        offset = (frame.tick * SPEED) % stride

        index = 0
        left = -offset
        while left < frame.width:
            stamp(grid, block_art(index + frame.tick // stride), left, top)
            # The links between them, drawn on the middle row.
            for bridge in range(len(BLOCK[0]), stride):
                x = left + bridge
                if 0 <= x < frame.width and 0 <= top + 1 < frame.height:
                    grid[top + 1][x] = "-"
            left += stride
            index += 1
        return lines(grid)


@animation("chain", glyphs="ascii", fps=6)
class PlainChain(ChainBlocks):
    ramp = ASCII


@animation("chain", glyphs="blocks", fps=6)
class BlockChain(ChainBlocks):
    ramp = BLOCKS
