"""Static wavetable helpers for Pyxel. Every generator returns pyxel.Tone."""

from .generators import (
    DEFAULT_GAIN, DEFAULT_SAMPLE_BITS, DEFAULT_SIZE,
    pm, from_function, from_samples, harmonics, pulse, saw, sine, square, triangle,
)
from .presets import bass, bell, lead, organ, soft

__all__ = [
    "DEFAULT_SIZE", "DEFAULT_SAMPLE_BITS", "DEFAULT_GAIN",
    "sine", "triangle", "saw", "square", "pulse", "harmonics", "pm",
    "from_function", "from_samples", "bell", "bass", "lead", "organ", "soft",
]
