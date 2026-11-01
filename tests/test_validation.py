import pytest

import pyxel_wavetable as wt


@pytest.mark.parametrize("size", [0, -1])
def test_size(size):
    with pytest.raises(ValueError):
        wt.sine(size=size)


@pytest.mark.parametrize("bits", [0, -1, 17])
def test_bits(bits):
    with pytest.raises(ValueError):
        wt.sine(sample_bits=bits)


@pytest.mark.parametrize("value", [-1, float("inf"), float("nan"), 1e100])
def test_gain(value):
    with pytest.raises(ValueError):
        wt.sine(gain=value)


@pytest.mark.parametrize("duty", [-1, 0, 1, 2, float("nan"), float("inf")])
def test_duty(duty):
    with pytest.raises(ValueError):
        wt.pulse(duty)


@pytest.mark.parametrize("ratio", [0, -1])
def test_ratio_range(ratio):
    with pytest.raises(ValueError):
        wt.pm(ratio)


@pytest.mark.parametrize("ratio", [1.5, 3.0, True, "3"])
def test_ratio_type(ratio):
    with pytest.raises(TypeError):
        wt.pm(ratio)


@pytest.mark.parametrize("index", [-1, float("inf"), float("nan")])
def test_index(index):
    with pytest.raises(ValueError):
        wt.pm(index=index)


@pytest.mark.parametrize("factory", [wt.from_samples, wt.harmonics])
def test_empty(factory):
    with pytest.raises(ValueError):
        factory(iter([]))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_wave_data(value):
    for make in [lambda: wt.from_samples([value]),
                 lambda: wt.harmonics([value]),
                 lambda: wt.from_function(lambda p: value)]:
        with pytest.raises(ValueError):
            make()


@pytest.mark.parametrize("kwargs", [{"size": True}, {"size": 2.5},
                                   {"sample_bits": True}, {"sample_bits": 4.0},
                                   {"normalize": 1}])
def test_parameter_types(kwargs):
    with pytest.raises(TypeError):
        wt.sine(**kwargs)
