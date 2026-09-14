#!/bin/sh
# Install HEID//R and the outside programs it runs. Nothing here is built from
# source: every part comes from the place its own authors publish it, and what
# the distribution already packages is left to the package manager.
set -e

repo=SilentAutomaton/heidr
api=https://api.github.com/repos
bin="$HOME/.local/bin"
share="$HOME/.local/share/heidr"
whisper_models=https://huggingface.co/ggerganov/whisper.cpp/resolve/main
vosk_models=https://alphacephei.com/vosk/models

whisper_binary=""
whisper_model=""
vosk_model=""
ollama_model=""
llama_wanted=""
skipped=""

# Questions are read from the terminal rather than from stdin, so the script
# still asks them when it arrives through a pipe. Where there is no terminal at
# all — a container, a build — stdin is the only thing left to read.
# The test has to be an open, not a permission check: /dev/tty exists and looks
# readable in a container that has no controlling terminal behind it.
if (: </dev/tty) 2>/dev/null; then
    answers=/dev/tty
else
    answers=/dev/stdin
fi

ask() {
    printf '%s' "$1" >&2
    read -r reply <"$answers" || reply=""
    echo "$reply"
}

confirm() {
    case "$(ask "$1 [y/N] ")" in
        y | Y | yes) return 0 ;;
        *) return 1 ;;
    esac
}

have() {
    command -v "$1" >/dev/null 2>&1
}

mark() {
    if have "$1"; then echo "installed"; else echo "missing"; fi
}

fetch() {
    echo "  downloading ${2##*/}"
    # A progress bar drawn where nothing can erase it — a log, a pipe — comes out
    # as one very long line across the middle of the questions.
    if [ -t 2 ]; then
        curl -fL --progress-bar -o "$2" "$1"
    else
        curl -fLsS -o "$2" "$1"
    fi
}

die() {
    echo "$1" >&2
    exit 1
}

# A part that cannot be installed is not a reason to abandon the rest. What was
# missed is collected and said once at the end.
note_skipped() {
    skipped="$skipped
  $1"
}

# The only sanctioned way to ask GitHub which release holds a file: whisper.cpp
# and llama.cpp publish their binaries on nightly tags, and their `latest`
# release carries no assets at all, so `latest` would find nothing.
asset_url() {
    # The listing is held rather than piped: `head` closing the pipe early makes
    # curl fail with a write error and say so in the middle of the questions.
    listing=$(curl -fsSL "$api/$1/releases?per_page=30")
    echo "$listing" |
        grep -o "https://github.com/$1/releases/download/[^\"]*$2[^\"]*" |
        head -n 1
}

[ "$(uname -s)" = "Linux" ] ||
    die "This installer is for Linux. There is no binary for $(uname -s); see docs/en/install.md for the source route."

manager=""
for candidate in pacman apt-get dnf zypper; do
    if have "$candidate"; then
        manager="$candidate"
        break
    fi
done

root=""
if [ "$(id -u)" != 0 ]; then
    have sudo || die "Installing packages needs root and there is no sudo here. Run this as root, or install the packages by hand."
    root=sudo
fi

# The same program is packaged under a different name on every distribution, so
# the name is chosen by the manager rather than assumed.
package_named() {
    case "$1:$manager" in
        rtl433:apt-get | rtl433:dnf) echo "rtl-433" ;;
        rtl433:*) echo "rtl_433" ;;
        dump1090:apt-get) echo "dump1090-mutability" ;;
        dump1090:*) echo "dump1090" ;;
        *) echo "$1" ;;
    esac
}

install_packages() {
    if [ -z "$manager" ]; then
        note_skipped "$* — no package manager found, install them by hand"
        return 0
    fi
    case "$manager" in
        pacman) $root pacman -S --needed --noconfirm "$@" ;;
        apt-get) $root apt-get install -y "$@" ;;
        dnf) $root dnf install -y "$@" ;;
        zypper) $root zypper install -y "$@" ;;
    esac || note_skipped "$* — the package manager refused; the name may differ on this distribution"
}

