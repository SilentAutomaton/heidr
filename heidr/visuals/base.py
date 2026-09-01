from textual.widgets import Static

# From flattest to richest. A visualisation declares the poorest terminal it can
# live on, and the registry hands back the best one this terminal can draw.
ASCII = " .:-=+*#%@"
BLOCKS = " ▁▂▃▄▅▆▇█"
BRAILLE = " ⣀⣄⣤⣦⣶⣷⣿"


def resample(bars: list[float], width: int) -> list[float]:
    """Fit any number of bars into the columns actually on screen."""
    if width <= 0 or not bars:
        return []
    if len(bars) == width:
        return list(bars)

    out = []
    for column in range(width):
        start = column * len(bars) // width
        end = max(start + 1, (column + 1) * len(bars) // width)
        chunk = bars[start:end]
        out.append(sum(chunk) / len(chunk))
    return out


def row(bars: list[float], ramp: str) -> str:
    top = len(ramp) - 1
    return "".join(ramp[min(top, max(0, round(value * top)))] for value in bars)


class Visualisation(Static):
    """A widget fed by one kind of event and nothing else.

    Geometry is recomputed on every render from the current size, so the
    terminal can be resized mid capture and the capture never notices.
    """

    ramp = ASCII

    def feed(self, payload) -> None:
        raise NotImplementedError
