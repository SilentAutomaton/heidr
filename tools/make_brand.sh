#!/bin/sh
# Render the wordmark. The letters are Norse by Joël Carrouché, free for any use
# but not to be redistributed, and the runes are Noto Sans Runic, OFL-1.1. Both
# are fetched here rather than committed: the first may not be shared, and a
# repository is a bad place to keep a font it does not modify anyway.
set -e
work="${TMPDIR:-/tmp}/heidr-brand"
fonts="$HOME/.local/share/fonts/heidr-brand"

if [ ! -f "$fonts/Norse-Bold.otf" ] || [ ! -f "$fonts/NotoSansRunic-Regular.ttf" ]; then
    mkdir -p "$work" "$fonts"
    curl -sL -o "$work/norse.zip" https://www.1001fonts.com/download/norse.zip
    unzip -oq "$work/norse.zip" -d "$work/norse"
    cp "$work/norse/Norse.otf" "$work/norse/Norse-Bold.otf" "$fonts/"
    curl -sL -o "$fonts/NotoSansRunic-Regular.ttf" \
        https://github.com/google/fonts/raw/main/ofl/notosansrunic/NotoSansRunic-Regular.ttf
    fc-cache -f "$fonts" >/dev/null
fi

cd "$(dirname "$0")/.."
rsvg-convert -w 1200 -h 300 docs/brand/heidr.svg -o docs/brand/heidr.png
rsvg-convert -w 1280 -h 640 docs/brand/social.svg -o docs/brand/social.png
echo "docs/brand/heidr.png docs/brand/social.png"
