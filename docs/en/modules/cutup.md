# cutup — reading

## What it does

Cuts the material into pieces and puts them back in another order. No language
model is involved at any point.

## Where the data comes from

Only the material the world module returned, plus the question, which is used
solely to seed the shuffle.

## How it is processed

1. The material is split into words.
2. One of two methods is chosen: the straight cut, which slices the text into
   fixed-length pieces and shuffles them, or the fold-in, which folds the second
   half of the text into the first.
3. The first few resulting lines are yielded, one at a time.

Nothing is added that was not already there. Every word in the answer came out
of the material, which is why this reading can be trusted even when everything
else is switched off.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `max_cut` | 4 | Words per piece |
| `lines` | 6 | How many lines to yield |

## Dependencies

None. Standard library only.

## Sources

The method is the one Brion Gysin and William Burroughs described. The two
variants and the idea of making the cut length a parameter follow
[zachng1/cutup](https://github.com/zachng1/cutup); the implementation here is
our own.
