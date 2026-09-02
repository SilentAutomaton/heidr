# babel — world module

## What it does

Opens a page of the Library of Babel. Given an anchor word, it does the more
second use: it returns the address where that word has always been.

## Where the data comes from

Nowhere. Nothing is fetched and nothing is stored.

This is the point of the library, and it is worth stating plainly. The pages are
not kept in a database and were not written by anyone. An address is mapped to
text by a function that can be run backwards, so the text at an address is a
fact about arithmetic, not a record of an event. It was there before the program
ran and it will be there after.

**This is not the library at libraryofbabel.info.** The construction is the same
one Jonathan Basile described; the constants are different, so the addresses do
not match his and the pages are not the same pages.

## How it is processed

The alphabet is 29 characters — 26 letters, space, comma, period — and a page is
3200 of them, so a page is a number below 29³²⁰⁰.

**With an anchor.** The page that begins with the anchor and continues in blank
space is built directly, then run backwards through the function to recover its
address. That address is a real address in the library, and reading it forwards
returns the same page. Your word is not put there; it is found there.

**Without an anchor.** The key's seed is taken as the address, and the page is
read forwards.

Either way the address is split into hexagon, wall, shelf, volume and page in
the manner of the library, and the hexagon is named in base 36 — which, for a
number this size, runs to about three thousand characters. The full name goes
into the ledger. Only an abbreviation is shown on screen.

### On the constants

The mapping is `text = digits((A × address + C) mod 29³²⁰⁰)`, and it is
invertible because `A` has an inverse modulo the alphabet size. Two things about
`A` and `C` matter, and both were learned the hard way:

- They are the width of a full page. A short multiplier leaves almost every
  digit of a small address untouched, and two neighbouring addresses then read
  almost identically.
- Their digits carry no pattern. Building them from a formula stamps that
  formula's period onto every page in the library, and the text comes out
  visibly striped.

They are derived by hashing a fixed label, so they are written down rather than
drawn, and every copy of this program opens the same library.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `excerpt` | 240 | How much of the page becomes the material's text |

## Dependencies

None. Standard library only, and no network.

## Sources

The construction — an invertible mapping from address to text, with no storage
behind it — is Jonathan Basile's, published at
[libraryofbabel.info-algo](https://github.com/librarianofbabel/libraryofbabel.info-algo).
That repository states no licence, so no code was copied; this is written from
the description. The idea is Borges's.
