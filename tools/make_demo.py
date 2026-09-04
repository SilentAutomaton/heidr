"""Record the animations as looping pictures for the README.

    python tools/make_demo.py            every demo in the table
    python tools/make_demo.py plasma     one of them

Nothing here records a screen. The interface is run headless, the frame number
is set by hand rather than left to a timer, and each frame is exported as an
SVG of the real widget tree. Two runs give the same bytes, which is what makes
a loop close without a seam and what makes this worth doing at all.

Needs `resvg` (or `rsvg-convert`) and `ffmpeg` on the path. Neither is a
dependency of the program: this is a tool for whoever rebuilds the pictures.
"""

import asyncio
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from heidr import config  # noqa: E402
from heidr.app import HeidrApp  # noqa: E402
from heidr.capabilities import Terminal  # noqa: E402
from heidr.visuals.canvas import Canvas  # noqa: E402

OUT = ROOT / "docs" / "demo"
SIZE = (96, 26)
SEED = 1804
ZOOM = 2
WIDTH = 800
# Rich names Fira Code in its export and almost nobody has it, so the family is
# chosen here rather than left to be guessed. It has to be monospaced and it has
# to carry the braille block and the block elements, which rules out most of
# them — DejaVu Sans Mono, the obvious first guess, has no braille at all.
# Whichever of these is installed is used, and fontconfig is asked rather than
# trusted: a face that cannot draw a braille cell renders an empty screen.
FONTS = (
    "JetBrainsMono Nerd Font Mono",
    "FiraCode Nerd Font Mono",
    "Iosevka",
    "Hack Nerd Font Mono",
    "Cascadia Mono",
    "Noto Sans Mono",
)
# The braille block and the block elements, the two things every painter needs.
COVERAGE = ":charset=2800 2588:spacing=100"

# name: animation, frames, frames a second, whether the interface is in shot.
DEMOS = {
    "menu": ("plasma", 44, 10, True),
    "plasma": ("plasma", 40, 10, False),
    "lattice": ("lattice", 56, 12, False),
    "waterfall": ("waterfall", 44, 12, False),
}
# Two whole rites, played in front of the recorder a step at a time. Every field
# set here is one a real run sets and every event is one a real run emits, so
# the interface does its own work rather than being drawn over. What is written
# down is the material, which is the one thing a recording cannot go and find
# again, and the answers that go with it.
SCENES = {
    "draw-radio": {
        "question": "will the noise say anything worth hearing tonight",
        "rite": ("gematria", "net_voice", "cutup"),
        "entry": "0031",
        "found": (
            "and now the weather for the coast / we are still here, if anyone "
            "is listening / a long night ahead of us",
            "internet radio",
        ),
        "said": [
            "a long night, if anyone",
            "the weather for the coast is listening",
            "we are still here ahead of us",
        ],
        "fps": 16,
    },
    "draw-pythia": {
        "question": "am I sane if I ask questions of a terminal prophet",
        "rite": ("blind", "chain", "pythia"),
        "entry": "0032",
        "found": (
            "0000000000000000000267c2b0f0e2a1e6ac6c1e0dbbf5f9f1c9b17c4a1e0d8f  "
            "/ happy birthday mum / gm / never gonna give you up",
            "blockchain",
        ),
        "said": ["Nope, lol"],
        "fps": 16,
    },
}
# Only the first is worth a GIF as well. The rest are WebP, which is a quarter
# of the size and keeps the glyph edges exactly where they were drawn.
ALSO_GIF = ("menu",)
TYPE_EVERY = 4
HOLD = 7
BINS = 48
SETTLE = 8


