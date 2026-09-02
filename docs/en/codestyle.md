# Code style

One rule above the others: **the code must read cleanly with every comment
deleted.** Comments explain why, never what. Write them in plain technical
English.

## Shape

- Functions stay short. If one needs a section header comment, it wanted to be
  two functions.
- Dataclasses instead of dictionaries for anything that crosses a module
  boundary.
- Type hints everywhere. No docstrings — the prose lives in `docs/`.
- Explicit imports. No `from x import *`, no re-export shims.

## Do not

- No metaclasses, no descriptors, no `__getattr__` tricks.
- No inheritance deeper than one level, and no abstract base class for a
  protocol with one implementation.
- No factories, builders or registries beyond the four the project already has.
- No `**kwargs` forwarded through layers. Name the parameters.
- No error handling for cases that cannot happen. Trust internal guarantees.
- No compatibility shims for code that was removed.

## Naming

Say what the thing is, not what it is made of.

```python
# no
def proc(d, f=None): ...
mgr = ModuleManagerFactory().create()

# yes
def draw_rite(config: Config) -> Rite: ...
```

## Errors the user sees

Three parts, in this order: what happened, why, what to do. No exception class
names, no tracebacks, and nothing that blames the reader.

```python
# no
raise RuntimeError("SDR init failed (errno 19)")

# yes
raise Unavailable(
    "No radio found. The RTL-SDR dongle is not plugged in. "
    "Connect it and run :checkhealth."
)
```

All user visible text lives in `heidr/strings.py`, never inline.

## Borrowed code

Keep the original header. Author, link, licence, and one line on what was taken.

```python
# Von Neumann debiasing and SHA-512 whitening.
# Adapted from rtl-entropy by Paul Warren, GPL-3.0.
# https://github.com/pwarren/rtl-entropy
```

If the licence does not allow the copy, reimplement from the description and say
so: `# Method described in <link>; implementation is our own.`

## Documentation language

Documentation is bilingual, and the two halves are held to different standards.

The English files in `docs/en/` are written in plain technical English: short
sentences, direct word order, no idioms, no synonyms for variety. They will be
read by people whose first language is not English and translated by machine.

The Russian files in `docs/ru/` are written in proper literary Russian. They are
connected prose, not a word-for-word rendering of the English and not a pile of
clipped fragments: full sentences, real transitions between paragraphs, a term
introduced only when it is needed and explained the first time it appears. A
table belongs where the data is tabular: module lists, licences,
signatures — but an explanation is never replaced by one.

The test is simple: read a paragraph aloud. If it sounds like the translated
manual for a household appliance, rewrite it.

Files in `docs/en/` and `docs/ru/` mirror each other by name and by meaning.
Change one, change the other in the same commit.

## Comments

Only where the logic is not obvious from the code. No section banners, no
commented out code, no notes about tools, plugins or assistants.

```python
# no
# loop over modules
for module in modules:

# yes
# Modules drawn recently are penalised, not banned: a repeat must stay possible
# or a coincidence would mean nothing.
weight = base / (penalty if name in recent else 1)
```
