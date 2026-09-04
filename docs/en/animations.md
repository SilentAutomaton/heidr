# Animations

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/animations.md)

## What one is

An animation is a painter: a function of the frame size and the frame number,
returning the lines to show. Nothing more.

```python
@animation("life", glyphs="blocks", fps=8)
def paint(frame: Frame) -> list[str]:
    ...
```

The frame carries everything a painter is allowed to know: `width`, `height`,
`tick`, the character `ramp`, the terminal's `glyphs`, and the last event as
`payload`. Geometry arrives on every frame and is never remembered, which is why
the terminal can be resized in the middle of a capture and nothing notices.

A painter that ignores `payload` is a background animation. A painter that reads
it is a picture of data. That is the whole difference: the waterfall and the
game of life are the same kind of object.

Where the painter needs to keep something between frames, it is a class with a
`paint` method instead of a function. `feed` is the other half: the canvas hands
it each event of the name the animation declared.

## Adding one

One file in `heidr/visuals/art/`, one function or class, one decorator. No core
file is edited, exactly as with a source module.

Declare the glyph level honestly. An animation that needs braille will simply
not be chosen in a bare console, and that is correct behaviour rather than a
failure.

Before writing a new one, look for it. Terminal graphics is old ground, and
somebody has usually done the hard part better; borrowing it with the author
named in `credits.md` beats a worse version written here.

## Glyph levels

Every animation declares the poorest terminal it can live on: `ascii`, `box`,
`blocks` or `braille`.

The same name is registered several times at different levels, and the registry
returns the richest one this terminal can draw. In a modern emulator the
waterfall is drawn in braille cells; in a bare console, in blocks; and where
neither exists, in `.:-=+*#%@`.

Nothing has to be chosen or configured. The difference between three waterfalls
is one line naming a character ramp; everything else is shared.

## Colour

Every animation used to be drawn in one colour, so the plasma field, the gears
and the falling glyphs were the same orange as the sign above them. Now each
one has a colour of its own, and several are offered per animation with one
drawn when it starts: the gears are teal today and brass tomorrow.

The table is `heidr/visuals/palette.py`, and it has rules worth keeping.

The animation is a **background**. The panel and the wordmark stand on top of
it, so every colour is held below the panel text in lightness and kept at
moderate saturation. A pure primary vibrates on a dark ground and reads as a
screensaver rather than as an instrument. A large red field reads as an error.
Neither is in the table, and a test enforces both.

The colour suits the subject rather than decorating it. Radar green is the only
colour a radar screen has ever been. The library is parchment. The seal is
cinnabar and the stone under it is jade. Silence is the grey the slogan is set
in. Where an animation imitates a real instrument, the instrument decides.

Colour steps down with the terminal exactly as the accent does: the hex value
where there are sixteen million colours, the nearest xterm index where there are
256, and **nothing at all below that**. The bare console theme is white on black
with reversed video, and tinting it would only spoil the one thing it does well.

Two animations are excluded and keep the accent. `seeress` is the sign of the
program and `reveal` is the answer, and the orange belongs to those.

### Coloured by level

Three animations draw something measured, and those are coloured by how much of
it there is rather than flatly: the waterfall runs from a cold floor to a hot
carrier, the oscilloscope from a dim trace to a bright one, the seismograph from
quiet slate to violent clay. That is what the instruments they imitate do, and
it is the reason a spectrum display is legible at a glance.

The canvas returns a `rich.text.Text` for those and a plain string for
everything else. The colour is chosen by the character's place in the ramp, and
neighbouring characters that land on the same colour share one span, so a row
costs a few dozen spans rather than one per cell. It is built as a `Text` and
never as markup, because a painter is free to draw a square bracket and markup
would read it as a tag.

Where the terminal has only 256 colours the stops are used as they are: an
xterm index cannot be mixed with another one.

## Which module brings which

A module names its animation in the same `visual` field it has always had, and
the animation is swapped when that stage begins. A module that names nothing is
given one of the background set at random, so every step has something to look
at rather than only the named ones.

