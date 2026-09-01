import time
from datetime import datetime, timezone

from heidr.contracts import Key
from heidr.question.words import digest_seed
from heidr.registry import question

# A known new moon, and the length of the cycle between them.
NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc).timestamp()
SYNODIC_DAYS = 29.530588853
PHASES = (
    "new moon",
    "waxing crescent",
    "first quarter",
    "waxing gibbous",
    "full moon",
    "waning gibbous",
    "last quarter",
    "waning crescent",
)


def moon_age(moment: float) -> float:
    """Days since the last new moon."""
    return ((moment - NEW_MOON) / 86400) % SYNODIC_DAYS


def phase_name(age_days: float) -> str:
    return PHASES[int(age_days / SYNODIC_DAYS * 8 + 0.5) % 8]


@question("moment", visual="moon")
def run(ctx, text: str) -> Key:
    # The question is not read at all. What is asked matters less than when.
    now = time.time()
    phase = phase_name(moon_age(now))
    return Key(seed=digest_seed(f"{int(now)}{phase}"), anchors=(phase,))
