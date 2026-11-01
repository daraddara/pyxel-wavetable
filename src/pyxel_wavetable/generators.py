"""Generate one static cycle and return an ordinary :class:`pyxel.Tone`."""

import math
from collections.abc import Callable, Iterable

import pyxel

DEFAULT_SIZE = 128
DEFAULT_SAMPLE_BITS = 8
DEFAULT_GAIN = 0.5


def _integer(name: str, value: int, minimum: int, maximum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is out of range")


def _finite(name: str, value: float) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite real number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def from_samples(
    samples: Iterable[float], *, sample_bits: int = DEFAULT_SAMPLE_BITS,
    gain: float = DEFAULT_GAIN, normalize: bool = True,
) -> pyxel.Tone:
    """Quantize floating samples; their count becomes the wavetable length.

    Normalize by absolute peak (unless zero), then clip to [-1, 1] and map
    to [0, 2**sample_bits - 1] using Python's round (ties to even).
    Gain is stored separately on the Tone, not baked into the samples.
    """
    _integer("sample_bits", sample_bits, 1, 16)
    gain = _finite("gain", gain)
    if gain < 0 or gain > 3.4028234663852886e38:
        raise ValueError("gain must be nonnegative and fit Pyxel's float32")
    if not isinstance(normalize, bool):
        raise TypeError("normalize must be a bool")
    values = [_finite("sample", value) for value in samples]
    if not values:
        raise ValueError("samples must not be empty")
    peak = max(abs(value) for value in values)
    if normalize and peak:
        values = [value / peak for value in values]
    maximum = (1 << sample_bits) - 1
    table = [round((max(-1.0, min(1.0, value)) + 1.0) * 0.5 * maximum)
             for value in values]
    tone = pyxel.Tone()
    tone.mode = 0
    tone.sample_bits = sample_bits
    tone.wavetable[:] = table
    tone.gain = gain
    return tone


def from_function(
    func: Callable[[float], float], *, size: int = DEFAULT_SIZE,
    sample_bits: int = DEFAULT_SAMPLE_BITS, gain: float = DEFAULT_GAIN,
    normalize: bool = True,
) -> pyxel.Tone:
    """Sample func at tau*i/size, excluding the duplicate cycle endpoint."""
    _integer("size", size, 1)
    return from_samples(
        (func(math.tau * i / size) for i in range(size)),
        sample_bits=sample_bits, gain=gain, normalize=normalize,
    )


def sine(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
         gain: float = DEFAULT_GAIN, normalize: bool = True) -> pyxel.Tone:
    """A sine wave starting at zero, rising."""
    return from_function(math.sin, size=size, sample_bits=sample_bits,
                         gain=gain, normalize=normalize)


def triangle(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
             gain: float = DEFAULT_GAIN, normalize: bool = True) -> pyxel.Tone:
    """A triangle wave starting at -1, peaking at phase pi."""
    return from_function(lambda p: 1 - 4 * abs(p / math.tau - 0.5),
                         size=size, sample_bits=sample_bits, gain=gain,
                         normalize=normalize)


def saw(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
        gain: float = DEFAULT_GAIN, normalize: bool = True) -> pyxel.Tone:
    """An ascending ramp from -1 toward +1, resetting at the cycle boundary."""
    return from_function(lambda p: 2 * p / math.tau - 1, size=size,
                         sample_bits=sample_bits, gain=gain, normalize=normalize)


def pulse(duty: float = 0.25, *, size: int = DEFAULT_SIZE,
          sample_bits: int = DEFAULT_SAMPLE_BITS, gain: float = DEFAULT_GAIN,
          normalize: bool = True) -> pyxel.Tone:
    """+1 for the first duty fraction of the cycle, otherwise -1."""
    duty = _finite("duty", duty)
    if not 0 < duty < 1:
        raise ValueError("duty must satisfy 0 < duty < 1")
    return from_function(lambda p: 1.0 if p / math.tau < duty else -1.0,
                         size=size, sample_bits=sample_bits, gain=gain,
                         normalize=normalize)


def square(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
           gain: float = DEFAULT_GAIN, normalize: bool = True) -> pyxel.Tone:
    """A pulse with duty=0.5."""
    return pulse(0.5, size=size, sample_bits=sample_bits, gain=gain,
                 normalize=normalize)


def harmonics(amplitudes: Iterable[float], *, size: int = DEFAULT_SIZE,
              sample_bits: int = DEFAULT_SAMPLE_BITS, gain: float = DEFAULT_GAIN,
              normalize: bool = True) -> pyxel.Tone:
    """Sum sine harmonics; entry zero is the fundamental amplitude."""
    amplitudes = [_finite("amplitude", value) for value in amplitudes]
    if not amplitudes:
        raise ValueError("amplitudes must not be empty")
    return from_function(
        lambda p: math.fsum(a * math.sin((n + 1) * p)
                            for n, a in enumerate(amplitudes)),
        size=size, sample_bits=sample_bits, gain=gain, normalize=normalize,
    )


def pm(ratio: int = 3, index: float = 1.8, *, size: int = DEFAULT_SIZE,
       sample_bits: int = DEFAULT_SAMPLE_BITS, gain: float = DEFAULT_GAIN) -> pyxel.Tone:
    """Static PM waveform sin(p + index*sin(ratio*p)); ratio must be integer."""
    _integer("ratio", ratio, 1)
    index = _finite("index", index)
    if index < 0:
        raise ValueError("index must be nonnegative")
    return from_function(lambda p: math.sin(p + index * math.sin(p * ratio)),
                         size=size, sample_bits=sample_bits, gain=gain)
