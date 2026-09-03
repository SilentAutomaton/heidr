# Architecture

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/architecture.md)

## The idea

A fixed pipeline gets boring after three runs: once you can see the mechanism,
the program is just a button. So the chain itself is the variable. There are
three slots, each holding a set of interchangeable modules, and one module is
picked at random for each slot before every run.

```
question ──> [slot A: question] ──> Key ──> [slot B: source] ──> Material ──> [slot C: reading] ──> answer
```

Ten question modules, twelve sources and eight readings make 960 distinct
chains. The schema never settles long enough to be learnt. The code calls a
chain a `Rite` and the interface calls it a "rite"; this document calls it a
run, because that is what it is.

## Contracts

Three frozen dataclasses carry everything between slots. They live in
`heidr/contracts.py`.

```python
Key(seed: int, anchors: tuple[str, ...])
Material(text: str, numbers: tuple[int, ...], source: str, extra: dict)
```

`seed` supplies addresses, frequencies and indices. `anchors` are the words a
source looks for in what it fetches. Any slot A module fits any slot B module,
because the contract is the only thing they share.

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
`heidr/visuals` and then `~/.config/heidr/modules/*.py`. A file dropped in the
user directory joins the choice without the core being edited.

Every module also declares `available(ctx) -> bool`. A missing dongle, an
unreachable network or an absent speech binary keeps it out of the choice, and
[`:checkhealth`](checkhealth.md) explains which of the three it was.

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
exists, and nothing else changes.

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
level it needs. The waterfall exists three times, in braille, in half blocks and
in `#.:`, and the registry returns whichever one this terminal can draw.

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

## The radio has two jobs

The same dongle serves two purposes that must not be confused with each other.

As a source of entropy, `sdr_noise` tunes to an empty frequency and samples the
noise floor. Nothing is being listened to: the samples are debiased, whitened,
and turned into a number. This is the oldest use of the radio here and it stays.

As a source of voices, `fm_voice`, `sw_voice` and `mw_voice` tune to real
transmitters and turn speech into text. There the content is what matters.

The two are not alternatives, and either can be picked. A voice module that
lands on an empty band has not fallen back on the entropy module; it has found
an empty band, which is a different fact about the evening.

## A voice does not have to arrive by aerial

Half the program used to be invisible to anybody without a dongle. So the same
idea — visit several transmitters, keep a few seconds of each, hand the audio to
the recogniser — was given three sources that need no hardware at all.
`net_voice` walks random internet radio stations, `kiwi_voice` borrows a public
KiwiSDR one slot at a time, and `twitch_voice` listens to a live channel.

`heidr/stream.py` is to those three what `heidr/radio.py` is to the aerial ones,
and it is deliberately shaped the same way. A `Stop` names one place to listen;
`gather` walks the stops with one buffer feeding the speaker, the waterfall and
the recogniser on the same turn of the loop; and the transcription and anchor
matching are the radio's own functions, not copies of them.

Two things differ, and both come from the network rather than from the design.

A listed station is not always a working station, so the caller offers more
stops than it wants and the ones that give nothing are passed over. On the
aerial an empty frequency is an answer; here a dead URL is not, it is a bad
address.

And a station sends a burst of buffered audio the moment a listener connects, so
the first seconds arrive faster than real time. They are neither dropped nor
slowed: the sound card blocks until it has room and the loop takes its pace from
the speaker. With no sound card the visit is simply quicker, which costs nothing
because nobody is listening to it.

## Nothing waits forever

A run talks to a radio, to public endpoints and to a daemon, and any of them can
be slow. A timeout handed to `requests` bounds one socket operation rather than
the whole exchange: a slow public feed once held a run for eighty seconds
without ever exceeding a ten second timeout.

So waiting is bounded in one place per kind of wait.

`heidr/net.py` runs a fetch in a thread and abandons it when the budget is
spent, raising a message that names the host and says what to do. Every network
source goes through it.

