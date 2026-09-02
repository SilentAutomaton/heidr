import base64
import sys

# OSC 52 asks the terminal itself to hold the text, which means it works the
# same locally and at the far end of an ssh session, and needs no clipboard
# program installed. Terminals cap what they will take; this is well under the
# usual limit and long enough for any answer this program produces.
LIMIT = 32000


def sequence(text: str) -> str:
    payload = base64.b64encode(text[:LIMIT].encode("utf-8")).decode("ascii")
    return f"\x1b]52;c;{payload}\x07"


def copy(text: str) -> bool:
    """Hand the text to the terminal's clipboard. False when there is none."""
    if not text.strip():
        return False
    sys.__stdout__.write(sequence(text))
    sys.__stdout__.flush()
    return True
