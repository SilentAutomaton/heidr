#!/bin/sh
# Render the wordmark. The fonts are IBM Plex Sans Condensed Bold and IBM Plex
# Mono, both OFL-1.1; they are fetched here rather than committed, because a
# repository is a bad place to keep a font it does not modify.
set -e
work="${TMPDIR:-/tmp}/heidr-brand"
fonts="$HOME/.local/share/fonts/heidr-brand"
plex=https://github.com/IBM/plex/releases/download

if [ ! -f "$fonts/IBMPlexSansCondensed-Bold.otf" ]; then
    mkdir -p "$work" "$fonts"
    curl -sL -o "$work/condensed.zip" "$plex/%40ibm%2Fplex-sans-condensed%401.1.0/ibm-plex-sans-condensed.zip"
    curl -sL -o "$work/mono.zip" "$plex/%40ibm%2Fplex-mono%401.1.0/ibm-plex-mono.zip"
    unzip -oq "$work/condensed.zip" -d "$work"
    unzip -oq "$work/mono.zip" -d "$work"
    cp "$work/ibm-plex-sans-condensed/fonts/complete/otf/IBMPlexSansCondensed-Bold.otf" "$fonts/"
    cp "$work/ibm-plex-mono/fonts/complete/otf/IBMPlexMono-Regular.otf" "$fonts/"
    fc-cache -f "$fonts" >/dev/null
fi

cd "$(dirname "$0")/.."
rsvg-convert -w 1200 -h 300 docs/brand/heidr.svg -o docs/brand/heidr.png
rsvg-convert -w 1280 -h 640 docs/brand/social.svg -o docs/brand/social.png
echo "docs/brand/heidr.png docs/brand/social.png"
