# Adding a module

A module is one file, one decorator, one `run` function, plus documentation and
usually no test of its own. There are four kinds.

| Kind | Package | Signature |
|---|---|---|
| Question | `heidr/question/` | `run(ctx, question) -> Key` |
| World | `heidr/world/` | `run(ctx, key) -> Material` |
| Reading | `heidr/reading/` | `run(ctx, question, material) -> Iterator[str]` |
| Visual | `heidr/visuals/` | a widget subscribing to an event |

You can also drop the same file into `~/.config/heidr/modules/` and it joins the
lottery without touching the repository.

## A complete world module

`heidr/world/quake.py`:

```python
import requests

from heidr.contracts import Key, Material
from heidr.registry import world

FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


def available(ctx) -> bool:
    return ctx.has("net")


@world("quake", needs=("net",), visual="tremor")
def run(ctx, key: Key) -> Material:
    events = requests.get(FEED, timeout=10).json()["features"]
    if not events:
        return Material("", (), "usgs", {})

    event = events[key.seed % len(events)]
    place = event["properties"]["place"]
    magnitude = event["properties"]["mag"]
    lon, lat, depth = event["geometry"]["coordinates"]

    ctx.emit("stage", f"quake {place}")
    return Material(
        text=place,
        numbers=(int(magnitude * 10), int(depth)),
        source="usgs",
        extra={"lat": lat, "lon": lon},
    )
```

That is the whole module. Notes:

- `needs` uses the known capability names: `net`, `sdr`, `stt`, `llm`, `audio`.
  The lottery skips a module whose needs are not met.
- `available()` is a cheap probe. It must never raise and never block for long.
- `visual="tremor"` is a preference, not a requirement. If the visual is missing
  or the terminal cannot draw it, an idle animation runs instead.
- `ctx.emit` is how anything reaches the screen. Never print.
- `ctx.settings` holds this module's `[modules.quake]` section, already merged
  with the defaults you declared.
- `ctx.levels` is the interface's own volume, mute and levelling. A module that
  plays sound passes it to `audio.Output` rather than reading the numbers out of
  the configuration, or the volume keys will not reach what is playing.

## Settings

Declare defaults on the decorator and read them from `ctx.settings`:

```python
@world("fm_voice", needs=("sdr", "stt"), defaults={"dwell_s": 4, "sweep": "random"})
def run(ctx, key):
    dwell = ctx.settings["dwell_s"]
```

They appear in the settings editor automatically, one row each, with their
effective values. Do not touch `config.py` — the only reason to open it is to add
a row to `CHOICES` when an option has a fixed set of values and should be
switched with `Enter` rather than typed.

## A reading module

Readings stream, so they yield:

```python
@reading("cutup")
def run(ctx, question: str, material: Material):
    for line in cut_up(material.text, ctx.settings["max_cut"]):
        yield line
```

If a reading calls a language model, get it from `ctx.llm` and pass the tokens
straight through. **The model interprets the material; it never selects it.**

## A visual

A visual subscribes to an event and declares the poorest terminal it can live
on:

```python
@visual("waterfall", event="spectrum", glyphs="blocks")
class Waterfall(Widget): ...
```

`glyphs` is one of `braille`, `blocks`, `box`, `ascii`. Register the same name
several times with different glyph levels and the best usable one is chosen.

Recompute geometry from the current size on every render. Nothing may cache a
width: the terminal is resized while a capture runs, and the capture must not
notice.

## Before it is done

1. `docs/en/modules/<name>.md` and `docs/ru/modules/<name>.md`, with all five
   sections: what it does, where the data comes from, how it is processed,
   dependencies, sources.
2. New dependency? Add it to the tables in `README.md` and to
   `pyproject.toml` as an optional extra if the module is not core.
3. Borrowed something? Header in the file, row in `docs/en/credits.md`.
4. `pytest` — the registry suite already covers your module. Add a test only for
   logic it cannot see.
5. One commit, one line: `add quake world module`.