| Animation | Shown for | What it is |
|---|---|---|
| `plasma` | `blind`, idle | Four sine waves radiating from four points |
| `life` | idle | Conway's rules, seeded from the measured entropy |
| `rule30` | idle | Wolfram's rule, one new line a frame, scrolling up |
| `rings` | idle | Ripples spreading from four drops on still water |
| `runes` | idle | The Elder Futhark, rising and fading |
| `rain` | idle | Falling columns of glyphs |
| `starfield` | `planetary`, idle | Stars with parallax |
| `moon` | `moment`, `calendar`, idle | The phase of the moon, growing with the terminal |
| `seeress` | the question field | Heiðr, breathing, blinking, staff in hand |
| `waterfall` | `fm_voice`, `mw_voice`, `sw_voice` | The spectrum, scrolling |
| `globe` | `net_voice` | A wire globe turning, a mark where each station is |
| `relay` | `kiwi_voice` | Somebody else's mast on the horizon, and the waves it hears |
| `scanlines` | `twitch_voice` | A glass screen with the picture not quite locked |
| `scope` | `ism`, `rtl_peak` | The live waveform |
| `radar` | `sky`, `adsb_local` | A sweep with a mark on it |
| `seismo` | `quake` | A seismograph trace |
| `hexlib` | `babel` | A wall of hexagons with letters falling through it |
| `codepage` | `mojibake` | A page re-read through one wrong encoding after another |
| `bits` | `sdr_noise` | Bits raining, pairs cancelling, the survivors becoming a digest |
| `sieve` | `skeleton` | Words shaken until their vowels fall out |
| `zipf` | `rarest` | A frequency histogram collapsing to the one bar nobody says |
| `initials` | `acrostic` | First letters lifting out of a stack of words |
| `abacus` | `gematria` | Letters dropping onto beads, and a total growing under them |
| `chain` | `chain` | Blocks, with a hash running along them |
| `dish` | `apt`, `hline` | A dish, and a noise floor rising under it |
| `cog` | anything that names no visual | A train of meshed gears, turning |
| `mirror` | `reversal` | A question going in one side of an axis and its opposite leaving the other |
| `lattice` | `embed` | A cloud of points settling onto one direction |
| `vapour` | `pythia` | Fumes rising from a tripod |
| `hush` | `mute` | The reading that returns nothing |
| `hexagram` | `iching` | Six lines building from the bottom up |
| `cards` | `tarot` | A card turning over |
| `scissors` | `cutup`, `oblique` | Text cut up and scattered |
| `reveal` | the answer | The reading resolving out of noise |

The gears are worth one line of explanation, because they are not a progress
bar: nothing in the mechanism knows how far along the answer is. It says only
that work is happening, which is the honest amount to say.

### Every stage lasts three seconds at least

