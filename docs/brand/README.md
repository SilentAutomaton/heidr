# The wordmark

White `HEID`, orange slashes, white `R`, and the slogan spaced out underneath.

The orange is reserved. In the interface it marks the sign and the answer and
nothing else; the animation behind them has a colour of its own, from the table
in `heidr/visuals/palette.py`. Reserved is not the same as only: those colours
are chosen to sit behind the orange rather than to compete with it.

| File | Size | Where it is used |
|---|---|---|
| `heidr.svg` / `heidr.png` | 1200×300 | The top of the README |
| `social.svg` / `social.png` | 1280×640 | GitHub's social preview |

## Colours

Taken from the dark theme of the project status page.

| Role | Value |
|---|---|
| Ground | `#0e1216` |
| Wordmark | `#e4e9ef` |
| Slashes | `#f0a63a` |
| Slogan | `#7c8895` |

## Rebuilding

```
./tools/make_brand.sh
```

The script fetches IBM Plex Sans Condensed Bold and IBM Plex Mono, both
OFL-1.1, into `~/.local/share/fonts/heidr-brand`, then renders both PNGs with
`rsvg-convert`. The fonts are not committed: the repository does not modify
them, so it has no business carrying them.

Edit the SVG, run the script, commit both. The PNGs are committed because
GitHub renders them everywhere, including in the social preview, where an SVG
is not accepted.

## The social preview

GitHub has no API for it. Upload `social.png` by hand at
**Settings → General → Social preview** on the repository page.
