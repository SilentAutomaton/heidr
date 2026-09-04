import shutil
from dataclasses import dataclass

from heidr import registry
from heidr.ledger import Ledger

OK, WARN, FAIL = "ok", "warn", "fail"
MARKS = {OK: "+", WARN: "~", FAIL: "-"}

RADIO_TOOLS = ("rtl_sdr", "rtl_fm", "rtl_power", "rtl_433", "dump1090")
STREAM_TOOLS = ("ffmpeg", "yt-dlp")


@dataclass(frozen=True)
class Check:
    name: str
    state: str
    detail: str

    def __str__(self) -> str:
        return f"{MARKS[self.state]} {self.name:<16} {self.detail}"


def report(ctx, terminal, ledger: Ledger | None = None) -> list[Check]:
    checks = [
        _terminal(terminal),
        _network(ctx),
        _radio(ctx),
        _tools(),
        _stream_tools(),
        _audio(),
        _llm(ctx),
        _speech(ctx),
    ]
    if ledger is not None:
        checks.append(_ledger(ledger))
    checks.extend(_modules(ctx))
    return checks


def _terminal(terminal) -> Check:
    detail = f"{terminal.colours} colours, {terminal.glyphs} glyphs, graphics {terminal.graphics}"
    state = OK if terminal.colours > 16 else WARN
    if state == WARN:
        detail += ". A bare console, so the plain theme is used."
    return Check("terminal", state, detail)


def _network(ctx) -> Check:
    if ctx.has("net"):
        return Check("network", OK, "reachable")
    return Check("network", WARN, "not reachable. The network modules stay out of the lottery.")


def _radio(ctx) -> Check:
    if ctx.has("sdr"):
        return Check("radio", OK, "an RTL-SDR device is present")
    return Check(
        "radio",
        WARN,
        "no RTL-SDR found. Plug in the dongle, then run :checkhealth again.",
    )


def _tools() -> Check:
    missing = [tool for tool in RADIO_TOOLS if shutil.which(tool) is None]
    if not missing:
        return Check("radio tools", OK, "all present")
    return Check(
        "radio tools",
        WARN,
        f"missing: {', '.join(missing)}. The modules that call them stay out of the lottery.",
    )


def _stream_tools() -> Check:
    missing = [tool for tool in STREAM_TOOLS if shutil.which(tool) is None]
    if not missing:
        return Check("stream tools", OK, "all present")
    return Check(
        "stream tools",
        WARN,
        f"missing: {', '.join(missing)}. The sources that listen over the network "
        "stay out of the lottery.",
    )


def _audio() -> Check:
    try:
        import sounddevice
    except Exception:
        return Check("audio", WARN, "sounddevice is not installed. The oracle runs silently.")
    try:
        outputs = [d for d in sounddevice.query_devices() if d["max_output_channels"] > 0]
    except Exception:
        outputs = []
    if outputs:
        return Check("audio", OK, f"{len(outputs)} output devices")
    return Check("audio", WARN, "no output device. The oracle runs silently.")


def _llm(ctx) -> Check:
    if ctx.llm is not None:
        return Check("language model", OK, f"{ctx.llm.name}, {ctx.config.get('llm.model', '')}")
    return Check(
        "language model",
        WARN,
        "no provider. Set llm.provider and its base_url, or leave it: the readings "
        "that need no model still work.",
    )


def _speech(ctx) -> Check:
    if ctx.stt is not None:
        return Check("speech", OK, ctx.stt.name)
    return Check(
        "speech",
        WARN,
        "no provider. Set stt.provider and stt.model_path. Without it there is no "
        "voice input and no radio transcription.",
    )


def _ledger(ledger: Ledger) -> Check:
    entries = ledger.entries()
    if not ledger.chain_ok():
        return Check(
            "ledger",
            FAIL,
            f"the chain does not verify over {len(entries)} entries. An entry was edited by hand.",
        )
    return Check("ledger", OK, f"{len(entries)} entries, chain verifies")


def _modules(ctx) -> list[Check]:
    checks = []
    for slot in registry.SLOTS:
        ready = [name for name, module in registry.MODULES[slot].items() if module.available(ctx)]
        total = len(registry.MODULES[slot])
        state = OK if ready else FAIL
        detail = f"{len(ready)} of {total} usable"
        if not ready:
            detail += ". No rite can be drawn until one is. See :modules."
        checks.append(Check(f"slot {slot}", state, detail))
    return checks


def as_text(checks: list[Check]) -> str:
    return "\n".join(str(check) for check in checks)
