import random
import sys
import threading
from dataclasses import replace
from pathlib import Path

from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static

from heidr import audio, capabilities, config, health, keymap, llm, mic, registry, rite, session, stt
from heidr.contracts import Cancelled, Context, Unavailable
from heidr.events import Bus
from heidr.history import History
from heidr.ledger import Ledger
from heidr.strings import NAME, SLOGANS, text
from heidr.ui import browser
from heidr.ui import mark, panel, prompt, stages
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine
from heidr.visuals.canvas import Canvas

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
# Drawn by lot, like everything else here. The fallback is fixed so that a
# missing animation cannot send the chooser round in circles.
IDLE_POOL = ("plasma", "life", "rain", "starfield", "moon")
IDLE = "plasma"
# The status line and the command line, which never change height, and the
# blank row above and below the panel. The stylesheets must agree, and a test
# says so.
CHROME_ROWS = 2
PANEL_PADDING = 2
# The spinner runs in braille where the terminal draws braille and in plain
# strokes where it does not: the same ladder as everything else here.
SPINNERS = {"braille": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏", "ascii": "|/-\\"}
SPIN_HZ = 10
SLOTS = 3
TRAIL = {"blocks": " \u203a ", "braille": " \u203a ", "box": " > ", "ascii": " > "}

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
        self.views = ["menu"]
        # Rows, cursor and empty text belong to the view that owns them, so
        # coming back from one list finds the other one where it was left.
        self.panes: dict[str, tuple[list[tuple[str, str]], str]] = {}
        self.cursors: dict[str, int] = {}
        self.body_text = ""
        self.tick = 0
        self.spin = 0
        self.progress: tuple[int, int] | None = None
        self.shown_title = ""
        self.bus = Bus()
        self.drawing = False
        self.stop_draw = threading.Event()
        self.asked = ""
        self.found = ("", "")
        self.said: list[str] = []
        self.notice = ""
        self.entry_id = ""
        self.stages: list[str] = []
        self.pinned = ""
        self.wanted: list[str] = []
        self._visual_off = None
        self.levels = audio.Levels.from_config(self.settings)
        # The garbled slogan is one more entry in the same pool, and it is only
        # in the pool where the terminal can really draw it.
        self.slogan = random.choice(SLOGANS)
        allowed = mark.can_garble(self.terminal.glyphs, self.settings)
        self.garbled = allowed and random.randrange(len(SLOGANS) + 1) == len(SLOGANS)
        self.ledger = Ledger(self.settings.get("ledger.path", "~/.local/share/heidr/ledger"))
        # Commands and questions are looked through apart, because they are not
        # the same kind of thing and mixing them makes both harder to find.
        kept = Path(self.settings.get("history.path", "~/.local/share/heidr")).expanduser()
        self.history = {"COMMAND": History(kept / "commands"), "INSERT": History(kept / "questions")}
        registry.discover(self.user_dir / "modules")
        # Probing the network and the radio takes time, so capabilities stay
        # empty until :checkhealth or a draw asks for them.
        self.context = Context(
            config=self.settings, emit=self.bus.emit, cancelled=self.stop_draw.is_set
        )
        super().__init__(css_path=THEMES / f"theme_{self.terminal.theme}.tcss")

    def probe(self) -> Context:
        allowed = self.capabilities_found
        found = allowed if allowed is not None else capabilities.detect_capabilities()

        # A provider that cannot be built is not a provider. The capability is
        # granted by building one, so a module that needs it is never handed a
        # provider that does not work.
        provider = capabilities.provider(llm.build, self.settings, "llm", allowed)
        listener = capabilities.provider(stt.build, self.settings, "stt", allowed)

        self.context = replace(
            self.context,
            capabilities=capabilities.with_providers(found, provider, listener),
            llm=provider,
            stt=listener,
            levels=self.levels,
            cancelled=self.stop_draw.is_set,
        )
        return self.context

    def compose(self) -> ComposeResult:
        # The animation fills the screen and the panel sits on top of it, so a
        # painter has the whole terminal to grow into and the text stays
        # readable on its own opaque ground.
        yield Canvas(self.terminal.glyphs, id="visual")
        with Vertical(id="frame"):
            yield Static(self._splash(), id="body")
        yield StatusLine(id="status")
        yield CommandLine(id="cmdline")

    def on_mount(self) -> None:
        self.show_idle()
        self.do_menu()
        status = self.query_one(StatusLine)
        status.mode = self.edit_mode
        status.volume = self.levels.volume
        status.provider = self.settings.get("llm.provider", "")
        self.query_one(CommandLine).accent = mark.accent(self.terminal.colours)
        # The panel is plain text, so the figure in it is moved by a timer of
        # its own rather than by the canvas.
        self.set_interval(1 / 3, self._breathe)
        self.set_interval(1 / SPIN_HZ, self._show_title)
        self._show_title()

    def _breathe(self) -> None:
        # The timer outlives the screen for a moment when the program leaves.
        if not self.query("#body"):
            return
        if self.view == "ask" or (self.view == "menu" and self.garbled):
            self.tick += 1
            self._render_body()

    def watch_edit_mode(self, value: str) -> None:
        line = self._status()
        if line is not None:
            line.mode = value

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
        if event.key in ("up", "ctrl+p"):
            line.buffer = self.history[self.edit_mode].back(line.buffer)
        elif event.key in ("down", "ctrl+n"):
            line.buffer = self.history[self.edit_mode].forward()
        elif event.key == "escape":
            line.close()
            self.edit_mode = "NORMAL"
        elif event.key == "enter":
            # Leave the line first, so a command that changes the mode wins.
            typed = line.close()
            self.history[self.edit_mode].add(typed)
            self.edit_mode = "NORMAL"
            accept(typed)
        elif event.key == "backspace":
            line.backspace()
        elif event.character and event.character.isprintable():
            line.type(event.character)
        if self.view == "ask":
            self._render_body()

    def _accept_question(self, question: str) -> None:
        if not question.strip():
            return
        line = self.query_one(CommandLine)
        if self.drawing:
            line.say(text("error.already_drawing"), level="error")
            return

        self._enter("rite")
        self.stages = []
        self.asked = question
        self.found = ("", "")
        self.said = []
        self.notice = ""
        self.entry_id = ""
        self._show_transcript()
        self.show_visual("waterfall")
        self._listen_to_the_draw()

        self.drawing = True
        self.stop_draw.clear()
        context = self.probe()
        spec, self.pinned = self.pinned, ""
        self.run_worker(lambda: self._draw(context, question, spec), thread=True, exclusive=True)

    def _draw(self, context, question: str, spec: str = "") -> None:
        """The whole rite, off the interface thread.

        Nothing here touches a widget: everything the reader sees arrives as an
        event and is put on screen by the handlers below.
        """
        try:
            drawn = session.perform(context, self.ledger, question, spec)
        except session.AlreadyAsked as repeated:
            self._finish(text("error.repeat_question", entry=repeated.entry.identifier))
        except rite.NothingAvailable:
            self._finish(text("error.no_modules"))
        except Cancelled:
            self._finish(text("status.cancelled"))
        except Unavailable as refused:
            # A module that cannot run is an ordinary outcome, not a crash.
            self._finish(str(refused))
        except Exception:
            # The class name of an exception is a fact about the code, not
            # about the reader's evening. The log keeps it; the screen does not.
            self._finish(text("error.draw_failed"))
        else:
            self.call_from_thread(self._drawn, drawn)

    def _finish(self, message: str) -> None:
        self.call_from_thread(self._draw_over, message)

    def _draw_over(self, message: str) -> None:
        self.drawing = False
        self.show_idle()
        self._announce(message)

    def _announce(self, message: str) -> None:
        """Say it where the reader is looking, and at the bottom as well.

        A rite that refused, stopped or said nothing is not a footnote. It goes
        into the panel, which is where the eye already is, and the bottom line
        repeats it for whoever is watching that instead.
        """
        self.notice = message
        self.query_one(CommandLine).say(message, level="error")
        self._render_body()

    def _drawn(self, drawn) -> None:
        self.drawing = False
        # A silent rite never announces its reading, so the finished bar is
        # filled from the rite itself: those three were drawn, whatever spoke.
        self.stages = [drawn.rite.question.name, drawn.rite.world.name, drawn.rite.reading.name]
        self.query_one(StatusLine).rite = str(drawn.rite)
        self._enter("rite")
        self.entry_id = drawn.entry.identifier
        self.found = (drawn.material.text, drawn.material.source)
        self.said = list(drawn.lines)
        self._show_transcript()
        self.show_idle()
        if drawn.rite.silent:
            self._announce(text("status.silent"))
        elif not drawn.lines:
            # A reading that yields nothing is not an error, but the screen
            # would otherwise look the same as one that simply finished.
            self._announce(text("status.no_answer"))

    def do_stop(self) -> None:
        if self.drawing:
            self.stop_draw.set()
            self.query_one(CommandLine).say(text("status.stopping"))
        else:
            self._back()

    # What the reader sees while it runs

    def _listen_to_the_draw(self) -> None:
        self.bus.subscribe("stage", lambda name: self._on_thread(self._stage, name))
        self.bus.subscribe("progress", lambda done: self._on_thread(self._progress, done))
        self.bus.subscribe("token", lambda line: self._on_thread(self._token, line))
        self.bus.subscribe("found", lambda material: self._on_thread(self._found, material))

    def _on_thread(self, handler, payload) -> None:
        if threading.current_thread() is threading.main_thread():
            handler(payload)
        else:
            self.call_from_thread(handler, payload)

    def _stage(self, name: str) -> None:
        """Each stage brings its own animation with it."""
        self.query_one(StatusLine).rite = str(name)
        module = self._module_named(str(name))
        if module is not None and module.name not in self.stages:
            self.stages.append(module.name)
            self.progress = None
            self._show_transcript()
        if module is not None:
            if module.visual:
                self.show_visual(module.visual)
            else:
                self.show_idle()

    def _progress(self, done) -> None:
        self.progress = tuple(done)

    def _title(self) -> str:
        """What the window is called, which is all you see when it is hidden."""
        if not self.drawing:
            return NAME
        frames = SPINNERS.get(self.terminal.glyphs, SPINNERS["ascii"])
        done, total = self.progress or (len(self.stages), SLOTS)
        stage = self.stages[-1] if self.stages else ""
        return f"{frames[self.spin % len(frames)]} {NAME} — {stage} {done}/{total}".rstrip()

    def _show_title(self) -> None:
        self.spin += 1
        wanted = self._title()
        if wanted == self.shown_title:
            return
        self.shown_title = wanted
        self.title = wanted
        # Textual does not promise to put the title on the window, so it is
        # written here as well. A console that does not know the sequence
        # ignores it, which is the behaviour wanted.
        sys.__stdout__.write(f"\x1b]2;{wanted}\x07")
        sys.__stdout__.flush()

    def on_unmount(self) -> None:
        # Nothing is left spinning in the window list after the program goes.
        self.shown_title = ""
        self.drawing = False
        self._show_title()

    def _module_named(self, name: str):
        # Stages announce themselves with extra words sometimes, so match the
        # first one: "babel 3f9a.1.2" is still babel.
        first = name.split()[0] if name.split() else name
        for slot in registry.SLOTS:
            found = registry.MODULES[slot].get(first)
            if found is not None:
                return found
        return None

    def _found(self, material) -> None:
        self.found = (material.text, material.source)
        self._show_transcript()

    def _token(self, line: str) -> None:
        self.said.append(str(line))
        self._show_transcript()

    def _show_transcript(self) -> None:
        self._render_body()

    def _show_text(self, body: str) -> None:
        self._enter("text")
        self.body_text = body
        self._render_body()

    @property
    def view(self) -> str:
        return self.views[-1]

    @property
    def rows(self) -> list[tuple[str, str]]:
        return self.panes.get(self.view, ([], ""))[0]

    @property
    def empty(self) -> str:
        return self.panes.get(self.view, ([], ""))[1]

    @property
    def cursor(self) -> int:
        return self.cursors.get(self.view, 0)

    @cursor.setter
    def cursor(self, value: int) -> None:
        self.cursors[self.view] = value

    def _enter(self, view: str) -> None:
        """Views stack, so Esc goes back the way it came in."""
        if view == self.views[0]:
            self.views = [view]
        elif view != self.view:
            self.views.append(view)
        self._show_path()

    def _back(self) -> bool:
        if len(self.views) == 1:
            return False
        self.views.pop()
        self._show_path()
        self._render_body()
        return True

    def _show_path(self) -> None:
        line = self._status()
        if line is not None:
            line.path = TRAIL[self.terminal.glyphs].join(self.views)

    def _status(self):
        # Timers and watchers outlive the screen for a moment when the program
        # leaves, and a missing status line then is ordinary rather than wrong.
        found = self.query("#status")
        return found.first(StatusLine) if found else None

    def _render_body(self, size=None) -> None:
        """The single place that decides what the body shows.

        Everything that changes the screen changes state and calls this. A
        resize calls it too, which is why a question and its answer survive one
        instead of being replaced by the splash.
        """
        size = size or self.size
        body = self.query_one("#body", Static)
        body.update(self._body_content(size))

    def _body_content(self, size) -> str:
        if size.width < MIN_COLUMNS or size.height < MIN_ROWS:
            return text("error.small_terminal", cols=MIN_COLUMNS, rows=MIN_ROWS)
        # One more line is kept for the "n of m" footer.
        room = size.height - CHROME_ROWS - PANEL_PADDING - 1
        if self.view == "menu":
            if not self.settings.get("ui.splash", True):
                return browser.render(self.rows, self.cursor, "", room)
            splash = self._splash()
            listed = browser.render(self.rows, self.cursor, "", room - splash.plain.count("\n") - 2)
            body = splash.copy()
            body.append(f"\n\n{listed}")
            return body
        if self.view.startswith("choose."):
            heading = text("prompt.choose", slot=self.view.split(".")[1])
            return f"{heading}\n\n{browser.render(self.rows, self.cursor, '', room - 2)}"
        if self.view in ("modules", "settings", "ledger"):
            return browser.render(self.rows, self.cursor, self.empty, room)
        if self.view == "ask":
            return prompt.panel(
                self.query_one(CommandLine).buffer,
                self.tick,
                size.width - PANEL_PADDING * 2,
                self.terminal.glyphs,
                text("hint.ask"),
            )
        if self.view == "text":
            return "\n".join(panel.wrap(self.body_text, panel.room(size.width)))
        if not self.asked:
            return self._splash()
        return self._rite_panel(panel.room(size.width))

    def _rite_panel(self, width: int):
        """The rite in labelled blocks: what was asked, what was found, what was said."""
        dim, accent = self._panel_styles()
        active = len(self.stages) - 1 if self.drawing else -1
        parts = [Text(stages.bar(self.stages, active, self.terminal.glyphs), dim)]
        if self.notice:
            parts.append(panel.notice(self.notice, accent))

        parts.append(panel.section("question", self.entry_id, panel.wrap(self.asked, width), dim))
        found, source = self.found
        if found:
            parts.append(panel.section("found", source, panel.shorten(found, width), dim))
        if self.said:
            reading = self.stages[-1] if len(self.stages) == SLOTS else ""
            answer = panel.wrap("\n".join(self.said), width)
            parts.append(panel.section("answer", reading, answer, dim))
        return panel.joined(parts)

    def _panel_styles(self) -> tuple[str, str]:
        # Dim text is not worth relying on in a console, so there the label is
        # simply plain and the accent carries the whole difference.
        dim = "dim" if self.terminal.colours > 16 else ""
        return dim, mark.accent(self.terminal.colours)

    # Visualisations

    def show_idle(self) -> None:
        self.show_visual(random.choice(IDLE_POOL))

    def show_visual(self, name: str) -> None:
        """Swap the painter on the one canvas; nothing is mounted or removed."""
        chosen = registry.pick_animation(name, self.terminal.glyphs)
        canvas = self.query_one("#visual", Canvas)
        # Only this canvas's own subscription goes; the draw's listeners stay.
        if self._visual_off is not None:
            self._visual_off()
            self._visual_off = None
        if chosen is None:
            if name != IDLE:
                self.show_visual(IDLE)
            return

        canvas.show(chosen.make(), chosen.fps)
        if chosen.event:
            self._visual_off = self.bus.subscribe(
                chosen.event, lambda payload: self._forward(canvas, payload)
            )

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
        self._enter("ask")
        line = self.query_one(CommandLine)
        line.open("> ")
        # The question is typed into the panel, so the bottom line stays quiet
        # instead of showing the same words twice.
        line.echo = False
        self.edit_mode = "INSERT"
        self._render_body()

    def do_voice_input(self) -> None:
        context = self.probe()
        if not mic.available(context):
            self.query_one(CommandLine).say(text("error.no_voice"), level="error")
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
        self._show_text(self._help_text())

    def do_checkhealth(self) -> None:
        checks = health.report(self.probe(), self.terminal, self.ledger)
        self._show_text(health.as_text(checks))

    def do_draw(self) -> None:
        # A draw needs a question, so asking for one is the whole of it.
        self.do_ask()

    def pin(self, spec: str) -> None:
        """Name the rite for the next draw instead of drawing one."""
        self.pinned = spec
        self.query_one(StatusLine).rite = spec
        self.do_ask()

    def do_compose(self) -> None:
        """Choose a rite one slot at a time, instead of naming it in one line."""
        self.wanted = []
        self._open_slot()

    def _open_slot(self) -> None:
        slot = registry.SLOTS[len(self.wanted)]
        self._open_browser(f"choose.{slot}", browser.slot_rows(slot, self.probe()), "")

    def _choose_slot(self) -> None:
        name, _line = self.rows[self.cursor]
        self.wanted.append(name)
        if len(self.wanted) < len(registry.SLOTS):
            self._open_slot()
            return
        # Back to where the command would have left us, by the same door.
        self.views = self.views[: self.views.index(f"choose.{registry.SLOTS[0]}")]
        self.pin(rite.SEPARATOR.join(self.wanted))

    def do_menu(self) -> None:
        self._open_browser("menu", browser.menu_rows(self.leader), "")

    def do_ledger(self) -> None:
        self._open_browser("ledger", browser.ledger_rows(self.ledger), text("empty.ledger"))

    def do_modules(self) -> None:
        self._open_browser("modules", browser.module_rows(self.probe()), text("empty.modules"))

    def do_settings(self) -> None:
        self._open_browser("settings", browser.setting_rows(self.settings), text("empty.settings"))

    def _open_browser(self, view: str, rows, empty: str) -> None:
        self._enter(view)
        self.panes[view] = (rows, empty)
        self.cursor = min(self.cursor, max(0, len(rows) - 1))
        self._show_rows()

    def _show_rows(self) -> None:
        self._render_body()

    def do_line_down(self) -> None:
        self._move_cursor(1)

    def do_line_up(self) -> None:
        self._move_cursor(-1)

    def do_page_down(self) -> None:
        self._move_cursor(self._room())

    def do_page_up(self) -> None:
        self._move_cursor(-self._room())

    def _room(self) -> int:
        # The same arithmetic the body uses, so a page is what is on screen.
        return max(1, self.size.height - CHROME_ROWS - PANEL_PADDING - 1)

    def _move_cursor(self, step: int) -> None:
        if not self.rows:
            return
        self.cursor = max(0, min(len(self.rows) - 1, self.cursor + step))
        self._show_rows()

    def do_choose(self) -> None:
        if self.view == "menu":
            self._act(self.rows[self.cursor][0])
        elif self.view == "modules":
            self._toggle_module()
        elif self.view == "settings":
            self._edit_setting()
        elif self.view == "ledger":
            self._show_entry()
        elif self.view.startswith("choose."):
            self._choose_slot()

    def _show_entry(self) -> None:
        identifier, _line = self.rows[self.cursor]
        found = [entry for entry in self.ledger.entries() if entry.identifier == identifier]
        if not found:
            return
        self._show_text(found[0].body or text("status.silent"))

    def _toggle_module(self) -> None:
        key, _line = self.rows[self.cursor]
        self.settings.set(key, not self.settings.get(key, True))
        self.panes["modules"] = (browser.module_rows(self.context), self.empty)
        self._show_rows()

    def _edit_setting(self) -> None:
        """Enter means change this now, when there is something to change it to."""
        key, _line = self.rows[self.cursor]
        value = self._setting_value(key)
        wanted = config.next_value(key, value)
        if wanted is not None:
            self._store_setting(key, wanted)
            return
        line = self.query_one(CommandLine)
        line.open(":")
        line.buffer = f"set {key}={value}"
        self.edit_mode = "COMMAND"

    def do_value_next(self) -> None:
        self._switch_value(1)

    def do_value_previous(self) -> None:
        self._switch_value(-1)

    def _switch_value(self, step: int) -> None:
        if self.view == "modules":
            self._toggle_module()
            return
        if self.view != "settings" or not self.rows:
            return
        key, _line = self.rows[self.cursor]
        wanted = config.next_value(key, self._setting_value(key), step)
        if wanted is None:
            self.query_one(CommandLine).say(text("hint.typed_setting"))
            return
        self._store_setting(key, wanted)

    def _setting_value(self, key: str):
        # A module's options are not in the configuration until they are set,
        # so they are read through the module the way the module reads them.
        parts = key.split(".")
        if parts[0] == "modules" and len(parts) == 3:
            found = self._module_named(parts[1])
            return self.settings.module(parts[1], found.defaults if found else {}).get(parts[2])
        return self.settings.get(key)

    def _store_setting(self, key: str, value) -> None:
        self.settings.set(key, value)
        self.panes["settings"] = (browser.setting_rows(self.settings), self.empty)
        self._show_rows()
        self.query_one(CommandLine).say(f"{key} is now {value}.")

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
        elif name == "checkhealth":
            self.do_checkhealth()
        elif name == "ledger":
            self.do_ledger()
        elif name in ("ask", "draw"):
            self.pin(argument.strip()) if argument.strip() else self.do_ask()
        elif name == "settings":
            self.do_settings()
        elif name == "menu":
            self.do_menu()
        elif name in ("w", "write"):
            line.say(text("status.saved", path=config.save(self.settings)))
        elif name:
            line.say(text("error.unknown_command", name=name), level="error")

    def _set_volume(self, argument: str, line: CommandLine) -> None:
        if not argument.isdigit():
            line.say(text("error.bad_volume"), level="error")
            return
        self.levels.volume = min(100, int(argument)) / 100
        self._show_volume()

    def _set_option(self, argument: str, line: CommandLine) -> None:
        option, separator, value = argument.partition("=")
        if not separator:
            line.say(text("error.bad_setting"), level="error")
            return
        self.settings.set(option.strip(), _typed(value.strip()))
        line.say(f"{option.strip()} is now {value.strip()}.")
        if self.view == "settings":
            self.do_settings()
        elif self.view == "modules":
            self.do_modules()

    # Layout

    def on_resize(self, event) -> None:
        # The event carries the new size; the widgets have not been laid out at
        # it yet, so the body is measured from the terminal rather than asked.
        self._render_body(event.size)

    def _splash(self):
        shown = mark.garble(self.slogan, self.tick) if self.garbled else self.slogan
        splash = mark.wordmark(self.terminal.glyphs, self.terminal.colours)
        splash.append(f"\n\n{shown}")
        return splash

    def _help_text(self) -> str:
        lines = [f"{NAME} keys", ""]
        for section in ("normal", "insert", "leader"):
            lines.append(section)
            for key, action in sorted(self.keymap[section].items()):
                lines.append(f"  {key:<16} {action}")
            lines.append("")
        lines.append(
            "Commands: :ask :draw :draw question//world//reading :ledger :modules "
            ":settings :set option=value :vol N :mute :checkhealth :w :help :q"
        )
        return "\n".join(lines)
