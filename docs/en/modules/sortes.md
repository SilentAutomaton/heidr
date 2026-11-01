# sortes — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/sortes.md)

## What it does

Opens a book at a chosen place and hands that passage to the run. People did this
with Virgil for over a thousand years and called it *sortes Vergilianae*. This
program opens the Elder Edda, because one of its poems is spoken by a seeress.

## Where the data comes from

A local file: `heidr/data/edda.txt`. It holds two poems, the Völuspá and the High
One's Lay, 203 stanzas in all. No network and no hardware are needed, so this
source is always available.

Stanza 26 of the Völuspá names the woman this program is named after: "Heidi they
called her, whithersoe'r she came."

## How it is processed

1. The file is split into passages at blank lines. Lines that start with `#` are
   ignored.
2. The key's seed selects one passage, modulo how many there are. So the question
   module decides the place, not a fresh coin toss.
3. The passage becomes the material's text. Its place and the number of passages
   become its numbers.

A file with no passages gives empty material, and another source takes the slot. A
file that cannot be read does the same.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `book` | the shipped file | Path to another UTF-8 text, with a blank line between passages |

## Dependencies

None. Standard library only.

## Sources

The translation is by Benjamin Thorpe, *Edda Sæmundar Hinns Fróða*, 1866, and is in
the public domain. The text was taken from
[Project Gutenberg eBook 14726](https://www.gutenberg.org/ebooks/14726). Stanza
numbers and footnote marks were removed. The square brackets are in the source,
and stanza 63 is not.
