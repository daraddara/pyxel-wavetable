"""Small static timbre examples, without envelopes or playback logic."""

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
