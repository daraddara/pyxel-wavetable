import pyxel
import pytest

import pyxel_wavetable as wt

PRESETS = [
    (wt.tom, 0.55),
    (wt.woodblock, 0.45),
    (wt.cowbell, 0.40),
    (wt.metallic, 0.35),
    (wt.click, 0.35),
]


@pytest.mark.parametrize("factory,gain", PRESETS)
def test_percussion_defaults(factory, gain):
    tone = factory()
    assert isinstance(tone, pyxel.Tone)
    assert tone.mode == 0
    assert len(tone.wavetable) == 128
    assert tone.sample_bits == 8
    assert tone.gain == pytest.approx(gain)
    assert all(0 <= value <= 255 for value in tone.wavetable)


@pytest.mark.parametrize("factory,_gain", PRESETS)
@pytest.mark.parametrize("bits", [1, 4, 16])
def test_percussion_overrides(factory, _gain, bits):
    tone = factory(size=64, sample_bits=bits, gain=0.2)
    assert isinstance(tone, pyxel.Tone)
    assert tone.mode == 0
    assert len(tone.wavetable) == 64
    assert tone.sample_bits == bits
    assert tone.gain == pytest.approx(0.2)
    assert all(0 <= value < (1 << bits) for value in tone.wavetable)
