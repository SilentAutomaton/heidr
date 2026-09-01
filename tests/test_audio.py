import numpy as np

from heidr.audio import Gain, Levels, Output, spectrum, to_float

RATE = 32000


def tone(amplitude: float, samples: int = 1024, hertz: float = 440.0) -> np.ndarray:
    time = np.arange(samples) / RATE
    return (amplitude * np.sin(2 * np.pi * hertz * time)).astype(np.float32)


def settled(gain: Gain, block: np.ndarray, blocks: int = 400) -> np.ndarray:
    for _ in range(blocks):
        out = gain.process(block)
    return out


def test_a_quiet_signal_is_brought_up_to_the_target():
    levels = Levels(volume=1.0)
    out = settled(Gain(levels, RATE), tone(0.01))

    assert abs(float(np.sqrt(np.mean(out**2))) - levels.target_rms) < 0.02


def test_a_loud_signal_is_brought_down_to_the_target():
    levels = Levels(volume=1.0)
    out = settled(Gain(levels, RATE), tone(0.9))

    assert abs(float(np.sqrt(np.mean(out**2))) - levels.target_rms) < 0.02


def test_the_ceiling_is_never_crossed():
    levels = Levels(volume=1.0, target_rms=0.9, ceiling=0.5)
    gain = Gain(levels, RATE)

    for amplitude in (0.001, 0.05, 0.4, 1.0):
        out = settled(gain, tone(amplitude), blocks=50)
        assert float(np.max(np.abs(out))) <= levels.ceiling + 1e-6


def travelled(gain: Gain, block: np.ndarray) -> float:
    """What fraction of the distance to its target one block moves the gain."""
    rms = float(np.sqrt(np.mean(block**2)))
    wanted = gain.levels.target_rms / rms
    before = gain.gain
    gain.process(block)
    return abs(gain.gain - before) / abs(wanted - before)


def test_a_sudden_loud_sound_is_caught_faster_than_a_pause_is_released():
    levels = Levels(volume=1.0, attack_ms=10, release_ms=2000)

    caught = travelled(settled_gain(levels), tone(1.0))
    released = travelled(settled_gain(levels), tone(0.001))

    # A pause between words must not pump the gain up into the noise, so the
    # way down is quick and the way back up is slow.
    assert caught > released * 10


def settled_gain(levels: Levels) -> Gain:
    gain = Gain(levels, RATE)
    settled(gain, tone(0.2), blocks=200)
    return gain


def test_muting_produces_silence():
    levels = Levels(volume=1.0, muted=True)
    assert not np.any(Gain(levels, RATE).process(tone(0.5)))


def test_volume_scales_what_leaves():
    loud = settled(Gain(Levels(volume=1.0), RATE), tone(0.3))
    quiet = settled(Gain(Levels(volume=0.25), RATE), tone(0.3))

    assert float(np.max(np.abs(quiet))) < float(np.max(np.abs(loud)))


def test_volume_keys_stay_inside_their_range():
    levels = Levels(volume=0.98)
    levels.louder()
    levels.louder()
    assert levels.volume == 1.0

    levels.volume = 0.02
    levels.quieter()
    levels.quieter()
    assert levels.volume == 0.0


def test_levels_come_from_the_configuration(default_config):
    default_config.set("audio.target_rms", 0.3)
    default_config.set("audio.volume", 0.4)

    levels = Levels.from_config(default_config)

    assert (levels.target_rms, levels.volume) == (0.3, 0.4)


def test_sixteen_bit_samples_become_floats():
    raw = np.array([0, 16384, -16384], dtype="<i2").tobytes()
    assert list(np.round(to_float(raw), 3)) == [0.0, 0.5, -0.5]


def test_the_spectrum_has_one_bar_per_column_between_zero_and_one():
    bars = spectrum(tone(0.5), bins=40)

    assert len(bars) == 40
    assert min(bars) >= 0.0 and max(bars) <= 1.0


def test_the_spectrum_puts_a_tone_in_the_right_place():
    bars = spectrum(tone(0.5, samples=4096, hertz=1000), bins=32)
    loudest = bars.index(max(bars))

    # 1 kHz sits an eighth of the way up a spectrum that reaches 16 kHz.
    assert 1 <= loudest <= 5


def test_the_spectrum_of_silence_is_flat():
    assert spectrum(np.zeros(1024, dtype=np.float32), bins=16) == [0.0] * 16


def test_output_without_a_sound_device_still_levels_the_block(monkeypatch):
    output = Output(Levels(volume=1.0), RATE)
    monkeypatch.setattr(output, "stream", None)

    played = output.play(tone(0.01))

    assert played.shape == (1024,)
    assert float(np.max(np.abs(played))) > 0.0
