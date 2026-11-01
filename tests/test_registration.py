import pyxel
import pytest

import pyxel_wavetable as wt


def signature(tone):
    return tone.mode, tone.sample_bits, list(tone.wavetable), tone.gain


@pytest.fixture(scope="module", autouse=True)
def initialize_pyxel():
    pyxel.init(1, 1, headless=True)


@pytest.fixture(autouse=True)
def preserve_tones():
    original = list(pyxel.tones)
    original_values = [signature(tone) for tone in original]
    try:
        yield
        assert [signature(tone) for tone in list(pyxel.tones)[:len(original)]] == original_values
    finally:
        pyxel.tones[:] = original


def test_add_tone():
    before = len(pyxel.tones)
    tone = wt.pm()
    index = wt.add_tone(tone)
    assert type(index) is int
    assert index == before
    assert len(pyxel.tones) == before + 1
    assert signature(pyxel.tones[index]) == signature(tone)


def test_add_tones_order():
    before = len(pyxel.tones)
    tones = [wt.sine(), wt.saw(), wt.pulse(0.125)]
    indices = wt.add_tones(tones)
    assert type(indices) is tuple
    assert indices == tuple(range(before, before + 3))
    assert all(type(index) is int for index in indices)
    assert len(pyxel.tones) == before + 3
    assert [signature(pyxel.tones[index]) for index in indices] == [signature(t) for t in tones]


@pytest.mark.parametrize("tones", [[], (), iter(())])
def test_empty(tones):
    before = [signature(tone) for tone in pyxel.tones]
    assert wt.add_tones(tones) == ()
    assert [signature(tone) for tone in pyxel.tones] == before


def test_generator():
    before = len(pyxel.tones)
    indices = wt.add_tones(wt.sine(gain=gain) for gain in [0.1, 0.2, 0.3])
    assert indices == tuple(range(before, before + 3))
    assert len(pyxel.tones) == before + 3
    assert [pyxel.tones[index].gain for index in indices] == pytest.approx([0.1, 0.2, 0.3])


def test_repeated_add_tone_uses_current_length():
    before = len(pyxel.tones)
    first = wt.add_tone(wt.sine())
    rest = wt.add_tones([wt.saw(), wt.pm()])
    last = wt.add_tone(wt.soft())
    assert (first, *rest, last) == tuple(range(before, before + 4))


def test_indices_in_native_sound_and_mml():
    index = wt.add_tone(wt.pm())
    sound = pyxel.Sound()
    sound.set("c2 d2 e2 g2", str(index), "7", "n", 12)
    assert list(sound.tones) == [index]
    sound.set_tones(str(index))
    assert list(sound.tones) == [index]
    # Register beyond the single-digit range supported by Sound.set_tones.
    indices = wt.add_tones(wt.sine() for _ in range(10))
    assert indices[-1] >= 10
    try:
        pyxel.play(0, f"@{indices[-1]} O3 C D E G", loop=True)
        pyxel.flip()
        assert pyxel.play_pos(0) is not None
    finally:
        pyxel.stop(0)
