# Install HEID//R and the outside programs it runs. Nothing here is built from
# source: every part comes from the place its own authors publish it, and what
# winget already packages is left to winget.
$ErrorActionPreference = 'Stop'

$repo = 'SilentAutomaton/heidr'
$api = 'https://api.github.com/repos'
$bin = Join-Path $env:LOCALAPPDATA 'heidr\bin'
$share = Join-Path $env:LOCALAPPDATA 'heidr'
$whisperModels = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main'
$voskModels = 'https://alphacephei.com/vosk/models'

$whisperBinary = ''
$whisperModel = ''
$voskModel = ''
$ollamaModel = ''
$llamaWanted = $false
$skipped = @()

function Ask($question, $fallback = '') {
    $answer = Read-Host $question
    if ([string]::IsNullOrWhiteSpace($answer)) { return $fallback }
    return $answer.Trim()
}

function Confirm($question) {
    return (Ask "$question [y/N]") -match '^(y|Y|yes)$'
}

function Have($program) {
    return [bool](Get-Command $program -ErrorAction SilentlyContinue)
}

function Mark($program) {
    if (Have $program) { return 'installed' } else { return 'missing' }
}

function Fetch($url, $target) {
    New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
    Write-Host "  downloading $(Split-Path $target -Leaf)"
    Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing
}

# A part that cannot be installed is not a reason to abandon the rest. What was
# missed is collected and said once at the end.
function Skip($why) {
    $script:skipped += $why
}

# The only sanctioned way to ask GitHub which release holds a file: whisper.cpp
# and llama.cpp publish their binaries on nightly tags, and their `latest`
# release carries no assets at all, so `latest` would find nothing.
function AssetUrl($project, $pattern) {
    $releases = Invoke-RestMethod -Uri "$api/$project/releases?per_page=30" -UseBasicParsing
    foreach ($release in $releases) {
        foreach ($asset in $release.assets) {
            if ($asset.name -like "*$pattern*") { return $asset.browser_download_url }
        }
    }
    return ''
}

function Unpack($archive, $target) {
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Expand-Archive -Path $archive -DestinationPath $target -Force
    Remove-Item $archive -Force
}

function InstallByWinget($id, $name) {
    if (-not (Have winget)) {
        Skip "$name - winget is not on this machine; install it from its own site"
        return $false
    }
    winget.exe install --id $id --accept-package-agreements --accept-source-agreements --silent |
        Out-Null
    if ($LASTEXITCODE -ne 0) {
        Skip "$name - winget refused; install it from its own site"
        return $false
    }
    return $true
}

function InstallHeidr {
    $url = AssetUrl $repo 'heidr-windows-x86_64.exe'
    if (-not $url) {
        Skip 'heidr - the latest release carries no Windows binary; install from source, as docs/en/install.md describes'
        return
    }
    Fetch $url (Join-Path $bin 'heidr.exe')
}

function InstallRadio {
    # Windows has no driver the rtl_* programs can use the way Linux does, so
    # there is nothing to install here and saying so is the honest answer.
    Write-Host ''
    Write-Host 'The RTL-SDR cannot be used from Windows directly. The way through is'
    Write-Host 'WSL2 with usbipd-win, which forwards the dongle into the Linux side:'
    Write-Host ''
    Write-Host '    winget install usbipd'
    Write-Host '    usbipd list'
    Write-Host '    usbipd bind --busid <the dongle id>'
    Write-Host '    usbipd attach --wsl --busid <the dongle id>'
    Write-Host ''
    Write-Host 'Then run this installer inside WSL2 instead. See docs/en/install.md.'
    Skip 'the radio tools - they need WSL2, not Windows'
}

function InstallStream {
    InstallByWinget 'Gyan.FFmpeg' 'ffmpeg' | Out-Null
    $url = AssetUrl 'yt-dlp/yt-dlp' 'yt-dlp.exe'
    if (-not $url) {
        Skip 'yt-dlp - its release carries no Windows binary today'
        return
    }
    Fetch $url (Join-Path $bin 'yt-dlp.exe')
}

function InstallWhisper {
    $url = AssetUrl 'ggml-org/whisper.cpp' 'whisper-bin-x64.zip'
    if (-not $url) {
        Skip 'whisper.cpp - no Windows binary published today; build it as docs/en/stt.md describes'
        return
    }
    $archive = Join-Path $share 'whisper.zip'
    Fetch $url $archive
    Unpack $archive (Join-Path $share 'whisper')
    $found = Get-ChildItem -Path (Join-Path $share 'whisper') -Recurse -Filter 'whisper-cli.exe' |
        Select-Object -First 1
    if (-not $found) {
        Skip 'whisper.cpp - the archive held no whisper-cli.exe, so the naming has changed'
        return
    }
    $script:whisperBinary = $found.FullName

    Write-Host 'Models, smallest first: small-q5_1 (190 MB), medium-q5_0 (540 MB), large-v3-turbo-q5_0 (570 MB).'
    $name = Ask 'Which model?' 'large-v3-turbo-q5_0'
    $target = Join-Path $share "models\ggml-$name.bin"
    Fetch "$whisperModels/ggml-$name.bin" $target
    $script:whisperModel = $target
}

