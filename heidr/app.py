from dataclasses import replace
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static

from heidr import capabilities, config, keymap, registry, rite, session
from heidr.contracts import Context
from heidr.events import Bus
from heidr.ledger import Ledger
from heidr.strings import BANNER_BLOCK, BANNER_PLAIN, NAME, SLOGANS, text
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

MIN_COLUMNS = 40
MIN_ROWS = 12
THEMES = Path(__file__).resolve().parent / "ui"


class HeidrApp(App):
    edit_mode = reactive("NORMAL")

    def __init__(self, settings=None, user_dir=None, terminal=None, capabilities_found=None):
        self.settings = settings or config.load()
        self.capabilities_found = capabilities_found
        self.user_dir = user_dir or config.USER_DIR
        self.terminal = terminal or capabilities.detect_terminal()
        self.keymap = keymap.load(self.user_dir)
        self.leader = keymap.leader_key(self.user_dir)
        self.leader_pending = False
        self.bus = Bus()
        self.ledger = Ledger(self.settings.get("ledger.path", "~/.local/share/heidr/ledger"))
        registry.discover(self.user_dir / "modules")
        # Probing the network and the radio takes time, so capabilities stay
        # empty until :checkhealth or a draw asks for them.
        self.context = Context(config=self.settings, emit=self.bus.emit)
        super().__init__(css_path=THEMES / f"theme_{self.terminal.theme}.tcss")

    def probe(self) -> Context:
        found = self.capabilities_found
        if found is None:
            found = capabilities.detect_capabilities(self.settings)
        self.context = replace(self.context, capabilities=found)
        return self.context

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._splash(), id="body")
            yield StatusLine(id="status")
            yield CommandLine(id="cmdline")

    def on_mount(self) -> None:
        status = self.query_one(StatusLine)
        status.mode = self.edit_mode
        status.volume = self.settings.get("audio.volume", 0.6)
        status.provider = self.settings.get("llm.provider", "")

    def watch_edit_mode(self, value: str) -> None:
        if self.is_mounted:
            self.query_one(StatusLine).mode = value

    # Input

    def on_key(self, event) -> None:
        event.stop()
        if self.edit_mode == "COMMAND":
            self._type_into_command_line(event, self._run_command)
        elif self.edit_mode == "INSERT":
            self._type_into_command_line(event, self._accept_question)
        else:
            self._handle_normal_key(event)

    def _handle_normal_key(self, event) -> None:
        if self.leader_pending:
            self.leader_pending = False
            self._act(self.keymap["leader"].get(event.key, ""))
            return
        if event.key == self.leader:
            self.leader_pending = True
            return
        self._act(self.keymap["normal"].get(event.key, ""))

    def _type_into_command_line(self, event, accept) -> None:
        line = self.query_one(CommandLine)
        if event.key == "escape":
            line.close()
            self.edit_mode = "NORMAL"
        elif event.key == "enter":
            accept(line.close())
            self.edit_mode = "NORMAL"
        elif event.key == "backspace":
            line.backspace()
        elif event.character and event.character.isprintable():
            line.type(event.character)

    def _accept_question(self, question: str) -> None:
        if not question.strip():
            return
        line = self.query_one(CommandLine)
        try:
            drawn = session.perform(self.probe(), self.ledger, question)
        except session.AlreadyAsked as repeated:
            line.say(text("error.repeat_question", entry=repeated.entry.identifier))
            return
        except rite.NothingAvailable:
            line.say(text("error.no_modules"))
            return

        status = self.query_one(StatusLine)
        status.rite = str(drawn.rite)
        self.query_one("#body", Static).update(self._draw_text(drawn))
        if drawn.rite.silent:
            line.say(text("status.silent"))

    def _draw_text(self, drawn) -> str:
        heading = f"{drawn.entry.identifier}  {drawn.rite}"
        return f"{heading}\n\n{drawn.body()}"

    def _act(self, action: str) -> None:
        handler = getattr(self, f"do_{action}", None)
        if handler is not None:
            handler()

    # Actions

    def do_command_line(self) -> None:
        self.query_one(CommandLine).open(":")
        self.edit_mode = "COMMAND"

    def do_ask(self) -> None:
        self.query_one(CommandLine).open("> ")
        self.edit_mode = "INSERT"

    def do_quit(self) -> None:
        self.exit()

    def do_help(self) -> None:
        self.query_one("#body", Static).update(self._help_text())

    def do_mute(self) -> None:
        status = self.query_one(StatusLine)
        status.muted = not status.muted

    def do_volume_up(self) -> None:
        self._change_volume(0.05)

    def do_volume_down(self) -> None:
        self._change_volume(-0.05)

    def _change_volume(self, step: float) -> None:
        status = self.query_one(StatusLine)
        status.volume = min(1.0, max(0.0, status.volume + step))
        self.settings.set("audio.volume", round(status.volume, 2))

    # Commands

    def _run_command(self, typed: str) -> None:
        name, _, argument = typed.strip().partition(" ")
        line = self.query_one(CommandLine)
        if name in ("q", "quit"):
            self.exit()
        elif name == "help":
            self.do_help()
        elif name == "mute":
            self.do_mute()
        elif name == "vol":
            self._set_volume(argument, line)
        elif name == "set":
            self._set_option(argument, line)
        elif name:
            line.say(f"Unknown command: {name}. Type :help for the list.")

    def _set_volume(self, argument: str, line: CommandLine) -> None:
        if not argument.isdigit():
            line.say("Volume takes a number from 0 to 100, as in :vol 40.")
            return
        status = self.query_one(StatusLine)
        status.volume = min(100, int(argument)) / 100
        self.settings.set("audio.volume", round(status.volume, 2))

    def _set_option(self, argument: str, line: CommandLine) -> None:
        option, separator, value = argument.partition("=")
        if not separator:
            line.say("Setting an option needs a value, as in :set ui.theme=tty.")
            return
        self.settings.set(option.strip(), value.strip())
        line.say(f"{option.strip()} is now {value.strip()}.")

    # Layout

    def on_resize(self, event) -> None:
        body = self.query_one("#body", Static)
        if event.size.width < MIN_COLUMNS or event.size.height < MIN_ROWS:
            body.update(text("error.small_terminal", cols=MIN_COLUMNS, rows=MIN_ROWS))
        else:
            body.update(self._splash())

    def _splash(self) -> str:
        import random

        banner = BANNER_BLOCK if self.terminal.glyphs != "ascii" else BANNER_PLAIN
        return f"{banner}\n\n{random.choice(SLOGANS)}"

    def _help_text(self) -> str:
        lines = [f"{NAME} keys", ""]
        for section in ("normal", "insert", "leader"):
            lines.append(section)
            for key, action in sorted(self.keymap[section].items()):
                lines.append(f"  {key:<16} {action}")
            lines.append("")
        lines.append("Commands: :q :help :vol N :mute :set option=value")
        return "\n".join(lines)
