"""Generate static Pyxel Tones and optionally add them by index."""

from .generators import (
    DEFAULT_GAIN, DEFAULT_SAMPLE_BITS, DEFAULT_SIZE,
    pm, from_function, from_samples, harmonics, pulse, saw, sine, square, triangle,
)
from .presets import bass, bell, click, cowbell, lead, metallic, organ, soft, tom, woodblock
from .registration import add_tone, add_tones

__all__ = [
    "DEFAULT_SIZE", "DEFAULT_SAMPLE_BITS", "DEFAULT_GAIN",
    "sine", "triangle", "saw", "square", "pulse", "harmonics", "pm",
    "from_function", "from_samples", "bell", "bass", "lead", "organ", "soft",
    "add_tone", "add_tones",
    "tom", "woodblock", "cowbell", "metallic", "click",
]
