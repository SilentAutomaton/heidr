#!/bin/sh
# Build the released Linux binary. It is built in a container rather than on
# the machine: a PyInstaller binary carries the C library it was linked
# against, so one built on a rolling distribution runs on that distribution
# and nowhere else. Debian bullseye is old enough to reach Ubuntu 20.04 and
# everything since. The other binaries are built by
# .github/workflows/build-binaries.yml or by hand on their own systems:
# PyInstaller does not cross-build.
set -e
cd "$(dirname "$0")/.."

mkdir -p dist

docker run --rm -v "$PWD:/src" -w /src python:3.12-bullseye sh -c '
    set -e
    python -m venv /tmp/build-env
    /tmp/build-env/bin/pip install --quiet pyinstaller ".[audio,effects]"
    /tmp/build-env/bin/pyinstaller --clean --distpath /tmp/dist --workpath /tmp/work heidr.spec
    cp /tmp/dist/heidr dist/heidr-linux-x86_64
'
echo "dist/heidr-linux-x86_64"

cd dist
sha256sum heidr-* >SHA256SUMS
cat SHA256SUMS
