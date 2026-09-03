"""A colour for each animation.

The animation is a background: the panel and the wordmark stand on top of it. So
every colour here is held below the panel text in lightness and kept at moderate
saturation. A pure primary vibrates on a dark ground and reads as a screensaver,
and a large red field reads as an error, so neither is in the table.

Each entry is a hex value and the xterm index nearest it. Below 256 colours
there is no tint at all: the bare console theme is white on black with reversed
video, and colouring it would only spoil that.
"""

import random

# The sign and the answer keep the accent orange, and nothing else may take it.
KEEPS_ACCENT = ("seeress", "reveal", "chainblocks")

TINTS: dict[str, tuple[tuple[str, int], ...]] = {
    # Behind the main screen
    "plasma": (("#a06cd5", 140), ("#7f8fd6", 104)),
    "life": (("#5cc98c", 78), ("#d3a24c", 179)),
    "rain": (("#43c76a", 77), ("#5fc9d0", 80)),
    "starfield": (("#a9c6f0", 152), ("#e0cf9a", 223)),
    "moon": (("#c2ccd8", 252), ("#d8cdb4", 187)),
    "runes": (("#c8a45c", 179), ("#8fae86", 108)),
    "rings": (("#5fb0c8", 74), ("#9fb3c4", 110)),
    "ants": (("#7f9bd0", 110), ("#c07a55", 173)),
    # Instruments
    "waterfall": (("#4fc0c8", 73),),
    "scope": (("#4fc97a", 77), ("#dba55a", 179)),
    "radar": (("#46c77e", 77),),
    "seismo": (("#93a4b4", 145),),
    "dish": (("#8db6d6", 110), ("#c8d2dc", 252)),
    "globe": (("#4f9fc0", 74), ("#6fbf9f", 79)),
    "relay": (("#8fa8c8", 110), ("#79c9b0", 79)),
    "scanlines": (("#9a7ac0", 140), ("#5fb8c8", 74)),
    "bits": (("#c3ccd8", 252), ("#7fbf8f", 108)),
    # The question, read apart
    "hexlib": (("#d3c49f", 180), ("#a89b84", 144)),
    "sieve": (("#c8b06a", 179),),
    "zipf": (("#8fa3b8", 110),),
    "initials": (("#a9b6c4", 146),),
    "abacus": (("#b8785a", 173), ("#c5a253", 179)),
    "codepage": (("#bf7bb0", 176), ("#9fbf6f", 149)),
    # The mechanism
    "cog": (("#3fb8af", 73), ("#c9a227", 178), ("#8fa3b8", 110)),
    "mirror": (("#b4c0cc", 251),),
    "lattice": (("#7f8fd6", 104),),
    "vapour": (("#a887c8", 140), ("#8fbf9f", 108)),
    # The reading
    "chain": (("#c0824a", 173), ("#7691c0", 110)),
    "hexagram": (("#c8613f", 166), ("#79b8a0", 79)),
    "cards": (("#c9a227", 178), ("#9a7ac0", 140)),
    "scissors": (("#b9b3a6", 145),),
    # The slogan grey from the brand. Silence should be quiet.
    "hush": (("#7c8895", 102),),
}


def tint(name: str, colours: int, rng: random.Random) -> str:
    """One colour for this animation, or nothing at all.

    Several are offered and one is drawn, in the same spirit as the rest of the
    program: the same animation is not the same colour twice running.
    """
    if colours < 256 or name in KEEPS_ACCENT:
        return ""
    offered = TINTS.get(name)
    if not offered:
        return ""
    return step_down(rng.choice(offered), colours)


def step_down(colour: tuple[str, int], colours: int) -> str:
    exact, index = colour
    return exact if colours >= 16777216 else f"color({index})"
