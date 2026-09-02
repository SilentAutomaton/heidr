# Credits

`HEID//R` stands on other people's work. This table is the whole list; each
module's own document repeats the rows that apply to it.

"Code" means source was adapted into this repository, with the original header
kept in the file. "Idea" means nothing was copied — the approach was described
in public and reimplemented here.

## Code adapted

| Project | Author | Licence | What was taken |
|---|---|---|---|
| [rtl-entropy](https://github.com/pwarren/rtl-entropy) | Paul Warren | GPL-3.0 | Von Neumann debiasing and SHA-512 whitening of raw radio samples |
| [drawille](https://github.com/asciimoo/drawille) | asciimoo | GPL-3.0 | Braille cell pixel rendering |
| [no-more-secrets](https://github.com/bartobri/no-more-secrets) | Brian Barto | GPL-3.0 | Keypress gated decryption reveal |
| [gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox) | Doug Haber | ISC | Frequency sweep modes and dwell time design |
| [dreamdir](https://github.com/sobjornstad/dreamdir) | Soren Bjornstad | MIT | Plain text one-file-per-entry ledger format |
| [asciimatics](https://github.com/peterbrittain/asciimatics) | Peter Brittain | Apache-2.0 | The plasma field and the turning cog, adapted into painters |

## Ideas and methods

| Project | Author | Licence | What was taken |
|---|---|---|---|
| [libraryofbabel.info-algo](https://github.com/librarianofbabel/libraryofbabel.info-algo) | Jonathan Basile | not stated | The invertible bijection: an address becomes text, and the text recovers the address. Reimplemented from the published description |
| [ichingshifa](https://github.com/kentang2017/ichingshifa) | kentang2017 | not stated | Confirmation of the Da Yan three-change counting. The method itself is traditional and was implemented here from the classical description |
| [randombtc](https://github.com/callebtc/randombtc) | callebtc | not verified | Use the Merkle root, not the block hash: mining difficulty pushes leading zeros into the hash and drains its entropy |
| [drand](https://github.com/drand/drand) | Protocol Labs and others | Apache-2.0 / MIT | Chaining each entry to the previous one so the whole history verifies |
| [retrogram-rtlsdr](https://github.com/r4d10n/retrogram-rtlsdr) | r4d10n | GPL | ASCII spectrum in the terminal as the register for a listening screen |
| [astroterm](https://github.com/da-luce/astroterm) | da-luce | MIT | Right ascension to altitude-azimuth projection with magnitude mapped to glyph density |
| [gum](https://github.com/charmbracelet/gum) and [huh](https://github.com/charmbracelet/huh) | Charm | MIT | The ceremonial vocabulary: confirm, spin, choose, one field per screen |
| [fortune-mod](https://github.com/shlomif/fortune-mod) | Shlomi Fish and others | ISC | Flat offline corpus convention, so a run never depends on a website |
| [Kerykeion](https://github.com/g-battaglia/kerykeion) | Giacomo Battaglia | not verified | Formatting found data into a block prepared for a language model, separate from the human readable form |
| [Stellium](https://github.com/katelouie/stellium) | katelouie | not verified | Planetary hours: seven rulers cycling from sunrise to sunrise, day and night hours counted apart |
| [ddate](https://github.com/bo0ts/ddate) | Druel the Chaotic, Bo Tso | GPL | Discordian calendar conversion |
| [Pentametron](http://pentametron.com) | Ranjit Bhatnagar | — | The north star: meaning is found in what people said by accident, never generated |
| [Plasma tutorial](http://lodev.org/cgtutor/plasma.html) | Lode Vandevenne | — | Four sine waves radiating from four points, which is what a plasma field is |
| [cmatrix](https://github.com/abishekvashok/cmatrix) | Abishek V Ashok | GPL-3.0 | The register of falling glyph columns |
| Conway's Game of Life | John Conway, 1970 | public domain | The rules, which are not ours to adjust |
| [Joan Stark's gallery](https://oldcompcz.github.io/jgs/joan_stark/), [Christopher Johnson's collection](https://asciiart.website/), [ASCII Art Archive](https://www.asciiart.eu/) | Joan G. Stark and others | all rights reserved | Studied, not copied. Density as tone, shadow inside a cowl, a face made of three marks. Their terms require the artist's initials to stay on every copy, which this licence cannot honour, so nothing was taken |
| Minecraft obfuscated text | Mojang | — | The register of the flickering slogan: letters change, word shapes do not |

## External programs called as subprocesses

These are executed, not linked. Their licences do not reach this code.

| Program | Licence | Used by |
|---|---|---|
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | MIT | `stt/whisper_cpp` |
| [vosk-api](https://github.com/alphacep/vosk-api) | Apache-2.0 | `stt/vosk` |
| rtl_sdr, rtl_fm, rtl_power | GPL-2.0 | the radio sources |
| [rtl_433](https://github.com/merbanan/rtl_433) | GPL-2.0 | `world/ism` |
| [dump1090](https://github.com/antirez/dump1090) | ISC | `world/adsb_local` |
| [noaa-apt](https://github.com/martinber/noaa-apt) | GPL-3.0 | `world/apt` |
| [chafa](https://github.com/hpjansson/chafa) | GPL-3.0 | image output in the terminal |

## Python dependencies

| Package | Licence |
|---|---|
| [textual](https://github.com/Textualize/textual), rich | MIT |
| [terminaltexteffects](https://github.com/ChrisBuilds/terminaltexteffects) | MIT |
| numpy, requests, tomli-w, sounddevice | BSD or MIT |

## Data

Public endpoints the sources use: USGS earthquake feed,
blockchain.info, api.adsb.lol, NIST Randomness Beacon, Certificate Transparency
logs, libraryofbabel.info. Each module's document names the exact endpoint and
its terms.

## Name

Heiðr, the völva of the *Völuspá*. Public domain by about a thousand years.
