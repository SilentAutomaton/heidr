# PyInstaller recipe: one file, no Python and no dependencies to install.
#
#   pyinstaller heidr.spec
#
# The external programs stay external. rtl_fm, whisper-cli and the rest are run
# as subprocesses, so they are found on the path at run time or the capability
# is simply absent, exactly as with an ordinary install.
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


def submodules(package):
    """Every module under the package, found on disk rather than by importing.

    PyInstaller's own collector imports each package to read its `__path__`, and
    importing `heidr.stt` pulls numpy in. That makes the build depend on the
    build machine being able to run the code it is packaging, which is not true
    of the wine container the Windows binary comes out of.
    """
    root = Path(package)
    found = [package]
    for path in sorted(root.rglob("*.py")):
        parts = path.relative_to(root).with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if parts:
            found.append(".".join((package,) + parts))
    return found


# Modules are found by walking the package at run time, so every one of them has
# to be in the archive whether or not anything imports it by name.
hidden = submodules("heidr")
data = [
    ("heidr/data", "heidr/data"),
    ("heidr/ui", "heidr/ui"),
    # config.install_example() looks one directory above the package, which in
    # the bundle is the root of the unpacked tree.
    ("config.example.toml", "."),
    ("keymap.example.toml", "."),
]

for package in ("textual", "rich", "terminaltexteffects"):
    found_data, _binaries, found_hidden = collect_all(package)
    data += found_data
    hidden += found_hidden

# A collector walking a package also picks up files that are not importable
# names — rich ships one called `unicode10-0-0.py` — and PyInstaller refuses
# the whole build over it rather than skipping it.
hidden = [name for name in hidden if all(part.isidentifier() for part in name.split("."))]

analysis = Analysis(
    ["heidr/__main__.py"],
    pathex=[],
    binaries=[],
    datas=data,
    hiddenimports=hidden,
    excludes=["tkinter", "test", "unittest", "pytest", "tools"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="heidr",
    console=True,
    strip=False,
    upx=False,
)