function InstallVosk {
    # vosk is imported by the program rather than run as a subprocess, so it has
    # to live in the same Python. The released binary carries its own interpreter
    # and cannot see anything pip installs, which is the whole answer here.
    if (Test-Path (Join-Path $bin 'heidr.exe')) {
        Write-Host 'Note: vosk is a Python package. The released binary carries its own'
        Write-Host 'Python and cannot load it, so vosk works only with a pip install of'
        Write-Host 'heidr. whisper.cpp is the choice for the binary.'
        if (-not (Confirm 'Install vosk anyway?')) { return }
    }
    if (-not (Have py) -and -not (Have python)) {
        Skip 'vosk - there is no Python here; install it from python.org, then run this again'
        return
    }
    $python = if (Have py) { 'py' } else { 'python' }
    & $python -m pip install --user vosk
    if ($LASTEXITCODE -ne 0) {
        Skip 'vosk - pip refused; install it into a virtual environment by hand'
        return
    }
    Write-Host 'Models: vosk-model-small-en-us-0.15 (40 MB), vosk-model-small-ru-0.22 (45 MB), vosk-model-en-us-0.22 (1.8 GB).'
    $name = Ask 'Which model?' 'vosk-model-small-en-us-0.15'
    $archive = Join-Path $share "$name.zip"
    Fetch "$voskModels/$name.zip" $archive
    Unpack $archive (Join-Path $share 'models')
    $script:voskModel = Join-Path $share "models\$name"
}

function InstallOllama {
    if (-not (InstallByWinget 'Ollama.Ollama' 'ollama')) {
        $url = AssetUrl 'ollama/ollama' 'OllamaSetup.exe'
        if (-not $url) {
            Skip 'ollama - no Windows installer published today; get it from ollama.com'
            return
        }
        $setup = Join-Path $share 'OllamaSetup.exe'
        Fetch $url $setup
        Start-Process -FilePath $setup -Wait
    }
    $model = Ask "Which model should ollama pull? Empty for qwen3.5:9B, '-' to skip" 'qwen3.5:9B'
    if ($model -eq '-') { return }
    ollama.exe pull $model
    if ($LASTEXITCODE -eq 0) {
        $script:ollamaModel = $model
    } else {
        Skip "the ollama model - start ollama, then run: ollama pull $model"
    }
}

function InstallLlama {
    $url = AssetUrl 'ggml-org/llama.cpp' 'bin-win-cpu-x64.zip'
    if (-not $url) {
        Skip 'llama.cpp - no Windows binary published today; build it from source'
        return
    }
    $archive = Join-Path $share 'llama.zip'
    Fetch $url $archive
    Unpack $archive (Join-Path $share 'llama.cpp')
    $found = Get-ChildItem -Path (Join-Path $share 'llama.cpp') -Recurse -Filter 'llama-server.exe' |
        Select-Object -First 1
    if (-not $found) {
        Skip 'llama.cpp - the archive held no llama-server.exe, so the naming has changed'
        return
    }
    $script:llamaWanted = $true
    Write-Host "llama-server.exe is in $($found.DirectoryName). Start it with your own model."
}

Write-Host 'HEID//R - what to install'
Write-Host ''
Write-Host "  1  heidr                the program itself           [$(Mark heidr)]"
Write-Host '  2  radio tools          not possible on Windows      [see WSL2]'
Write-Host "  3  stream tools         ffmpeg and yt-dlp            [$(Mark ffmpeg)]"
Write-Host "  4  whisper.cpp          speech, best on noisy radio  [$(Mark whisper-cli)]"
Write-Host "  5  vosk                 speech, answers as it goes   [$(Mark vosk-transcriber)]"
Write-Host "  6  ollama               a local language model       [$(Mark ollama)]"
Write-Host "  7  llama.cpp            a local language model       [$(Mark llama-server)]"
Write-Host ''
Write-Host 'Only the first is needed. The program says what is missing at every start'
Write-Host 'and runs without any of the rest.'
Write-Host ''

$chosen = Ask "Numbers, separated by spaces, or 'all'"
if ($chosen -eq 'all') { $chosen = '1 2 3 4 5 6 7' }
if (-not $chosen) { throw 'Nothing chosen. Nothing installed.' }

foreach ($number in $chosen -split '\s+') {
    switch ($number) {
        '1' { InstallHeidr }
        '2' { InstallRadio }
        '3' { InstallStream }
        '4' { InstallWhisper }
        '5' { InstallVosk }
        '6' { InstallOllama }
        '7' { InstallLlama }
        default { Write-Host "There is no $number on the list. Skipped." }
    }
}

# Installing a recogniser is half of it. The program reads which one to use out
# of its configuration, and an unset model path leaves it with nothing.
$heidr = Join-Path $bin 'heidr.exe'
if (-not (Test-Path $heidr)) {
    $heidr = if (Have heidr) { 'heidr' } else { '' }
}

if ($heidr) {
    if ($whisperModel) {
        & $heidr --set stt.provider=whisper_cpp --set "stt.model_path=$whisperModel" --set "stt.binary=$whisperBinary"
    } elseif ($voskModel) {
        & $heidr --set stt.provider=vosk --set "stt.model_path=$voskModel"
    }
    if ($ollamaModel) {
        & $heidr --set llm.provider=ollama --set "llm.model=$ollamaModel" --set llm.base_url=http://localhost:11434
    } elseif ($llamaWanted) {
        & $heidr --set llm.provider=openai_compat --set llm.base_url=http://localhost:8080
    }
}

if ($skipped) {
    Write-Host ''
    Write-Host 'Not installed:'
    foreach ($line in $skipped) { Write-Host "  $line" }
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$bin*") {
    if (Confirm "Add $bin to your PATH?") {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$bin", 'User')
        Write-Host 'Added. Open a new terminal for it to take effect.'
    } else {
        Write-Host "$bin is not on your PATH, so the shell will not find heidr there."
    }
}

if ($heidr) {
    Write-Host ''
    & $heidr --self-check
}