`entropy.collect` asks all its sources at once and keeps whatever answered
within the budget. A source that is too slow is simply absent from the mix,
which is the same as being unreachable, and the seed is never short of material
because `os.urandom` and the clock are always in it.

The radio fails loudly. A capture that returns no samples never becomes a hash
of nothing: it raises, and the run is recorded as void.

## Nothing goes too fast either

The opposite problem is smaller but it is real. A module that reads a local file
or does arithmetic on the question is finished in a few milliseconds. Its
animation appears and disappears inside one frame, and the reader sees the stage
bar jump rather than a rite passing through three stages.

So every module has a floor as well as a budget. When it finishes, the run waits
until three seconds have passed **since that module started** — not three
seconds added on top. A module that took five seconds waits for nothing, and the
floor is invisible to it.

`rite.min_stage_s` is the number, and zero turns the floor off. The wait is
sliced, so `Escape` still ends a run at once, and a module that refused is held
for the same three seconds, because the line naming who gave way to whom needs
to be read as well.

## A module that cannot answer

Every source can be unavailable today. Until recently the first failure ended
the whole run: an unreachable feed, a field missing from a reply, a dongle held
by another program. Thirteen other sources stood idle while that happened.

Now the slot picks again. The choice was made at random in the first place, and
a module that cannot answer is unavailable rather than unwanted, so replacing it
does not repeat the draw.

| What happened | What the run does |
|---|---|
| `Unavailable` | Picks another module for the slot |
| Any other exception, such as a parse error or a missing field | The same |
| Material with neither text nor numbers | The same: the source returned nothing |
| A reading that yields no lines | The same, unless it declares that it returns none |
| `Cancelled` | Stops. The reader asked for it, so it is not a failure |

`rite.attempts` sets how many modules a slot may try, three by default. One
restores the old behaviour where the first failure ends the run. When the
attempts run out, or no module is left, the run gives up and repeats the last
refusal it was given.

A reading is the one slot that can fail in the middle of a sentence. If it broke
before producing a line, another reading is picked. If it broke after producing
one, what it produced is kept and the run ends there, because running it again
would repeat the first line.

An empty answer has to be declared rather than guessed at, so the module states
it: `@reading("mute", silent=True)`. Only a module that says this may return
nothing without being replaced.

Every module that gave way appears on screen at the moment it happens, and in
the entry afterwards under an `Instead` header. A substitution the reader cannot
see would be a lie by omission.

## Ledger

Runs are stored as one plain text file each, in the manner of `dreamdir`: a
fixed width identifier, a `key: value` header, a blank line, then the body.
Greppable, readable by a human, and still readable in ten years without this
program.

The hash of the question is written before anything is fetched, and each entry
is sealed against the one before it. Asking again after an unwanted answer is
not possible, and the whole history verifies with one command.

An entry ends in one of three states, and the difference matters:

| Status | Meaning | Can the question be asked again? |
|---|---|---|
| `complete` | The run finished and produced lines | Not for a day |
| `broken` | A source answered and no reading could read it | Yes, at once |
| `void` | Nothing was found at all | Yes, at once |

The rule exists to stop a second attempt at an unwelcome answer, not to spend a
question on a timeout. A question is therefore spent by an answer arriving, and
by nothing else. `void` and `broken` record different facts, namely whether any
material was found, and neither of them costs the asker anything.

One case looks like a failure and is not. A run silenced by the random choice,
or read by `mute`, counts as complete and does spend the question: returning
nothing was the outcome, and the material in the entry stands in place of the
answer.

The hold lasts a day rather than for good. "How will today go" is a different
question tomorrow, and the entry already carries the date it was promised on, so
the rule reads it instead of scanning the whole history for ever.
`ledger.repeat_after_h`
sets the window, and zero restores the older rule where a question was spent
permanently. A date nobody can parse keeps the question spent: only time lifts
the rule, never a damaged file.

A chain named by hand skips the check entirely: `:draw rarest//babel//iching`,
or the same thing picked from the menu. Such an entry is marked `(chosen)`.
Putting one question to several chains is an experiment, and the mark keeps it
apart from a chain that was picked at random.