need_tool() {
    have "$1" || install_packages "$1"
    have "$1" || die "$1 is needed to unpack what was downloaded, and it could not be installed. Install it, then run this again."
}

install_heidr() {
    url=$(asset_url "$repo" heidr-linux-x86_64)
    [ -n "$url" ] ||
        die "The latest release has no Linux binary. Install from source instead: see docs/en/install.md."
    mkdir -p "$bin"
    fetch "$url" "$bin/heidr"
    chmod +x "$bin/heidr"
}

install_radio() {
    install_packages rtl-sdr
    if confirm "Also install rtl_433 and dump1090? Two sources need them."; then
        install_packages "$(package_named rtl433)" "$(package_named dump1090)"
    fi
}

install_stream() {
    install_packages ffmpeg
    url=$(asset_url yt-dlp/yt-dlp yt-dlp_linux)
    if [ -z "$url" ]; then
        note_skipped "yt-dlp — its release carries no Linux binary today"
        return 0
    fi
    mkdir -p "$bin"
    fetch "$url" "$bin/yt-dlp"
    chmod +x "$bin/yt-dlp"
}

install_whisper() {
    need_tool tar
    url=$(asset_url ggml-org/whisper.cpp whisper-bin-ubuntu-x64.tar.gz)
    if [ -z "$url" ]; then
        note_skipped "whisper.cpp — no Linux binary published today; build it as docs/en/stt.md describes"
        return 0
    fi
    mkdir -p "$share/whisper" "$bin"
    fetch "$url" "$share/whisper.tar.gz"
    tar -xzf "$share/whisper.tar.gz" -C "$share/whisper"
    rm -f "$share/whisper.tar.gz"
    found=$(find "$share/whisper" -type f -name whisper-cli | head -n 1)
    if [ -z "$found" ]; then
        note_skipped "whisper.cpp — the archive held no whisper-cli, so the naming has changed"
        return 0
    fi
    chmod +x "$found"
    ln -sf "$found" "$bin/whisper-cli"
    whisper_binary="$bin/whisper-cli"

    echo "Models, smallest first: small-q5_1 (190 MB), medium-q5_0 (540 MB), large-v3-turbo-q5_0 (570 MB)."
    name=$(ask "Which model? [large-v3-turbo-q5_0] ")
    [ -n "$name" ] || name=large-v3-turbo-q5_0
    mkdir -p "$share/models"
    fetch "$whisper_models/ggml-$name.bin" "$share/models/ggml-$name.bin"
    whisper_model="$share/models/ggml-$name.bin"
}

install_vosk() {
    # vosk is imported by the program rather than run as a subprocess, so it has
    # to live in the same Python. A released binary carries its own interpreter
    # and cannot see anything pip installs, which is the whole answer here.
    if [ -x "$bin/heidr" ] && ! have python3; then
        note_skipped "vosk — it is a Python package and the released binary cannot load one; use whisper.cpp instead"
        return 0
    fi
    if [ -x "$bin/heidr" ]; then
        echo "Note: vosk is a Python package. The released binary carries its own"
        echo "Python and cannot load it, so vosk works only with a pip install of"
        echo "heidr. whisper.cpp is the choice for the binary."
        confirm "Install vosk anyway?" || return 0
    fi
    need_tool unzip
    pip3 install --user vosk ||
        pip3 install --user --break-system-packages vosk ||
        {
            note_skipped "vosk — pip refused; install it into a virtual environment by hand"
            return 0
        }
    echo "Models: vosk-model-small-en-us-0.15 (40 MB), vosk-model-small-ru-0.22 (45 MB), vosk-model-en-us-0.22 (1.8 GB)."
    name=$(ask "Which model? [vosk-model-small-en-us-0.15] ")
    [ -n "$name" ] || name=vosk-model-small-en-us-0.15
    mkdir -p "$share/models"
    fetch "$vosk_models/$name.zip" "$share/$name.zip"
    unzip -oq "$share/$name.zip" -d "$share/models"
    rm -f "$share/$name.zip"
    vosk_model="$share/models/$name"
}

