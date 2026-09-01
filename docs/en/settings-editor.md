# Settings editor and module list

Two pages opened from inside the interface, so editing the configuration does not
mean leaving the program.

## `:modules`

Every registered module: slot, name and state.

| State | Meaning |
|---|---|
| `ready` | Works here and now, and is in the lottery |
| `needs sdr, stt` | Something listed is missing |
| `unavailable` | The module's own probe said no |
| `off` | You switched it off |

Telling those four apart matters. `needs sdr` means "plug the dongle in"; `off`
means "you turned this off yourself, and I remember". The first is fixed with
hardware, the second with the same `Enter` key.

Navigation: `j` and `k` move, `Enter` toggles. A module switched off leaves the
lottery immediately, with no restart.

## `:settings`

Every configurable option except the per-module sections: interface, audio,
language model, speech, rite, ledger. Each shows its effective value across all
layers, not what happens to be written in the file.

`Enter` on a line opens the command line already filled in with
`:set key=value`, leaving only the tail to change. Fewer chances to mistype a key
name.

## `:set`

Works without the list too. The value is read as the kind it looks like: `true`
and `false` become booleans, whole and decimal numbers become numbers, anything
else stays a string.

```
:set audio.target_rms=0.2
:set ui.splash=false
:set modules.fm_voice.dwell_s=8
```

Changes take effect at once, volume and levelling parameters included.

## `:w`

Writes the configuration to `~/.config/heidr/config.toml`.

Only what differs from the defaults is written. The file stays short and readable
instead of becoming a dump of every parameter with your own edits lost among
them.

Without `:w`, changes last until you quit. That is deliberate: turning the volume
down for one session is ordinary, and there is no reason to rewrite a file for
it.

## Module settings

The `[modules.<name>]` sections are not listed: each module has its own set, and
the sensible place to describe them is that module's own document.

They can be changed the same way: `:set modules.sky.radius_nm=80`.

## Sources

The interaction vocabulary — confirm, choose, one field at a time — is informed
by [gum](https://github.com/charmbracelet/gum) and
[huh](https://github.com/charmbracelet/huh) from Charm. No code was taken: those
are Go.
