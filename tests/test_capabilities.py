import pytest

from heidr.capabilities import detect_terminal

UTF8 = {"LANG": "en_US.UTF-8"}


@pytest.mark.parametrize(
    "environ, colours, glyphs, graphics",
    [
        ({"TERM": "linux", **UTF8}, 16, "blocks", "none"),
        ({"TERM": "xterm-256color", **UTF8}, 256, "braille", "sixel"),
        ({"TERM": "tmux-256color", "COLORTERM": "truecolor", **UTF8}, 16777216, "braille", "none"),
        ({"TERM": "xterm-kitty", "COLORTERM": "truecolor", **UTF8}, 16777216, "braille", "kitty"),
        ({"TERM": "dumb"}, 8, "ascii", "none"),
        ({"TERM": "xterm-256color", "LANG": "C"}, 256, "ascii", "sixel"),
    ],
)
def test_terminal_detection(environ, colours, glyphs, graphics):
    terminal = detect_terminal(environ)
    assert (terminal.colours, terminal.glyphs, terminal.graphics) == (colours, glyphs, graphics)


def test_poor_colour_terminals_get_the_tty_theme():
    assert detect_terminal({"TERM": "linux", **UTF8}).theme == "tty"
    assert detect_terminal({"TERM": "xterm-256color", **UTF8}).theme == "full"
