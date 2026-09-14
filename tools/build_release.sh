#!/bin/sh
# Build the released binaries. Both are built in containers rather than on the
# machine: a PyInstaller binary carries the C library it was linked against, so
# one built on a rolling distribution runs on that distribution and nowhere
# else. Debian bullseye is old enough to reach Ubuntu 20.04 and everything since.
set -e
cd "$(dirname "$0")/.."

linux_image=python:3.12-bullseye
# Not 3.12: PyInstaller's isolated helper subprocess dies under that image.
windows_image=tobix/pywine:3.11
wanted="${1:-all}"

build_linux() {
    docker run --rm -v "$PWD:/src" -w /src "$linux_image" sh -c '
        set -e
        python -m venv /tmp/build-env
        /tmp/build-env/bin/pip install --quiet pyinstaller ".[audio,effects]"
        /tmp/build-env/bin/pyinstaller --clean --distpath /tmp/dist --workpath /tmp/work heidr.spec
        cp /tmp/dist/heidr dist/heidr-linux-x86_64
    '
    echo "dist/heidr-linux-x86_64"
}

# wine is the only way to a Windows binary from here, and it is the part that
# may not work. A failure is reported and the release goes out without it.
build_windows() {
    docker run --rm -v "$PWD:/src" -w /src -e WINEDEBUG=-all "$windows_image" sh -c '
        set -e
        # The prefix is created fresh for every container, and PyInstaller runs
        # its collectors in subprocesses. Starting those while wineboot is still
        # settling kills them, which looks like a PyInstaller fault and is not.
        wineboot -u >/dev/null 2>&1 || true
        wineserver -w
        wine python -m pip install --quiet pyinstaller ".[audio,effects]"
        wine python -m PyInstaller --clean --distpath /tmp/dist --workpath /tmp/work heidr.spec
        cp /tmp/dist/heidr.exe dist/heidr-windows-x86_64.exe
    ' || return 1
    echo "dist/heidr-windows-x86_64.exe"
}

mkdir -p dist

case "$wanted" in
    all | linux) build_linux ;;
esac

case "$wanted" in
    all | windows)
        build_windows || echo "The Windows build failed. The release goes out without it." >&2
        ;;
esac

cd dist
rm -f SHA256SUMS
sha256sum heidr-linux-x86_64 heidr-windows-x86_64.exe 2>/dev/null >SHA256SUMS || true
cat SHA256SUMS