async def scene(name: str, into: Path) -> int:
    """Play one whole rite in front of the recorder, a step at a time.

    Every attribute set here is one a real run sets, and every event is one a
    real run emits, so the interface is doing its own work rather than being
    drawn over. What is supplied is the material, which is the one thing a
    recording cannot go and find again.
    """
    from heidr.contracts import Material

    plan = SCENES[name]
    app, pilot_out = None, []
    settings = config.Config(config.merge(config.DEFAULTS, {}), into / "config.toml")
    settings.set("ui.motion", False)
    random.seed(SEED)
    app = HeidrApp(
        settings=settings,
        user_dir=Path("/nonexistent"),
        terminal=Terminal(colours=16777216, glyphs="braille", graphics="none"),
        capabilities_found=frozenset(),
    )
    number = 0
    async with app.run_test(size=SIZE) as pilot:
        for _ in range(SETTLE):
            await pilot.pause()
        canvas = app.query_one("#visual", Canvas)

        async def hold(count: int) -> None:
            nonlocal number
            for _ in range(count):
                take_over(app.query_one("#visual", Canvas))
                board = app.query_one("#visual", Canvas)
                board.tick = number
                board.refresh()
                await pilot.pause()
                (into / f"{number:04d}.svg").write_text(app.export_screenshot(title="HEID//R"))
                number += 1

        take_over(canvas)
        await hold(HOLD)

        # The question, typed.
        app.do_ask()
        line = app.query_one("CommandLine")
        for at in range(0, len(plan["question"]) + 1, TYPE_EVERY):
            line.buffer = plan["question"][:at]
            app._render_body()
            await hold(1)
        line.buffer = plan["question"]
        app._render_body()
        await hold(HOLD // 2)

        # The rite begins. From here everything arrives as an event, exactly as
        # it does when the worker thread is really drawing.
        line.close()
        app.edit_mode = "NORMAL"
        app._enter("rite")
        app.stages = []
        app.asked = plan["question"]
        app.entry_id = plan["entry"]
        app.found = ("", "")
        app.said = []
        app.notes = []
        app.notice = ""
        app.drawing = True
        app._listen_to_the_draw()
        app._render_body()

        asked, world, reading = plan["rite"]
        # Reseeded at every swap: the animation's colour is drawn then, and the
        # exports in between take numbers from the same stream.
        random.seed(SEED)
        app.bus.emit("stage", asked)
        take_over(app.query_one("#visual", Canvas))
        await hold(HOLD * 2)

        random.seed(SEED)
        app.bus.emit("stage", world)
        take_over(app.query_one("#visual", Canvas))
        for step in range(1, 5):
            app.bus.emit("progress", (step, 4))
            await hold(HOLD)
        app.bus.emit("found", Material(text=plan["found"][0], source=plan["found"][1]))
        await hold(HOLD)

        random.seed(SEED)
        app.bus.emit("stage", reading)
        take_over(app.query_one("#visual", Canvas))
        await hold(HOLD)
        for said in plan["said"]:
            app.bus.emit("token", said)
            await hold(HOLD)

        # And the rite is over, which is a state of its own: the bar fills, the
        # animation goes back to idle and the answer stands on its own.
        app.drawing = False
        app.stages = list(plan["rite"])
        app._show_hint()
        random.seed(SEED)
        app.show_visual("reveal")
        board = app.query_one("#visual", Canvas)
        take_over(board)
        # The reveal draws the answer resolving out of noise, so it wants the
        # answer. A real run hands it over on the same event.
        board.feed("\n".join(plan["said"]))
        app._render_body()
        await hold(HOLD * 3)
    return number


def take_over(canvas: Canvas) -> None:
    """Take the animation off its timer and off the operating system.

    The canvas steps itself, and here the frame number is set by hand. Several
    painters also build a random generator on their first frame; left alone it
    comes from the operating system and no two recordings are alike.
    """
    if canvas.timer is not None:
        canvas.timer.stop()
        canvas.timer = None
    if canvas.painter is not None and hasattr(canvas.painter, "rng"):
        canvas.painter.rng = random.Random(SEED)


async def frames(name: str, into: Path) -> int:
    if name in SCENES:
        return await scene(name, into)
    animation, count, _fps, chrome = DEMOS[name]
    settings = config.Config(config.merge(config.DEFAULTS, {}), into / "config.toml")
    # The flickering slogan is a timer of its own and would move between one
    # frame and the next. It is a thing to see in the program rather than in a
    # recording of it.
    settings.set("ui.motion", False)
    # Before the interface exists, because the slogan under the sign is drawn
    # while it is being built.
    random.seed(SEED)
    app = HeidrApp(
        settings=settings,
        user_dir=Path("/nonexistent"),
        terminal=Terminal(colours=16777216, glyphs="braille", graphics="none"),
        capabilities_found=frozenset(),
    )
    async with app.run_test(size=SIZE) as pilot:
        if not chrome:
            # The animation is the subject, so the panel and the status line
            # come off and it fills the frame edge to edge.
            app.query_one("#body").display = False
            app.query_one("#chrome").display = False
        # Again before the animation is chosen, because its colour is drawn then.
        random.seed(SEED)
        app.show_visual(animation)
        canvas = app.query_one("#visual", Canvas)
        # The canvas runs its own timer, and it would keep stepping the frame
        # number while the export is waiting. The whole point here is that the
        # frame number is set by hand, so the timer goes.
        take_over(canvas)
        # The first layout takes a few passes to settle — a scrollbar appears
        # and goes again — and a recording that starts before it has is a
        # recording of the interface still making its mind up.
        for _ in range(SETTLE):
            await pilot.pause()

        fed = listens(animation)
        if fed:
            # A scrolling display is empty until it has been fed as many times
            # as it has rows, and a demo that starts empty has a seam in it.
            for number in range(-SIZE[1], 0):
                canvas.feed(spectrum(number))

        for number in range(count):
            if fed:
                canvas.feed(spectrum(number))
            canvas.tick = number
            canvas.refresh()
            await pilot.pause()
            (into / f"{number:04d}.svg").write_text(app.export_screenshot(title="HEID//R"))
    return count


def listens(animation: str) -> bool:
    from heidr import registry

    return any(entry.event for entry in registry.ANIMATIONS.get(animation, []))


def spectrum(number: int) -> list[float]:
    """A band with two carriers drifting across it, over a noise floor.

    Made from the frame number rather than from a generator, so the recording
    is the same every time it is made.
    """
    bars = []
    for place in range(BINS):
        floor = 0.08 + 0.06 * math.sin(place * 1.7 + number * 0.3)
        first = 0.9 * math.exp(-(((place - (12 + 6 * math.sin(number / 9))) / 1.6) ** 2))
        second = 0.7 * math.exp(-(((place - (33 - 5 * math.sin(number / 7))) / 1.2) ** 2))
        bars.append(min(1.0, floor + first + second))
    return bars


def rasterise(work: Path, count: int, font: str) -> None:
    for number in range(count):
        source = work / f"{number:04d}.svg"
        target = work / f"{number:04d}.png"
        if shutil.which("resvg"):
            run(["resvg", "--zoom", str(ZOOM), "--font-family", font,
                 "--monospace-family", font, str(source), str(target)])
        else:
            run(["rsvg-convert", "-z", str(ZOOM), str(source), "-o", str(target)])


def usable_font() -> str:
    """The first of the wanted faces fontconfig says can draw the glyphs."""
    try:
        listed = subprocess.run(
            ["fc-list", "-f", "%{family[0]}\n", COVERAGE], check=True, capture_output=True, text=True
        )
    except (OSError, subprocess.CalledProcessError):
        return FONTS[0]
    have = set(listed.stdout.splitlines())
    for wanted in FONTS:
        if wanted in have:
            return wanted
    return sorted(have)[0] if have else FONTS[0]


def encode(name: str, work: Path, fps: int) -> list[Path]:
    pattern = str(work / "%04d.png")
    made = [OUT / f"{name}.webp"]
    # Lossless, because everything here is a glyph edge and that is exactly what
    # a lossy encoder smears.
    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
         "-vf", f"scale={WIDTH}:-2:flags=neighbor",
         "-c:v", "libwebp_anim", "-lossless", "1", "-loop", "0", str(made[0])])

    if name in ALSO_GIF:
        palette = work / "palette.png"
        # A palette weighted toward the pixels that move, and an ordered dither
        # that stays put between frames. The default dither crawls, and a
        # background full of braille dots boils.
        scale = f"scale={WIDTH}:-2:flags=neighbor"
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
             "-vf", f"{scale},palettegen=max_colors=16:stats_mode=diff", str(palette)])
        made.append(OUT / f"{name}.gif")
        run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", pattern,
             "-i", str(palette),
             "-lavfi", f"{scale}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5",
             "-loop", "0", str(made[-1])])
    return made


