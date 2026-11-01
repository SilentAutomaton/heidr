# runes — reading

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/runes.md)

## What it does

Draws three runes of the Elder Futhark, one for each Norn: Urd for what was,
Verdandi for what is, Skuld for what is owed. Each rune gets one line of meaning.

## Where the data comes from

The material, and a local file: `heidr/data/futhark.txt`, one line per rune.

## How it is processed

1. The material seeds the draw, so the same finding always gives the same runes.
   As with `tarot`, the randomness was spent when the source was consulted.
2. Three runes are sampled without replacement.
3. Each rune is printed by its Latin name. A console font rarely has the Runic
   block, and an empty box tells the reader nothing.

The whole material goes into the seed, so this reading answers every source,
including `sdr_noise`, which has numbers and no text.

There are no reversed runes. Reversal is a modern addition, and nine of the
twenty-four look the same upside down.

## Dependencies

None. Standard library only.

## Sources

The rune names are reconstructions and belong to nobody. Their order is the one
cut on the Kylver stone, about the year 400.

**No published readings are shipped.** The rune poems say little about divination,
and the modern handbooks are under copyright. The line per rune in `futhark.txt`
was written for this project.

Drawing three is an old shape. In *Germania*, chapter 10, Tacitus describes lots
cut from a branch, scattered on a white cloth, and three of them picked up and
read. He does not say the marks were runes.
