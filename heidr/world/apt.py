import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

# The three remaining NOAA birds still sending pictures in the clear, the way
# weather satellites have since 1960.
SATELLITES = {"noaa-15": 137_620_000, "noaa-18": 137_912_500, "noaa-19": 137_100_000}
DECODER = "noaa-apt"
RATE = 11025


def available(ctx) -> bool:
    return ctx.has("sdr") and shutil.which(DECODER) is not None


def record(frequency: int, seconds: int, folder: Path, gain: str = "") -> Path:
    """Take the downlink as plain audio; the picture is inside it."""
    path = folder / "pass.wav"
    command = [
        "rtl_fm", "-f", str(frequency), "-M", "fm", "-s", "60k", "-r", str(RATE),
    ]
    if gain:
        command += ["-g", gain]
    command += ["-"]

    with path.open("wb") as sink:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + seconds
        try:
            while time.monotonic() < deadline:
                block = process.stdout.read(RATE * 2)
                if not block:
                    break
                sink.write(block)
        finally:
            process.terminate()
            process.wait(timeout=5)
    return path


def decode(audio: Path, image: Path) -> bool:
    finished = subprocess.run(
        [DECODER, str(audio), "-o", str(image)], capture_output=True, timeout=300
    )
    return finished.returncode == 0 and image.is_file()


@world(
    "apt",
    visual="dish",
    needs=("sdr",),
    defaults={
        "satellite": "noaa-19",
        "seconds": 600,
        "gain": "",
        "keep_in": "~/.local/share/heidr/apt",
    },
)
def run(ctx, key: Key) -> Material:
    settings = ctx.settings
    name = settings["satellite"]
    if name not in SATELLITES:
        raise Unavailable(
            f"No satellite named {name!r}. Set modules.apt.satellite to one of: "
            f"{', '.join(sorted(SATELLITES))}."
        )

    keep = Path(str(settings["keep_in"])).expanduser()
    keep.mkdir(parents=True, exist_ok=True)
    image = keep / f"{name}-{int(time.time())}.png"

    ctx.emit("stage", f"{name} at {SATELLITES[name] / 1e6:.4f} MHz")
    with tempfile.TemporaryDirectory() as folder:
        audio = record(SATELLITES[name], int(settings["seconds"]), Path(folder), str(settings["gain"]))
        if not audio.stat().st_size:
            raise Unavailable(
                "The receiver gave nothing on the satellite frequency. Either "
                "another program is holding the dongle, or the pass is over. "
                "Start a draw while the satellite is above the horizon."
            )
        if not decode(audio, image):
            raise Unavailable(
                f"{DECODER} could not find a picture in the recording. There was "
                "probably no satellite overhead. Check a pass prediction and "
                "draw again during one."
            )

    ctx.emit("stage", f"decoded {image.name}")
    return Material(
        text=str(image),
        numbers=(SATELLITES[name], image.stat().st_size),
        source=f"apt/{name}",
        extra={"image": str(image), "satellite": name, "frequency": SATELLITES[name]},
    )
