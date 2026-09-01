import math
import time
from datetime import datetime, timezone

from heidr.contracts import Key
from heidr.question.words import digest_seed
from heidr.registry import question

# The classical order, and the one that makes the scheme work: the ruler of an
# hour is the next planet along this chain, and the ruler of a day is the ruler
# of its first hour. Follow it for twenty four hours and you land on the right
# planet for the next day, which is why the week runs Sun, Moon, Mars, Mercury,
# Jupiter, Venus, Saturn.
CHALDEAN = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")
DAY_RULERS = ("Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun")
ZENITH = math.radians(90.833)


def solar_events(day: datetime, latitude: float, longitude: float) -> tuple[float, float]:
    """Sunrise and sunset as hours UTC, by the usual sunrise equation."""
    day_number = day.timetuple().tm_yday
    rising, setting = (
        _event(day_number, latitude, longitude, rising) for rising in (True, False)
    )
    return rising, setting


def _event(day_number: int, latitude: float, longitude: float, rising: bool) -> float:
    longitude_hour = longitude / 15
    approximate = day_number + ((6 if rising else 18) - longitude_hour) / 24

    mean_anomaly = 0.9856 * approximate - 3.289
    true_longitude = (
        mean_anomaly
        + 1.916 * math.sin(math.radians(mean_anomaly))
        + 0.020 * math.sin(math.radians(2 * mean_anomaly))
        + 282.634
    ) % 360

    right_ascension = math.degrees(
        math.atan(0.91764 * math.tan(math.radians(true_longitude)))
    ) % 360
    quadrant = (true_longitude // 90) * 90
    right_ascension = (right_ascension - (right_ascension // 90) * 90 + quadrant) / 15

    declination_sin = 0.39782 * math.sin(math.radians(true_longitude))
    declination_cos = math.cos(math.asin(declination_sin))

    hour_cos = (
        math.cos(ZENITH) - declination_sin * math.sin(math.radians(latitude))
    ) / (declination_cos * math.cos(math.radians(latitude)))
    if abs(hour_cos) > 1:
        # Polar day or polar night: the sun does not cross the horizon at all.
        return 6.0 if rising else 18.0

    hour_angle = math.degrees(math.acos(hour_cos))
    hour_angle = (360 - hour_angle if rising else hour_angle) / 15

    local = hour_angle + right_ascension - 0.06571 * approximate - 6.622
    return (local - longitude_hour) % 24


def ruler(moment: float, latitude: float, longitude: float) -> tuple[str, int, bool]:
    """Which planet rules the hour this moment falls in.

    Day and night are divided into twelve hours each, so an hour of daylight in
    June is far longer than one in December. That unevenness is the whole idea.
    """
    when = datetime.fromtimestamp(moment, tz=timezone.utc)
    rising, setting = solar_events(when, latitude, longitude)
    now = when.hour + when.minute / 60 + when.second / 3600

    daylight = rising <= now < setting
    if daylight:
        length = (setting - rising) / 12
        index = int((now - rising) / length)
    else:
        night = (24 - setting + rising) % 24 or 24
        length = night / 12
        past_sunset = (now - setting) % 24
        index = int(past_sunset / length)

    weekday = (when.weekday() + 1) % 7
    first = CHALDEAN.index(DAY_RULERS[weekday])
    hours_in = index if daylight else index + 12
    return CHALDEAN[(first + hours_in) % 7], min(index + 1, 12), daylight


def available(ctx) -> bool:
    return bool(ctx.settings.get("latitude")) or bool(ctx.settings.get("longitude"))


@question("planetary", defaults={"latitude": 0.0, "longitude": 0.0})
def run(ctx, text: str) -> Key:
    planet, hour, daylight = ruler(
        time.time(), float(ctx.settings["latitude"]), float(ctx.settings["longitude"])
    )
    part = "day" if daylight else "night"
    return Key(seed=digest_seed(f"{planet}{hour}{part}{text}"), anchors=(planet.lower(),))
