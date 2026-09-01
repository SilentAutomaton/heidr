import os
import shutil
import socket
from dataclasses import dataclass

from heidr.contracts import CAPABILITIES, Unavailable

GLYPH_LEVELS = ("ascii", "box", "blocks", "braille")

# Terminals that draw box and block glyphs but have no braille in the console
# font. TERM=linux is the bare virtual console.
BLOCK_ONLY_TERMS = ("linux", "vt100", "vt220", "ansi", "dumb")


@dataclass(frozen=True)
class Terminal:
    colours: int
    glyphs: str
    graphics: str

    @property
    def theme(self) -> str:
        return "tty" if self.colours <= 16 else "full"


def detect_terminal(environ: dict[str, str] | None = None) -> Terminal:
    env = os.environ if environ is None else environ
    term = env.get("TERM", "")
    return Terminal(
        colours=_colours(env, term),
        glyphs=_glyphs(env, term),
        graphics=_graphics(env, term),
    )


def _colours(env: dict[str, str], term: str) -> int:
    if env.get("COLORTERM", "") in ("truecolor", "24bit"):
        return 16777216
    if "256" in term or "direct" in term:
        return 256
    if term in ("", "dumb"):
        return 8
    return 16


def _glyphs(env: dict[str, str], term: str) -> str:
    if term.startswith(BLOCK_ONLY_TERMS):
        return "blocks" if term != "dumb" else "ascii"
    charset = (env.get("LC_ALL") or env.get("LC_CTYPE") or env.get("LANG") or "").lower()
    if "utf-8" not in charset and "utf8" not in charset:
        return "ascii"
    return "braille"


def _graphics(env: dict[str, str], term: str) -> str:
    if env.get("TERM_PROGRAM") == "WezTerm" or term.startswith("xterm-kitty"):
        return "kitty"
    if term.startswith(("xterm", "mlterm", "foot")) and "KITTY_WINDOW_ID" not in env:
        return "sixel"
    return "none"


def detect_capabilities(timeout: float = 0.4) -> frozenset[str]:
    """What this machine can do right now.

    Only the things that can be answered by looking. Whether a language model or
    a speech provider really works is settled by building one, not by reading a
    name out of the configuration, so those two are added later by the app.
    """
    found = set()
    if _network_reachable(timeout):
        found.add("net")
    if _radio_present():
        found.add("sdr")
    if _audio_present():
        found.add("audio")
    return frozenset(found & set(CAPABILITIES))


def provider(make, settings, capability: str, allowed=None):
    """Build a provider, or return nothing at all.

    A provider that cannot be built is not a provider: the capability is granted
    by building one, so a module that needs it is never handed something that
    does not work. An explicit capability set is the whole truth, which is how a
    test keeps the program away from a real daemon.
    """
    if allowed is not None and capability not in allowed:
        return None
    try:
        built = make(settings)
    except Unavailable:
        return None
    if hasattr(built, "available") and not built.available():
        return None
    return built


def with_providers(found: frozenset[str], llm_provider, stt_provider) -> frozenset[str]:
    found = set(found) - {"llm", "stt"}
    if llm_provider is not None:
        found.add("llm")
    if stt_provider is not None:
        found.add("stt")
    return frozenset(found)


def _network_reachable(timeout: float) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
        return True
    except OSError:
        return False


def _radio_present() -> bool:
    if not shutil.which("rtl_test"):
        return False
    devices = "/sys/bus/usb/devices"
    return any(_is_rtl_device(entry) for entry in _listdir(devices))


def _is_rtl_device(path: str) -> bool:
    try:
        with open(f"{path}/idVendor") as handle:
            return handle.read().strip() == "0bda"
    except OSError:
        return False


def _listdir(root: str) -> list[str]:
    try:
        return [f"{root}/{name}" for name in os.listdir(root)]
    except OSError:
        return []


def _audio_present() -> bool:
    try:
        import sounddevice
    except Exception:
        return False
    try:
        return any(device["max_output_channels"] > 0 for device in sounddevice.query_devices())
    except Exception:
        return False
