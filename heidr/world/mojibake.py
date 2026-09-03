import os
import re

from heidr.contracts import Key, Material
from heidr.registry import world

ENCODINGS = ("cp1251", "koi8-r", "cp1252", "shift_jis", "cp866")
RUN = re.compile(r"[^\W\d_]{3,}", re.UNICODE)
BYTES = 4096


def readable_runs(data: bytes, encoding: str) -> list[str]:
    return RUN.findall(data.decode(encoding, errors="replace"))


@world("mojibake", visual="codepage", defaults={"encodings": list(ENCODINGS), "bytes": BYTES})
def run(ctx, key: Key) -> Material:
    encodings = ctx.settings["encodings"]
    encoding = encodings[key.seed % len(encodings)]
    data = os.urandom(int(ctx.settings["bytes"]))

    runs = readable_runs(data, encoding)
    ctx.emit("stage", f"mojibake {encoding}: {len(runs)} runs")

    return Material(
        text=" ".join(runs),
        numbers=tuple(len(run) for run in runs[:8]),
        source=f"urandom/{encoding}",
        extra={"encoding": encoding, "runs": len(runs)},
    )