install_ollama() {
    curl -fsSL https://ollama.com/install.sh | sh
    model=$(ask "Which model should ollama pull? [qwen3.5:9B], or '-' to skip: ")
    [ -n "$model" ] || model=qwen3.5:9B
    if [ "$model" = "-" ]; then
        return 0
    fi
    if ollama pull "$model"; then
        ollama_model="$model"
    else
        note_skipped "the ollama model — start the daemon, then run: ollama pull $model"
    fi
}

install_llama() {
    need_tool tar
    url=$(asset_url ggml-org/llama.cpp bin-ubuntu-x64.tar.gz)
    if [ -z "$url" ]; then
        note_skipped "llama.cpp — no Linux binary published today; build it from source"
        return 0
    fi
    mkdir -p "$share/llama.cpp" "$bin"
    fetch "$url" "$share/llama.tar.gz"
    tar -xzf "$share/llama.tar.gz" -C "$share/llama.cpp"
    rm -f "$share/llama.tar.gz"
    found=$(find "$share/llama.cpp" -type f -name llama-server | head -n 1)
    if [ -z "$found" ]; then
        note_skipped "llama.cpp — the archive held no llama-server, so the naming has changed"
        return 0
    fi
    chmod +x "$found"
    ln -sf "$found" "$bin/llama-server"
    llama_wanted=yes
}

echo "HEID//R — what to install"
echo
echo "  1  heidr                the program itself           [$(mark heidr)]"
echo "  2  radio tools          rtl-sdr, and optionally more [$(mark rtl_fm)]"
echo "  3  stream tools         ffmpeg and yt-dlp            [$(mark ffmpeg)]"
echo "  4  whisper.cpp          speech, best on noisy radio  [$(mark whisper-cli)]"
echo "  5  vosk                 speech, answers as it goes   [$(mark vosk-transcriber)]"
echo "  6  ollama               a local language model       [$(mark ollama)]"
echo "  7  llama.cpp            a local language model       [$(mark llama-server)]"
echo
echo "Only the first is needed. The program says what is missing at every start"
echo "and runs without any of the rest."
echo

chosen=$(ask "Numbers, separated by spaces, or 'all': ")
if [ "$chosen" = "all" ]; then
    chosen="1 2 3 4 5 6 7"
fi
[ -n "$chosen" ] || die "Nothing chosen. Nothing installed."

for number in $chosen; do
    case "$number" in
        1) install_heidr ;;
        2) install_radio ;;
        3) install_stream ;;
        4) install_whisper ;;
        5) install_vosk ;;
        6) install_ollama ;;
        7) install_llama ;;
        *) echo "There is no $number on the list. Skipped." ;;
    esac
done

# Installing a recogniser is half of it. The program reads which one to use out
# of its configuration, and an unset model path leaves it with nothing.
heidr="$bin/heidr"
if ! [ -x "$heidr" ]; then
    have heidr && heidr=heidr || heidr=""
fi

if [ -n "$heidr" ]; then
    if [ -n "$whisper_model" ]; then
        "$heidr" --set stt.provider=whisper_cpp \
            --set "stt.model_path=$whisper_model" \
            --set "stt.binary=$whisper_binary"
    elif [ -n "$vosk_model" ]; then
        "$heidr" --set stt.provider=vosk --set "stt.model_path=$vosk_model"
    fi
    if [ -n "$ollama_model" ]; then
        "$heidr" --set llm.provider=ollama \
            --set "llm.model=$ollama_model" \
            --set llm.base_url=http://localhost:11434
    elif [ -n "$llama_wanted" ]; then
        "$heidr" --set llm.provider=openai_compat --set llm.base_url=http://localhost:8080
    fi
fi

if [ -n "$skipped" ]; then
    echo
    echo "Not installed:$skipped"
fi

case ":$PATH:" in
    *":$bin:"*) ;;
    *) echo "
$bin is not on your PATH, so the shell will not find heidr there. Add it in
your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac

if [ -n "$heidr" ]; then
    echo
    "$heidr" --self-check || true
fi
