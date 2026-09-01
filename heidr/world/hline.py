import statistics

from heidr import radio
from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

# Neutral hydrogen radiates at this frequency and nowhere else. It is the most
# common substance in the universe, and this is the line the Milky Way is
# mapped with.
REST_HZ = 1_420_405_751
LIGHT_MS = 299_792_458


def available(ctx) -> bool:
    return ctx.has("sdr")


def band_around(centre_hz: int, span_hz: int) -> str:
    return f"{centre_hz - span_hz // 2}:{centre_hz + span_hz // 2}"


def excess(bins: list[tuple[int, float]]) -> tuple[int, float, float]:
    """The loudest bin, how far it stands above the baseline, and that baseline.

    The sky here is not a station but a broad rise over the noise, so the
    baseline is the median of the whole sweep and the signal is what pokes out
    of it.
    """
    if not bins:
        return 0, 0.0, 0.0
    floor = statistics.median(power for _hertz, power in bins)
    hertz, power = max(bins, key=lambda pair: pair[1])
    return hertz, power - floor, floor


def radial_velocity(hertz: int) -> float:
    """Metres per second, positive away from us.

    A cloud moving away stretches the wave, so the line arrives below its rest
    frequency. This is the whole of radio astronomy's arithmetic and it fits on
    one line.
    """
    return LIGHT_MS * (REST_HZ - hertz) / REST_HZ


@world(
    "hline",
    needs=("sdr",),
    visual="dish",
    defaults={"span_hz": 2_000_000, "step": "10k", "seconds": 30, "gain": "", "min_excess_db": 1.0},
)
def run(ctx, key: Key) -> Material:
    settings = ctx.settings
    csv = radio.scan(
        band_around(REST_HZ, int(settings["span_hz"])),
        settings["step"],
        int(settings["seconds"]),
        gain=str(settings["gain"]),
    )
    bins = radio.power_bins(csv)
    if not bins:
        raise Unavailable(
            "The receiver gave nothing at 1420 MHz. Either another program is "
            "holding the dongle or rtl_power cannot open it. Close the other "
            "program, then draw again."
        )

    hertz, above, floor = excess(bins)
    velocity = radial_velocity(hertz)
    offset = hertz - REST_HZ

    ctx.emit("stage", f"hydrogen {above:.1f} dB above the floor, {velocity / 1000:+.1f} km/s")
    return Material(
        text=f"{velocity / 1000:+.1f} km/s at {above:.1f} dB above the noise",
        numbers=(abs(offset), int(abs(velocity)), int(above * 10)),
        source="hydrogen",
        extra={
            "hertz": hertz,
            "offset_hz": offset,
            "velocity_ms": velocity,
            "excess_db": above,
            "floor_db": floor,
            # Below this the sweep is honest noise and says so.
            "detected": above >= float(settings["min_excess_db"]),
        },
    )
