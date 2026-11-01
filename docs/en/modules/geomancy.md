# geomancy — reading

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/geomancy.md)

## What it does

Raises a geomantic shield from the material and reads its last three figures: two
witnesses and a judge. A reader once marked rows of dots in the sand and counted
them. Here the sand is whatever the source found.

## Where the data comes from

The material, and a local file: `heidr/data/geomancy.txt`, one line per figure.

## How it is processed

1. The material seeds four figures, the mothers. A figure has four rows, and each
   row has one point or two. This is why a figure is four bits and there are
   sixteen of them.
2. The four daughters read the mothers crosswise: the first takes the four heads,
   the second the four necks.
3. Each pair of the eight gives a niece. Two figures add row by row: an odd total
   gives one point and an even total gives two. In code this is XOR.
4. The nieces give two witnesses, and the witnesses give the judge.

The arithmetic has one known property: **the judge always has an even number of
points**, whatever the mothers were. Only eight of the sixteen figures can be
judge. A test checks this, and it fails if a step of the shield is wrong.

The whole material goes into the seed, so this reading answers every source. The
numbers are not used directly, because a source can give between two and eight of
them, on very different scales.

## Dependencies

None. Standard library only.

## Sources

The figures, their Latin names and the shield are medieval and belong to nobody.
John Michael Greer's *The Art and Practice of Geomancy* (2009) describes the
method used here. Nothing was copied from it.

**No published readings are shipped.** The line per figure in `geomancy.txt` was
written for this project.
