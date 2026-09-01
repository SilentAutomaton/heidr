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
    from heidr import capabilities, health, registry
    from heidr.contracts import Context
    from heidr.ledger import Ledger
    from tools.check_docs import complaints

    registry.discover(config.USER_DIR / "modules")
    context = Context(config=settings, capabilities=capabilities.detect_capabilities())
    ledger = Ledger(settings.get("ledger.path", "~/.local/share/heidr/ledger"))
    print(health.as_text(health.report(context, capabilities.detect_terminal(), ledger)))

    undocumented = complaints()
    for line in undocumented:
        print(f"- documentation  {line}")
    return 1 if undocumented else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="heidr", description=f"{NAME} terminal oracle")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--splash", action="store_true", help="print the wordmark and exit")
    parser.add_argument("--print-config", action="store_true", help="print the merged configuration")
    parser.add_argument("--self-check", action="store_true", help="report what works here")
    args = parser.parse_args(argv)

    if args.splash:
        print(splash())
        return 0

    copied = config.install_example()
    if copied:
        print(text("config.copied", path=copied))

    settings = config.load()

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
