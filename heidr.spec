# PyInstaller recipe: one file, no Python and no dependencies to install.
#
#   pyinstaller heidr.spec
#
# The external programs stay external. rtl_fm, whisper-cli and the rest are run
# as subprocesses, so they are found on the path at run time or the capability
# is simply absent, exactly as with an ordinary install.
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Modules are found by walking the package, so every one of them has to be in
# the archive whether or not anything imports it by name.
hidden = collect_submodules("heidr")
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

analysis = Analysis(
    ["heidr/__main__.py"],
    pathex=[],
    binaries=[],
    datas=data,
    hiddenimports=hidden,
    excludes=["tkinter", "test", "unittest", "pytest"],
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
