# iching — reading

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/iching.md)

## What it does

Casts a hexagram from the material and names it, together with the hexagram it
is changing into.

## Where the data comes from

The material, and a local file: `heidr/data/hexagrams.txt`, sixty-four lines,
one per hexagram, in King Wen order. Nothing is fetched.

## How it is processed

### The cast

The stalks are handled the way the Da Yan method describes, and this is the part
worth being careful about.

Forty-nine stalks are split into two heaps. One stalk is taken from the right
heap and held aside; each heap is then counted off in fours, and whatever the
counting leaves over is set aside with it. That is one change. Three changes
leave a heap divisible by four, and the quotient — 6, 7, 8 or 9 — is the line.

This produces the classical distribution, which is **not** uniform:

| Line | Meaning | Probability |
|---|---|---|
| 6 | old yin, changing | 1/16 |
| 7 | young yang | 5/16 |
| 8 | young yin | 7/16 |
| 9 | old yang, changing | 3/16 |

Casting with three coins instead gives 1/8, 3/8, 3/8, 1/8 — the two kinds of
change become equally likely, and old yin stops being rare. That is a different
book wearing the same name, and this module exists to avoid it.

### The hand that splits the heap

The split is not a fresh coin toss. The material — its source, its text, its
numbers — seeds the sequence, so the same finding always yields the same
hexagram. The randomness was already spent when the source was
consulted; spending more of it here would only dilute what was found.

### The reading

Six lines are cast from the bottom up and drawn with `o` and `x` marking the old
ones. If any line is old, the hexagram it turns into is named after it.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `corpus` | the shipped file | Path to another book, `lines\|number\|name\|gloss` per line |

## Dependencies

None. Standard library only.

## Sources

The method is classical and belongs to nobody.
[ichingshifa](https://github.com/kentang2017/ichingshifa) by kentang2017 was read
as a check that the three-change counting produces the distribution above; no
code was copied, and that repository states no licence.

**The classical judgement texts are not shipped.** Every well-known English
rendering — Wilhelm, Blofeld, Lynn — is a translation under copyright. The
glosses in `hexagrams.txt` were written for this project. Point `corpus` at a
text you have the right to use if you want the real thing.
