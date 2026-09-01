from heidr import radio
from heidr.contracts import Key, Material
from heidr.registry import world

# Medium wave: the oldest broadcast band still in use, and the one where a
# station heard at night may be a thousand kilometres away. Channels sit on a
# 9 kHz grid in most of the world and 10 kHz in the Americas.
BAND = "0.531-1.602"

available = radio.available


@world(
    "mw_voice",
    needs=("sdr", "stt"),
    visual="waterfall",
    defaults={
        "band": BAND,
        "sweep": "random",
        "stops": 3,
        "dwell_s": 20,
        "mode": "am",
        "rate": 16000,
        "input_rate": "24k",
        "bins": 64,
        "tuned": True,
        "scan_step": "9k",
        "scan_s": 8,
        "scan_margin": 6.0,
        "scan_separation": 9000,
        "gain": "",
        "direct": "",
    },
)
def run(ctx, key: Key) -> Material:
    said, stops = radio.gather(ctx, key)
    kept = radio.matching(said, key.anchors)

    return Material(
        text=" / ".join(kept),
        numbers=tuple(int(frequency) for frequency in stops[:4]),
        source="mediumwave",
        extra={"stops": len(stops), "phrases": len(said), "kept": len(kept)},
    )
