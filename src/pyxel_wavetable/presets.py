"""Small static timbre examples, without envelopes or playback logic."""

import pyxel

from .generators import DEFAULT_GAIN, DEFAULT_SAMPLE_BITS, DEFAULT_SIZE, pm, harmonics


def bell(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=DEFAULT_GAIN):
    """Bell-like static spectrum; no decay envelope."""
    return pm(5, 1.6, size=size, sample_bits=sample_bits, gain=gain)


def bass(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=DEFAULT_GAIN):
    return harmonics([1, 0.4, 0.15], size=size, sample_bits=sample_bits, gain=gain)


def lead(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=DEFAULT_GAIN):
    return pm(2, 1.2, size=size, sample_bits=sample_bits, gain=gain)


def organ(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=DEFAULT_GAIN):
    return harmonics([1, 0.5, 0.25, 0, 0.1], size=size, sample_bits=sample_bits, gain=gain)


def soft(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=DEFAULT_GAIN):
    return harmonics([1, 0.1], size=size, sample_bits=sample_bits, gain=gain)


def tom(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
        gain: float = 0.55) -> pyxel.Tone:
    """Rounded tom-like spectrum; decay belongs to Pyxel playback."""
    return harmonics([1.00, 0.32, 0.14, 0.06], size=size,
                     sample_bits=sample_bits, gain=gain)


def woodblock(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
              gain: float = 0.45) -> pyxel.Tone:
    """Hollow, woodblock-like static spectrum."""
    return harmonics([1.00, 0.05, 0.55, 0.03, 0.20], size=size,
                     sample_bits=sample_bits, gain=gain)


def cowbell(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
            gain: float = 0.40) -> pyxel.Tone:
    """Bright electronic cowbell-like PM spectrum."""
    return pm(ratio=3, index=1.7, size=size, sample_bits=sample_bits, gain=gain)


def metallic(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
             gain: float = 0.35) -> pyxel.Tone:
    """Complex harmonic spectrum for metallic percussion."""
    return harmonics([1.00, 0.08, 0.65, 0.00, 0.48, 0.12, 0.35, 0.04],
                     size=size, sample_bits=sample_bits, gain=gain)


def click(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
          gain: float = 0.35) -> pyxel.Tone:
    """High-harmonic material for short click/rim-like sounds."""
    return harmonics([0.15, 0.05, 0.20, 0.10, 0.40, 0.20, 0.55, 0.25],
                     size=size, sample_bits=sample_bits, gain=gain)