An animation nobody sees was not worth drawing. Some modules finish in
milliseconds, so a module that has answered holds its slot until three seconds
have passed since it started; a slower module is not delayed at all. The rule
lives in the run rather than in any animation, and it is described in
[the architecture](architecture.md#nothing-goes-too-fast-either).

### While a slow step says nothing

Recognising speech is the longest silence in the program. A large model on a
thirty second window takes over a minute, and a capture of three stops is two of
those — during which the source has finished, no event arrives, and the
animation that was running is a picture of data that stopped coming.

Three things say that it is still alive. The status line names the step and how
much audio is being listened back to. The animation swaps to the gears, which
mean work is happening and nothing knows how far along it is. And the spinner
that used to turn only in the window title now turns in the status line as well,
where somebody looking at the terminal can see it.

The spinner is on for the whole of a draw, not only for the recogniser, so any
step that goes quiet — a slow feed, a model thinking — shows the same sign.

### Silence is allowed to be funny

`hush` is not one picture but a set, and the lot decides which is shown. The
reading has returned nothing, and this is the one place the program is allowed
a joke: there is no answer either way, so there is nothing to lose.

The set holds the serious figure with a finger to its lips and the thoroughly
unserious shrug, `¯\_(ツ)_/¯`. The glyph ladder applies here too. `ツ` is
katakana and a console font usually has none, so the same pose exists in plain
ASCII for poor terminals.

Nothing else takes this tone. The joke belongs to the empty answer alone, and a
real answer is shown plainly.

## Recording them

`tools/make_demo.py` writes the looping pictures in `docs/demo/`.

```
python tools/make_demo.py            every demo in the table
python tools/make_demo.py plasma     one of them
```

<p align="center">
  <img src="../demo/plasma.webp" alt="plasma" width="420">
  <img src="../demo/waterfall.webp" alt="waterfall" width="420">
</p>

Nothing here records a screen. The interface is run headless, the frame number
is set by hand rather than left to a timer, and every frame is exported as an
SVG of the real widget tree — the same export the snapshot tests use. Then
`resvg` rasterises each frame with a named monospace font and `ffmpeg` encodes
them.

That is the whole reason for doing it this way rather than with a screen
recorder or a terminal replayer. A painter is a function of the frame number, so
frame N is frame N whichever machine draws it, and a loop can be closed by
choosing a frame count rather than by trimming footage until the join stops
showing. The one test that guarantees it is already in the suite: an animation
repainted at the same tick must not change.

Two things have to be pinned or the recording is not reproducible after all.
Several painters build a random generator on their first frame, so the tool
hands them a seeded one. And Rich names a font in its export that almost nobody
has, so the tool names the family instead of leaving it to be guessed.

Two of the recordings are whole rites rather than one animation: `draw-radio`
and `draw-pythia`. Those are played a step at a time from a table at the top of
the tool. Every field a scene sets is one a real run sets and every event it
emits is one a real run emits, so the interface does its own work rather than
being drawn over; what the table supplies is the material and the answer, which
are the things a recording cannot go and find again.

The result is a lossless animated WebP, and for the one on the front page a GIF
as well. WebP is about a third of the size and keeps the glyph edges exactly
where they were drawn, which is the one thing a lossy encoder ruins. The GIF
uses a palette weighted toward the pixels that move and an ordered dither that
stays put between frames; the default dither crawls, and a screen full of
braille dots boils.

## Where it is drawn

The animation fills the whole terminal. The text sits on top of it in a panel
that is centred and sized by what it holds, and the panel carries its own opaque
background so the animation behind it never makes the reading harder to read.

**Nothing else may cover the canvas.** A widget above it hides its characters
even when that widget's background is fully transparent: the compositor gives
the cell to whoever is on top, and blending colours does not bring the glyphs
underneath back. A full width container over the canvas is therefore the same
thing as no animation at all, which is exactly what happened here for a whole
cycle, while every test about sizes and stylesheets stayed green.

The test that catches it composites the screen and looks for the characters of
`plasma`, which fills every cell, in the corners. That is the only kind of proof
that means anything here: what the terminal would really receive.

Two more consequences. A painter is given the whole screen, so a moon or a gear
train grows when the window does. And the panel is capped at ninety per cent of
the width and wraps its text, so it can never grow to cover everything.

## The panel

A run is shown in labelled blocks rather than as one flat stretch of text:

```
· gematria  //  · babel  //  ▸ pythia

question · 00012
  Что мне делать?

found · bitcoin/914233
  !lzz(5<Sq_Ewq> CORE|u& fmBN ,KT2+ 0 EXSAT sysB
  … 180 more characters

answer · pythia
  Ешь то, что не выбирал.
```

Everything is folded to the width of the panel. Before, a line of three hundred
characters was cut at the edge and the rest was simply gone from the screen,
with nothing to say so. The material is capped at ten lines and says how much is
left over; the whole of it is always in the ledger.

The material appears as soon as the source hands it over, on a `found` event,
rather than when the whole run finishes. A reading through a language model
takes half a minute, and there is no reason to stare at nothing meanwhile.

A message that ends a run is written into the panel with a `!` in the accent
colour and repeated in the bottom line: a refusal, a failure, or a reading that
produced no lines. Small talk, such as a setting that changed, stays at the bottom
alone.

## The question field

Asking opens a view of its own: Heiðr on the left, a box on the right with the
question in it, and one line under the box saying what the keys do. The bottom
line stays quiet while the box is open, because the same words in two places
read as two different things.

The figure is plain text inside the panel rather than a painter behind it, so a
timer of its own moves her three times a second. She blinks, her staff head
brightens, and the hem of her cloak swings; nothing else. Below seventy four
columns she is dropped and the field keeps the room: half a figure beside half a
field helps nobody.

Her marks, the eyes and the mouth and the head of the staff and the hem, are
found in
the drawing at import time rather than written down as coordinates. The drawing
changed once and the coordinates did not, and her face came out bent.

## The stage bar

A run has three slots, and the panel shows them across the top:

```
· gematria  //  ▸ babel  //    ...
```

A slot that has run is dotted, the slot at work is pointed at, and a slot the
run has not reached yet is named `...`. The stages are learnt one at a time
from the same events that swap the animation, so the bar cannot show a module
before it is really chosen.

## The sign and the slogan

The wordmark is white and its slashes are orange, and nothing else in the
program takes that orange except the answer. The exact value steps down with the
terminal: `#e08b1e` where there are sixteen million colours, xterm index 214
where there are 256, and plain yellow below that. The animation behind the sign
has [a colour of its own](#colour); the sign does not share it.

A slogan is drawn under it, one of a dozen. One entry in that pool is not a
slogan but an effect: the letters change three times a second while the shape of
the words stays put, in the manner of obfuscated text in Minecraft.

That entry is only in the pool when three things hold. The terminal must draw
block glyphs, or random Unicode turns into empty squares. `TERM` must not be
`dumb`. And `ui.motion` must be true, because flickering text is a thing some
people cannot look at. Fail any one of them and the effect is simply not among
the choices, the same way a radio module is not among the choices without a
dongle.

## The window title

The title is the only thing visible when the window is not. While a run is going
it
reads:

```
⠹ HEID//R — fm_voice 2/4
```

The spinner comes first, then the sign, then the module at work and how far it
has got. Between runs it is the sign alone, with no trailing dashes or
zeroes, and the program restores it on the way out so nothing is left spinning
in a window list.

The spinner is braille where the terminal draws braille and `|/-\` where it does
not. Progress comes from a `progress` event carrying a done and a total. The
sweep across the band sends it, because it is the longest thing the program
does; a module that sends nothing shows the stage of the run instead, `2/3`.
Inventing a percentage for work that cannot measure itself would be worse than
saying nothing.

`App.title` is set as well, and the escape sequence is written directly, since
a bare console ignores what it does not know.

## Threads

Captures run in worker threads, and a widget may only be touched from the thread
the interface lives on. Bus events therefore go through `call_from_thread` when
they arrive from anywhere else, and directly when they do not.

A module never needs to know this. It calls `ctx.emit` and carries on.

## Sources

The plasma field and the turning cog come from
[asciimatics](https://github.com/peterbrittain/asciimatics) by Peter Brittain,
Apache-2.0.

The register of the listening screen, an ASCII spectrum scrolling in the
terminal, comes from
[retrogram-rtlsdr](https://github.com/r4d10n/retrogram-rtlsdr) by r4d10n.

The text reveal mechanic comes from
[no-more-secrets](https://github.com/bartobri/no-more-secrets) by Brian Barto,
GPL-3.0.

The falling columns follow [cmatrix](https://github.com/abishekvashok/cmatrix)
by Abishek V Ashok, GPL-3.0.

The rules of the game of life are John Conway's, 1970, and are not ours to
adjust.

The garbled slogan copies the register of obfuscated text in Minecraft.

Heiðr herself, the cards, the dish and the gears are drawn for this project.
Kaomoji such as `¯\_(ツ)_/¯` are folklore with no clear author and are taken as
they are; anything with a named author would be named here beside the rest.
