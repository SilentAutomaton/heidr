from heidr import radio
from heidr.contracts import Key, Material
from heidr.registry import world

available = radio.available


@world(
    "fm_voice",
    needs=("sdr", "stt"),
    visual="waterfall",
    defaults={
        "band": "88.0-108.0",
        "sweep": "random",
        "stops": 6,
        "dwell_s": 4,
        "mode": "wbfm",
        "rate": 32000,
        "bins": 64,
        "tuned": True,
        "scan_step": "100k",
        "scan_s": 4,
        "gain": "",
        "input_rate": "",
    },
)
def run(ctx, key: Key) -> Material:
    said, stops = radio.gather(ctx, key)
    kept = radio.matching(said, key.anchors)

    return Material(
        text=" / ".join(kept),
        numbers=tuple(int(frequency) for frequency in stops[:4]),
        source="fm",
        extra={"stops": len(stops), "phrases": len(said), "kept": len(kept)},
    )
