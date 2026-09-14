import argparse
import random
import sys

import tomli_w

from heidr import __version__, config
from heidr.strings import BANNER_BLOCK, BANNER_PLAIN, NAME, SLOGANS, text


def splash(block_glyphs: bool = True) -> str:
    banner = BANNER_BLOCK if block_glyphs else BANNER_PLAIN
    return f"{banner}\n\n{random.choice(SLOGANS)}"


def self_check(settings) -> int:
    """What works on this machine, without starting the interface."""
    from heidr import capabilities, health, llm, registry, stt
    from heidr.contracts import Context
    from heidr.ledger import Ledger

    registry.discover(config.USER_DIR / "modules")
    # The providers are built here for the same reason the interface builds
    # them: whether a model or a recogniser really answers cannot be read out
    # of the configuration.
    provider = capabilities.provider(llm.build, settings, "llm")
    listener = capabilities.provider(stt.build, settings, "stt")
    context = Context(
        config=settings,
        capabilities=capabilities.with_providers(capabilities.detect_capabilities(), provider, listener),
        llm=provider,
        stt=listener,
    )
    ledger = Ledger(settings.get("ledger.path", "~/.local/share/heidr/ledger"))
    print(health.as_text(health.report(context, capabilities.detect_terminal(), ledger)))

    undocumented = _undocumented()
    for line in undocumented:
        print(f"- documentation  {line}")
    return 1 if undocumented else 0


def _undocumented() -> list[str]:
    """Whether the repository documents every module.

    An installed copy carries no repository — neither a built binary nor a
    wheel ships `tools/` — so there is nothing to check and nothing to complain
    about. The question belongs to the source tree.
    """
    try:
        from tools.check_docs import complaints
    except ImportError:
        return []

    return complaints()


def as_value(written: str):
    """A setting as a shell wrote it, read back as what it is.

    Everything arrives from a command line as text, and a thread count stored
    as "4" is read back as a string the next time the program starts.
    """
    lowered = written.strip().lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    for kind in (int, float):
        try:
            return kind(written)
        except ValueError:
            continue
    return written


def apply_settings(settings, pairs: list[str]) -> int:
    """Write settings from the command line, which is how an installer finishes.

    Nothing is saved until every pair is understood: half a configuration is
    harder to undo than none.
    """
    wanted = []
    for pair in pairs:
        key, sign, value = pair.partition("=")
        if not sign:
            print(text("config.not_a_pair", pair=pair), file=sys.stderr)
            return 1
        if settings.get(key.strip()) is None and not _known(key.strip()):
            print(text("config.unknown_key", name=key.strip()), file=sys.stderr)
            return 1
        wanted.append((key.strip(), as_value(value)))

    for key, value in wanted:
        settings.set(key, value)
    print(text("status.saved", path=config.save(settings)))
    return 0


def _known(dotted: str) -> bool:
    # Module settings are declared by the modules themselves rather than by the
    # defaults, so `modules.fm_voice.stops` is a name the defaults never hold.
    return dotted.startswith("modules.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="heidr", description=f"{NAME} terminal oracle")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--splash", action="store_true", help="print the wordmark and exit")
    parser.add_argument("--print-config", action="store_true", help="print the merged configuration")
    parser.add_argument("--self-check", action="store_true", help="report what works here")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        dest="settings",
        help="write one setting and exit, as in --set stt.provider=whisper_cpp",
    )
    args = parser.parse_args(argv)

    if args.splash:
        print(splash())
        return 0

    copied = config.install_example()
    if copied:
        print(text("config.copied", path=copied))

    settings = config.load()

    if args.settings:
        return apply_settings(settings, args.settings)

    if args.print_config:
        print(tomli_w.dumps(settings.data).rstrip())
        return 0

    if args.self_check:
        return self_check(settings)

    from heidr.app import HeidrApp

    HeidrApp(settings=settings).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
