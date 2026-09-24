# The wordmark

`HEID//R` cut in runic letters: bone white, with the slashes in the blue green of
old ice. Under it runs a band of runes, the name `ᚺᛖᛁᚦᚱ` and then the Elder
Futhark in its three ættir, the way a runestone carries its text between two
lines. The slogan is spaced out underneath.

The blue green is reserved. In the interface it marks the sign and the answer and
nothing else; the animation behind them has a colour of its own, from the table
in `heidr/visuals/palette.py`. Reserved is not the same as only: those colours
are chosen to sit behind it rather than to compete with it.

| File | Size | Where it is used |
|---|---|---|
| `heidr.svg` / `heidr.png` | 1200×300 | The top of the README |
| `social.svg` / `social.png` | 1280×640 | GitHub's social preview |

## Colours


| Role | Value |
|---|---|
| Ground | `#0e1216` |
| Wordmark | `#e6e1d6` |
| Slashes, runes | `#3db4c8` |
| Band | `#2a6f7a` |
| Slogan | `#7c8895` |

## Rebuilding

```
./tools/make_brand.sh
```

The script fetches Norse by Joël Carrouché and Noto Sans Runic into
`~/.local/share/fonts/heidr-brand`, then renders both PNGs with `rsvg-convert`.
The fonts are not committed. Norse is free to use but not to redistribute, and
the repository does not modify either, so it has no business carrying them.
The licences are in [credits](../en/credits.md#fonts).

Edit the SVG, run the script, commit both. The PNGs are committed because
GitHub renders them everywhere, including in the social preview, where an SVG
is not accepted.

## The social preview

GitHub has no API for it. Upload `social.png` by hand at
**Settings → General → Social preview** on the repository page.
