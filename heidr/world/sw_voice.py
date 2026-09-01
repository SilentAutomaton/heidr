from heidr import radio
from heidr.contracts import Key, Material
from heidr.registry import world

# Same sweep as fm_voice, pointed at a shortwave broadcast band in AM. Up here
# the band is mostly noise, the voices are distant and half buried, and the
# recogniser hallucinates freely. That is the point.
available = radio.available


@world(
    "sw_voice",
    needs=("sdr", "stt"),
    visual="waterfall",
    defaults={
        "band": "3.9-4.0",
        "sweep": "bounce",
        "stops": 6,
        "dwell_s": 6,
        "mode": "am",
        "rate": 16000,
        "bins": 64,
        "tuned": False,
        "scan_step": "100k",
        "scan_s": 4,
        "gain": "",
        "input_rate": "12k",
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