def run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True)


def record(name: str, font: str) -> list[Path]:
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        count = asyncio.run(frames(name, work))
        rasterise(work, count, font)
        fps = SCENES[name]["fps"] if name in SCENES else DEMOS[name][2]
        return encode(name, work, fps)


def main(wanted: list[str]) -> int:
    if os.environ.get("PYTHONHASHSEED") != "0":
        # Python salts its hashes differently in every process, and somewhere
        # under the interface a set is walked in hash order. Two recordings made
        # on the same machine would then differ, which defeats the point.
        os.environ["PYTHONHASHSEED"] = "0"
        os.execv(sys.executable, [sys.executable, *sys.argv])

    missing = [tool for tool in ("ffmpeg",) if shutil.which(tool) is None]
    if not (shutil.which("resvg") or shutil.which("rsvg-convert")):
        missing.append("resvg or rsvg-convert")
    if missing:
        print(f"missing: {', '.join(missing)}")
        return 1

    every = {**DEMOS, **SCENES}
    unknown = [name for name in wanted if name not in every]
    if unknown:
        print(f"no demo called {', '.join(unknown)}. There are: {', '.join(every)}")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    font = usable_font()
    print(f"drawing with {font}")
    for name in wanted or every:
        for made in record(name, font):
            print(f"{made.relative_to(ROOT)}  {made.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
