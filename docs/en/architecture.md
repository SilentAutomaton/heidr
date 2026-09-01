# Architecture

## The idea

A fixed pipeline gets boring after three runs: once you can see the mechanism,
the program is just a button. So the *rite itself* is the variable. Three slots,
each holding a set of interchangeable modules, and a lottery draws one module
per slot before every session.

```
question ──> [slot A: question] ──> Key ──> [slot B: world] ──> Material ──> [slot C: reading] ──> answer
```

With ten question modules, twelve world modules and eight readings there are 960
distinct rites. You never learn the schema, because it never settles.

## Contracts

Three frozen dataclasses carry everything between slots. They live in
`heidr/contracts.py`.

```python
Key(seed: int, anchors: tuple[str, ...])
Material(text: str, numbers: tuple[int, ...], source: str, extra: dict)
```

`seed` supplies addresses, frequencies and indices. `anchors` are the words a
world module looks for in what it finds. Any slot A module fits any slot B
module, because the contract is the only thing they share.

Module signatures:

```python
def run(ctx: Context, question: str) -> Key                            # slot A
def run(ctx: Context, key: Key) -> Material                            # slot B
def run(ctx: Context, question: str, m: Material) -> Iterator[str]     # slot C
```

Slot C returns an iterator, which is why a language model's output reaches the
screen token by token with no extra streaming machinery.

## Registry

`heidr/registry.py` holds four dictionaries: question, world, reading, visual. A
module registers itself with one decorator:

```python
@world("fm_voice", needs=("sdr", "stt"), visual="waterfall")
def run(ctx, key): ...
```

Discovery walks `heidr/question`, `heidr/world`, `heidr/reading`,
`heidr/visuals` and then `~/.config/heidr/modules/*.py`. Dropping a file in the
user directory is enough to enter the lottery. The core is never edited.

Every module also declares `available(ctx) -> bool`. No dongle, no network, no
speech binary — the module simply does not enter the draw, and `:checkhealth`
explains why.

## Events, not wiring

Modules publish, visualisations subscribe:

```python
ctx.emit("spectrum", bins)
ctx.emit("audio", pcm)
ctx.emit("token", text)
ctx.emit("stage", name)
```

A visualisation does not know which module feeds it, and a module does not know
who draws it. Adding a visualisation means subscribing to an event that already
exists — no change anywhere else.

## Configuration

Layers, each overriding the one before: built-in defaults, `/etc/heidr/`,
`~/.config/heidr/`, then environment variables for secrets. `[modules.<name>]`
reaches the module as `ctx.settings`, so a new setting never touches
`config.py`. API keys come from the environment only and are never written to a
file.

## Terminal capabilities

`heidr/capabilities.py` probes three things: colour depth, glyph level (braille,
blocks, box drawing, plain ASCII) and graphics protocol (kitty, sixel, none).
A bare Linux console reports eight colours, blocks and boxes but no braille and
no graphics.

Two stylesheets follow from that, and every visualisation declares the glyph
level it needs. The waterfall exists three times — braille, half blocks, and
`#.:` — and the right one is chosen for you.

## Audio

One output path for the whole program, so "every sound is levelled" is a
property of the wiring rather than a rule anyone has to remember.

```
rtl_fm ──s16le──> reader ──┬──> gain control ──> limiter ──> sounddevice
                           ├──> FFT ──> spectrum event
                           └──> ring buffer ──> speech provider
```

Levelling is a slow automatic gain stage aiming at a target RMS, followed by a
hard limiter so nothing clips. All four parameters are configurable and change
live from the interface.

## Nothing waits forever

A rite talks to a radio, to public endpoints and to a daemon, and every one of
them can be slow. A timeout handed to `requests` bounds one socket operation,
not the whole exchange: a slow public feed held a draw for eighty seconds
without ever exceeding a ten second timeout.

So waiting is bounded in one place per kind of wait.

`heidr/net.py` runs a fetch in a thread and abandons it when the budget is
spent, raising a message that names the host and says what to do. Every network
world module goes through it.

`entropy.collect` asks all its sources at once and keeps whatever answered
within the budget. A source that is too slow is simply absent from the mix,
which is the same as being unreachable, and the seed is never short of material
because `os.urandom` and the clock are always in it.

The radio fails loudly rather than quietly. A capture that returns no samples
does not become a hash of nothing: it raises, and the draw is recorded as void.

## Ledger

Draws are stored as one plain text file each, in the manner of `dreamdir`: a
fixed width identifier, a `key: value` header, a blank line, then the body.
Greppable, readable by a human, and still readable in ten years without this
program.

The hash of the question is written *before* the draw, and each entry chains to
the previous one. Re-rolling after an unwanted answer is not possible, and the
whole history verifies with one command.
