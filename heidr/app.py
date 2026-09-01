import threading
from dataclasses import replace
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Static

from heidr import audio, capabilities, config, keymap, llm, mic, registry, rite, session, stt
from heidr.contracts import Context, Unavailable
from heidr.events import Bus
from heidr.ledger import Ledger
from heidr.strings import BANNER_BLOCK, BANNER_PLAIN, NAME, SLOGANS, text
from heidr.ui import browser
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

def _typed(value: str):
    """Read what was typed as the kind of value it looks like."""
    lowered = value.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            continue
    return value


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
        self.view = "rite"
        self.cursor = 0
        self.rows: list[tuple[str, str]] = []
        self.bus = Bus()
        self.levels = audio.Levels.from_config(self.settings)
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

        # A provider that cannot be built is not a provider, so the modules
        # that need one drop out of the lottery instead of failing halfway
        # through a rite.
        provider = None
        if "llm" in found:
            try:
                provider = llm.build(self.settings)
            except Unavailable:
                found = found - {"llm"}

        listener = None
        if "stt" in found:
            try:
                listener = stt.build(self.settings)
            except Unavailable:
                listener = None
            if listener is None or not listener.available():
                listener = None
                found = found - {"stt"}

        self.context = replace(self.context, capabilities=found, llm=provider, stt=listener)
        return self.context

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self._splash(), id="body")
            yield Container(id="visual")
            yield StatusLine(id="status")
            yield CommandLine(id="cmdline")

    def on_mount(self) -> None:
        self.show_visual("idle")
        status = self.query_one(StatusLine)
        status.mode = self.edit_mode
        status.volume = self.levels.volume
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
            self._handle_insert_key(event)
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

    def _handle_insert_key(self, event) -> None:
        action = self.keymap["insert"].get(event.key, "")
        if action:
            self._act(action)
            return
        self._type_into_command_line(event, self._accept_question)

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
        self.show_visual("waterfall")
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
        self.show_visual("idle")
        self.query_one("#body", Static).update(self._draw_text(drawn))
        if drawn.rite.silent:
            line.say(text("status.silent"))

    # Visualisations

    def show_visual(self, name: str) -> None:
        chosen = registry.pick_visual(name, self.terminal.glyphs)
        pane = self.query_one("#visual", Container)
        pane.remove_children()
        self.bus.clear()
        if chosen is None:
            if name != "idle":
                self.show_visual("idle")
            return

        widget = chosen.widget()
        pane.mount(widget)
        self.bus.subscribe(chosen.event, lambda payload: self._forward(widget, payload))

    def _forward(self, widget, payload) -> None:
        # Captures run in worker threads, and a widget may only be touched from
        # the one the interface lives on.
        if threading.current_thread() is threading.main_thread():
            widget.feed(payload)
        else:
            self.call_from_thread(widget.feed, payload)

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

    def do_voice_input(self) -> None:
        context = self.probe()
        if not mic.available(context):
            self.query_one(CommandLine).say(text("error.no_voice"))
            return
        self.run_worker(lambda: self._dictate(context), thread=True)

    def _dictate(self, context) -> None:
        line = self.query_one(CommandLine)
        heard = mic.dictate(context, lambda said: self.call_from_thread(self._show_dictation, said))
        if heard:
            self.call_from_thread(line.type, "")

    def _show_dictation(self, said: str) -> None:
        line = self.query_one(CommandLine)
        line.buffer = said

    def do_normal_mode(self) -> None:
        self.query_one(CommandLine).close()
        self.edit_mode = "NORMAL"

    def do_quit(self) -> None:
        self.exit()

    def do_help(self) -> None:
        self.view = "rite"
        self.query_one("#body", Static).update(self._help_text())

    def do_modules(self) -> None:
        self._open_browser("modules", browser.module_rows(self.probe()), text("empty.modules"))

    def do_settings(self) -> None:
        self._open_browser("settings", browser.setting_rows(self.settings), text("empty.settings"))

    def _open_browser(self, view: str, rows, empty: str) -> None:
        self.view = view
        self.rows = rows
        self.cursor = min(self.cursor, max(0, len(rows) - 1))
        self.empty = empty
        self._show_rows()

    def _show_rows(self) -> None:
        self.query_one("#body", Static).update(
            browser.render(self.rows, self.cursor, getattr(self, "empty", ""))
        )

    def do_line_down(self) -> None:
        self._move_cursor(1)

    def do_line_up(self) -> None:
        self._move_cursor(-1)

    def _move_cursor(self, step: int) -> None:
        if self.view not in ("modules", "settings") or not self.rows:
            return
        self.cursor = max(0, min(len(self.rows) - 1, self.cursor + step))
        self._show_rows()

    def do_choose(self) -> None:
        if self.view == "modules":
            self._toggle_module()
        elif self.view == "settings":
            self._edit_setting()

    def _toggle_module(self) -> None:
        key, _line = self.rows[self.cursor]
        self.settings.set(key, not self.settings.get(key, True))
        self.rows = browser.module_rows(self.context)
        self._show_rows()

    def _edit_setting(self) -> None:
        key, _line = self.rows[self.cursor]
        line = self.query_one(CommandLine)
        line.open(":")
        line.buffer = f"set {key}={self.settings.get(key)}"
        self.edit_mode = "COMMAND"

    def do_mute(self) -> None:
        self.levels.muted = not self.levels.muted
        self.query_one(StatusLine).muted = self.levels.muted

    def do_volume_up(self) -> None:
        self._change_volume(0.05)

    def do_volume_down(self) -> None:
        self._change_volume(-0.05)

    def _change_volume(self, step: float) -> None:
        if step > 0:
            self.levels.louder(step)
        else:
            self.levels.quieter(-step)
        self._show_volume()

    def _show_volume(self) -> None:
        self.query_one(StatusLine).volume = self.levels.volume
        self.settings.set("audio.volume", self.levels.volume)

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
        elif name == "modules":
            self.do_modules()
        elif name == "settings":
            self.do_settings()
        elif name in ("w", "write"):
            line.say(text("status.saved", path=config.save(self.settings)))
        elif name:
            line.say(f"Unknown command: {name}. Type :help for the list.")

    def _set_volume(self, argument: str, line: CommandLine) -> None:
        if not argument.isdigit():
            line.say("Volume takes a number from 0 to 100, as in :vol 40.")
            return
        self.levels.volume = min(100, int(argument)) / 100
        self._show_volume()

    def _set_option(self, argument: str, line: CommandLine) -> None:
        option, separator, value = argument.partition("=")
        if not separator:
            line.say("Setting an option needs a value, as in :set ui.theme=tty.")
            return
        self.settings.set(option.strip(), _typed(value.strip()))
        line.say(f"{option.strip()} is now {value.strip()}.")
        if self.view == "settings":
            self.do_settings()
        elif self.view == "modules":
            self.do_modules()

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
