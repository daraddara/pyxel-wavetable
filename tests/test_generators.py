import math

import pyxel
import pytest

import pyxel_wavetable as wt


@pytest.mark.parametrize("factory", [wt.sine, wt.triangle, wt.saw, wt.square,
                                    wt.pulse, wt.pm, wt.bell, wt.bass, wt.lead,
                                    wt.organ, wt.soft])
def test_real_tones(factory):
    tone = factory(size=64, gain=0.25)
    assert isinstance(tone, pyxel.Tone)
    assert len(tone.wavetable) == 64
    assert tone.mode == 0
    assert tone.gain == pytest.approx(0.25)
    assert tone.sample_bits == 8


@pytest.mark.parametrize("bits", [1, 4, 8, 16])
def test_quantization(bits):
    tone = wt.from_samples([-1, 0, 1], sample_bits=bits)
    maximum = (1 << bits) - 1
    assert list(tone.wavetable) == [0, round(maximum / 2), maximum]
    assert all(0 <= x <= maximum for x in wt.sine(sample_bits=bits).wavetable)


def test_defaults():
    tone = wt.sine()
    assert len(tone.wavetable) == wt.DEFAULT_SIZE == 128
    assert tone.sample_bits == wt.DEFAULT_SAMPLE_BITS == 8
    assert tone.gain == wt.DEFAULT_GAIN == 0.5


def test_sine_samples():
    assert list(wt.sine(size=4).wavetable) == [128, 255, 128, 0]


def test_basic_shapes():
    assert list(wt.triangle(size=4).wavetable) == [0, 128, 255, 128]
    assert list(wt.saw(size=4).wavetable) == [0, 64, 128, 191]
    assert list(wt.square(size=8).wavetable) == list(wt.pulse(0.5, size=8).wavetable)


@pytest.mark.parametrize("duty", [0.125, 0.25, 0.5, 0.75])
def test_pulse_ratio(duty):
    values = list(wt.pulse(duty, size=128).wavetable)
    assert values.count(255) == int(128 * duty)
    assert values.count(0) == 128 - int(128 * duty)


def test_harmonics_formula():
    tone = wt.harmonics([1, 0.5, 0.25])
    expected = wt.from_function(lambda p: math.sin(p) + 0.5 * math.sin(2*p)
                               + 0.25 * math.sin(3*p))
    assert isinstance(tone, pyxel.Tone)
    assert list(tone.wavetable) == list(expected.wavetable)


def test_pm_formula_and_zero_index():
    expected = wt.from_function(lambda p: math.sin(p + 1.8 * math.sin(3*p)))
    assert list(wt.pm().wavetable) == list(expected.wavetable)
    assert list(wt.pm(index=0).wavetable) == list(wt.sine().wavetable)


def test_from_function_phases():
    phases = []

    def wave(p):
        phases.append(p)
        return p / math.pi - 1

    tone = wt.from_function(wave, size=4, normalize=False)
    assert phases == [0, math.pi/2, math.pi, 3*math.pi/2]
    assert list(tone.wavetable) == [0, 64, 128, 191]


def test_normalization_and_clipping():
    samples = [-2, -1, 0, 1, 2]
    assert list(wt.from_samples(samples).wavetable) == [0, 64, 128, 191, 255]
    assert list(wt.from_samples(samples, normalize=False).wavetable) == [0, 0, 128, 255, 255]
    assert list(wt.from_samples([-0.25, 0.25]).wavetable) == [0, 255]


def test_zero_and_iterable_input():
    assert list(wt.from_samples(iter([0, 0, 0])).wavetable) == [128]*3
    assert len(wt.harmonics(iter([0, 0])).wavetable) == 128
    assert list(wt.from_samples([0.5], normalize=False).wavetable) == [191]


def test_gain_is_separate_and_tones_are_independent():
    first, second = wt.sine(gain=0), wt.sine(gain=1)
    assert list(first.wavetable) == list(second.wavetable)
    first.wavetable[0] = 0
    assert second.wavetable[0] == 128
