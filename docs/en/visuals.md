# Visualisations

## How they work

A visualisation is a widget subscribed to one event and nothing else. It does not
know which module feeds it, and the module does not know who draws it; only the
event bus sits between them.

The practical consequence is the important one: adding a visualisation means
subscribing to an event that already exists. No module changes.

```python
@visual("waterfall", event="spectrum", glyphs="blocks")
class BlockWaterfall(Waterfall):
    ramp = BLOCKS
```

## Glyph levels

Every visualisation declares the poorest terminal it can live on: `ascii`, `box`,
`blocks` or `braille`.

The same name is registered several times at different levels, and the registry
returns the richest one this terminal can draw. In a modern emulator the
waterfall is drawn in braille cells; in a bare console, in blocks; and where
neither exists, in `.:-=+*#%@`.

Nothing has to be chosen or configured. The difference between the three
waterfalls is one line naming a character ramp; everything else is shared.

## What exists now

### waterfall

Subscribed to `spectrum`. New rows arrive at the top, old ones scroll down and
are forgotten after sixty-four.

Width is never remembered: on every render the spectrum is fitted again to
whatever columns exist now. So the window can be resized in the middle of a
capture, and the capture does not find out.

### idle

Subscribed to `tick`. Shown when nothing is happening.

It is a slowly drifting interference pattern, and it honestly means nothing: not
a progress bar, not a signal level, not a picture of the oracle thinking. It is
there so the program looks awake rather than hung.

### reveal

Subscribed to `token`. The reading arrives as noise and resolves character by
character.

The mechanic comes from `no-more-secrets`, and what matters is not the animation
but what sits behind it: the answer does not arrive finished, it has to be waited
for.

## Threads

Captures run in worker threads, and a widget may only be touched from the thread
the interface lives on. Bus events therefore go through `call_from_thread` when
they arrive from anywhere else, and directly when they do not.

A module never needs to know this. It calls `ctx.emit` and carries on.

## Adding one

Subscribe to an event that already exists: `spectrum`, `token`, `stage`, `audio`,
`tick`. Declare the glyph level honestly — a visualisation that needs braille
simply will not be chosen in a console, and that is correct behaviour rather than
a failure.

Compute geometry from the current size on every render, and cache nothing.

## Where it is drawn

The animation fills the whole terminal. The text sits on top of it in a panel
that is centred and sized by what it holds, up to the size of the terminal
itself, and the panel carries its own opaque background so the animation behind
it never makes the reading harder to read.

Two consequences follow. A painter is given the whole screen, so a moon or a
gear train grows when the window does. And the panel is never taller than there
is room for, so the status line and the command line keep their two rows
whatever happens above them.

## The question field

Asking opens a view of its own: Heiðr on the left, a box on the right with the
question in it, and one line under the box saying what the keys do. The bottom
line stays quiet while the box is open, because the same words in two places
read as two different things.

The figure is plain text inside the panel rather than a painter behind it, so a
timer of its own moves her three times a second. She blinks, her staff head
brightens, and the hem of her cloak shifts; nothing else.

## The stage bar

A rite has three slots, and the panel shows them across the top:

```
· gematria  //  ▸ babel  //    ...
```

A slot that has run is dotted, the slot at work is pointed at, and a slot the
rite has not reached yet is named `...`. The stages are learnt one at a time
from the same events that swap the animation, so the bar cannot show a module
before it is really chosen.

## The sign and the slogan

The wordmark is white and its slashes are orange, and that is the only colour in
the program. The exact orange steps down with the terminal: `#e08b1e` where
there are sixteen million colours, xterm index 214 where there are 256, and
plain yellow below that.

A slogan is drawn under it, one of a dozen. One entry in that pool is not a
slogan but an effect: the letters change three times a second while the shape of
the words stays put, in the manner of obfuscated text in Minecraft.

That entry is only in the pool when three things hold. The terminal must draw
block glyphs, or random Unicode turns into empty squares. `TERM` must not be
`dumb`. And `ui.motion` must be true, because flickering text is a thing some
people cannot look at. Fail any one of them and the effect is simply not among
the choices, the same way a radio module is not among the choices without a
dongle.

## Sources

The register of the listening screen — an ASCII spectrum scrolling in the
terminal — comes from
[retrogram-rtlsdr](https://github.com/r4d10n/retrogram-rtlsdr) by r4d10n.

The text reveal mechanic comes from
[no-more-secrets](https://github.com/bartobri/no-more-secrets) by Brian Barto,
GPL-3.0.
