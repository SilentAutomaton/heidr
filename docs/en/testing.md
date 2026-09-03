# Testing

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/testing.md)

The goal is that every behaviour has exactly one test that fails when the
behaviour breaks. Coverage is measured but is not the target: a suite that
mirrors the code line by line only makes the code harder to change.

## Running

```
pytest                  # everything that needs no hardware and no network
pytest -m live          # the rest: real radio, real network, real audio device
```

`live` tests are excluded by default in `pyproject.toml`.

## The registry suite

`tests/test_registry_contract.py` is parametrised over every registered module,
so it grows on its own. A new module is checked automatically for:

- the return type its slot promises;
- `available()` returning a bool and never raising;
- declared `needs` using only known capability names;
- surviving an empty question and a stub context;
- having documentation in both languages, with the dependency and source
  sections present.

Because of this, most modules need no test file of their own. Write one only for
logic a contract test cannot see.

## What gets its own test

One test per behaviour that can actually break:

- a question module is deterministic: the same question yields the same key;
- the Da Yan casting produces the real distribution, where old lines are much
  rarer than young ones, checked statistically over many casts with a tolerance;
- Von Neumann debiasing removes the bias from a deliberately biased stream;
- the Library of Babel bijection round-trips: address to text and back;
- the ledger chain verifies, and a tampered entry is detected;
- a repeated question is refused;
- the recency penalty lowers a weight without zeroing it;
- config layers override in the right order, and writing back keeps only the
  differences from the defaults;
- capability detection returns the expected levels across a matrix of `TERM` and
  `COLORTERM` values;
- the gain control reaches its target and the limiter never exceeds its ceiling;
- every network parser handles its recorded sample.

## What gets no test

Trivial wrappers, dataclass construction, the string table, Textual internals,
exact wording of messages, output formatting. **If a test breaks when a variable
is renamed, it should not exist.**

## Boundaries

Tests never touch the network, the radio or an audio device. Use the fakes in
`tests/conftest.py`:

| Fake | Replaces |
|---|---|
| `stub_context` | the real `Context`, with an in-memory event bus |
| `fake_pcm` | `rtl_fm`, generating synthetic samples |
| `fake_llm` | any provider, yielding a fixed token list |
| `fake_stt` | any speech provider, yielding fixed text |
| `tests/fixtures/*.json` | recorded USGS, blockchain, beacon and ADS-B replies |

If a test needs the real thing, mark it:

```python
@pytest.mark.live
def test_dongle_actually_tunes(): ...
```

## Interface tests

Textual's own `App.run_test()` pilot drives the interface. Test the behaviour
and the layout decision, never the pixels: mode transitions, command parsing,
the refusal on a tiny terminal, reflow between 40×12 and 200×50, keymap
overrides, and the fallback to a simpler visualisation on a poor glyph level.

No screenshot snapshots. They break on every unrelated change and teach nothing.

## Where tests live

In the same commit as the code they cover. There is no "write the tests" step at
the end of the plan, and there never will be.
