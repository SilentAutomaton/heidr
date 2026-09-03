from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import blank, lines, stamp

# Raw bits raining, most of them cancelling out, and what is left condensing
# into a digest. Shown while sdr_noise is sampling an empty frequency, which is
# the oldest use of the radio here and the one where nothing is being listened
# to at all.
#
# The rule drawn is Von Neumann's, which is what the module really does: bits
# arrive in pairs, a pair of two different bits keeps the first of them, and a
# pair of two the same is thrown away. A biased source becomes an unbiased one
# and most of the samples are lost, which is the whole bargain.
HEX = "0123456789abcdef"
FALL = 0.55
SIEVE_AT = 0.62
PAIRS = 4


def bit(column: int, step: int) -> int:
    mixed = (column * 73856093) ^ (step * 19349663)
    # Deliberately biased, because the noise floor of a receiver is: about three
    # ones to five zeroes, which is what makes the debiasing worth doing.
    return 1 if mixed % 8 < 3 else 0


def paint(frame: Frame) -> list[str]:
    grid = blank(frame.width, frame.height)
    sieve = max(1, int(frame.height * SIEVE_AT))
    for column in range(frame.width):
        grid[sieve][column] = frame.ramp[max(1, len(frame.ramp) // 3)]

    kept = []
    for column in range(0, frame.width, 3):
        offset = frame.tick + column
        for row in range(sieve):
            step = int((offset - row) * FALL)
            first, second = bit(column, step), bit(column, step + 1)
            grid[row][column] = str(first)
            if column + 1 < frame.width:
                grid[row][column + 1] = str(second)

        # What the sieve lets through. A column offers several pairs, because
        # most of them are thrown away and a digest made of two bits would be a
        # poor picture of a whitened one.
        step = int(offset * FALL)
        for extra in range(PAIRS):
            first, second = bit(column, step + 2 * extra), bit(column, step + 2 * extra + 1)
            if first == second:
                continue
            kept.append(first)
            if extra == 0:
                landed = sieve + 1 + (offset // 2) % max(1, frame.height - sieve - 2)
                if landed < frame.height:
                    grid[landed][column] = str(first)

    if len(kept) >= 4:
        digest = "".join(
            HEX[sum(nibble[place] << place for place in range(4))]
            for nibble in [kept[at : at + 4] for at in range(0, len(kept) - 3, 4)]
        )
        stamp(grid, [digest], max(0, (frame.width - len(digest)) // 2), frame.height - 1)
    return lines(grid)


for level in ("ascii", "blocks", "braille"):
    animation("bits", glyphs=level, fps=10)(paint)
