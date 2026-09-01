from heidr import radio
from heidr.contracts import Key, Material
from heidr.registry import world

# The international shortwave broadcast bands, by metre band. Which of them
# carries anything depends on the hour and the ionosphere, so the draw picks
# one and the scan then decides where inside it to stop.
BANDS = (
    "5.85-6.20",  # 49 m, reliable after dark
    "7.20-7.45",  # 41 m
    "9.40-9.90",  # 31 m, the workhorse
    "11.60-12.10",  # 25 m, daytime
    "15.10-15.80",  # 19 m, daytime
)

available = radio.available


@world(
    "sw_voice",
    needs=("sdr", "stt"),
    visual="waterfall",
    defaults={
        "band": list(BANDS),
        "sweep": "random",
        "stops": 3,
        "dwell_s": 20,
        "mode": "am",
        "rate": 16000,
        "input_rate": "24k",
        "bins": 64,
        "tuned": True,
        "scan_step": "5k",
        "scan_s": 6,
        "scan_margin": 6.0,
        "scan_separation": 10000,
        "gain": "",
        # Empty on a receiver whose driver reaches shortwave by itself, which is
        # the case for the RTL-SDR Blog V4. Set it to direct2 on a dongle that
        # needs the input sampled directly.
        "direct": "",
    },
)
def run(ctx, key: Key) -> Material:
    said, stops = radio.gather(ctx, key)
    kept = radio.matching(said, key.anchors)

    return Material(
        text=" / ".join(kept),
        numbers=tuple(int(frequency) for frequency in stops[:4]),
        source="shortwave",
        extra={"stops": len(stops), "phrases": len(said), "kept": len(kept)},
    )
