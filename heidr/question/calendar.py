import time
from datetime import date, datetime, timezone

from heidr.contracts import Key
from heidr.question.words import digest_seed
from heidr.registry import question

# Discordian, after ddate, which lived in util-linux for two decades before
# being thrown out for frivolity. https://github.com/bo0ts/ddate
SEASONS = ("Chaos", "Discord", "Confusion", "Bureaucracy", "The Aftermath")
DISCORDIAN_DAYS = ("Sweetmorn", "Boomtime", "Pungenday", "Prickle-Prickle", "Setting Orange")

# French Republican, from the calendar of 1793: twelve months of thirty days,
# named after what the fields were doing.
REPUBLICAN_MONTHS = (
    "Vendémiaire", "Brumaire", "Frimaire", "Nivôse", "Pluviôse", "Ventôse",
    "Germinal", "Floréal", "Prairial", "Messidor", "Thermidor", "Fructidor",
)
REPUBLICAN_EPOCH = date(1792, 9, 22)

# The Maya long count simply counts days from a fixed morning. 584283 is the
# Goodman-Martinez-Thompson correlation in Julian days; 1721425 converts that to
# the proleptic Gregorian ordinal Python counts in.
LONG_COUNT_EPOCH = 1721425 - 584283


def discordian(when: date) -> str:
    day_of_year = when.timetuple().tm_yday
    leap = when.year % 4 == 0 and (when.year % 100 != 0 or when.year % 400 == 0)
    if leap and day_of_year == 60:
        return f"St Tib's Day, {when.year + 1166} YOLD"
    if leap and day_of_year > 60:
        day_of_year -= 1

    season, day = divmod(day_of_year - 1, 73)
    weekday = DISCORDIAN_DAYS[(day_of_year - 1) % 5]
    return f"{weekday}, {day + 1} {SEASONS[season]} {when.year + 1166} YOLD"


def republican_leap(year: int) -> bool:
    # Romme's arithmetic rule. The calendar as decreed used the true autumn
    # equinox instead, which needs an ephemeris to follow; this is the version
    # everyone who implements it in software actually uses.
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def republican(when: date) -> str:
    days = (when - REPUBLICAN_EPOCH).days
    if days < 0:
        return "before the Republic"

    year = 1
    while True:
        length = 366 if republican_leap(year) else 365
        if days < length:
            break
        days -= length
        year += 1

    month, day = divmod(days, 30)
    if month >= 12:
        return f"sansculottide {day + 1}, year {year}"
    return f"{day + 1} {REPUBLICAN_MONTHS[month]}, year {year}"


def long_count(when: date) -> str:
    days = when.toordinal() + LONG_COUNT_EPOCH
    baktun, rest = divmod(days, 144000)
    katun, rest = divmod(rest, 7200)
    tun, rest = divmod(rest, 360)
    winal, kin = divmod(rest, 20)
    return f"{baktun}.{katun}.{tun}.{winal}.{kin}"


CALENDARS = {"discordian": discordian, "republican": republican, "long_count": long_count}


@question("calendar", visual="moon", defaults={"which": "rotate"})
def run(ctx, text: str) -> Key:
    when = datetime.fromtimestamp(time.time(), tz=timezone.utc).date()
    names = sorted(CALENDARS)
    wanted = ctx.settings["which"]
    if wanted not in CALENDARS:
        # Rotating by the day means a question asked tomorrow is dated in
        # another reckoning, without anyone choosing which.
        wanted = names[when.toordinal() % len(names)]

    stamped = CALENDARS[wanted](when)
    return Key(seed=digest_seed(f"{wanted}{stamped}{text}"), anchors=(wanted,))
