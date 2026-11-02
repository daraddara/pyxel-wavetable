"""Small static timbre examples, without envelopes or playback logic."""

import pyxel
from dataclasses import dataclass
from types import MappingProxyType

from .generators import DEFAULT_GAIN, DEFAULT_SAMPLE_BITS, DEFAULT_SIZE, pm, harmonics


@dataclass(frozen=True)
class _PresetDefinition:
    name: str
    category: str
    generator: str
    gain: float = DEFAULT_GAIN
    ratio: int = 3
    index: float = 1.8
    amplitudes: tuple[float, ...] = ()
    size: int = DEFAULT_SIZE
    sample_bits: int = DEFAULT_SAMPLE_BITS


_PRESETS = MappingProxyType({definition.name: definition for definition in (
    _PresetDefinition("bell", "tonal", "pm", ratio=5, index=1.6),
    _PresetDefinition("bass", "tonal", "harmonics", amplitudes=(1, .4, .15)),
    _PresetDefinition("lead", "tonal", "pm", ratio=2, index=1.2),
    _PresetDefinition("organ", "tonal", "harmonics", amplitudes=(1, .5, .25, 0, .1)),
    _PresetDefinition("soft", "tonal", "harmonics", amplitudes=(1, .1)),
    _PresetDefinition("tom", "percussion", "harmonics", gain=.55, amplitudes=(1, .32, .14, .06)),
    _PresetDefinition("woodblock", "percussion", "harmonics", gain=.45,
                      amplitudes=(1, .05, .55, .03, .2)),
    _PresetDefinition("cowbell", "percussion", "pm", gain=.4, ratio=3, index=1.7),
    _PresetDefinition("metallic", "percussion", "harmonics", gain=.35,
                      amplitudes=(1, .08, .65, 0, .48, .12, .35, .04)),
    _PresetDefinition("click", "percussion", "harmonics", gain=.35,
                      amplitudes=(.15, .05, .2, .1, .4, .2, .55, .25)),
)})


def _preset_definitions() -> tuple[_PresetDefinition, ...]:
    """Internal metadata shared by the public presets and the bundled Tone Lab."""
    return tuple(_PRESETS.values())


def _build_preset(name, *, size, sample_bits, gain):
    definition = _PRESETS[name]
    if definition.generator == "pm":
        return pm(definition.ratio, definition.index, size=size,
                  sample_bits=sample_bits, gain=gain)
    return harmonics(definition.amplitudes, size=size, sample_bits=sample_bits, gain=gain)


def bell(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=_PRESETS["bell"].gain):
    """Bell-like static spectrum; no decay envelope."""
    return _build_preset("bell", size=size, sample_bits=sample_bits, gain=gain)


def bass(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=_PRESETS["bass"].gain):
    return _build_preset("bass", size=size, sample_bits=sample_bits, gain=gain)


def lead(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=_PRESETS["lead"].gain):
    return _build_preset("lead", size=size, sample_bits=sample_bits, gain=gain)


def organ(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=_PRESETS["organ"].gain):
    return _build_preset("organ", size=size, sample_bits=sample_bits, gain=gain)


def soft(*, size=DEFAULT_SIZE, sample_bits=DEFAULT_SAMPLE_BITS, gain=_PRESETS["soft"].gain):
    return _build_preset("soft", size=size, sample_bits=sample_bits, gain=gain)


def tom(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
        gain: float = _PRESETS["tom"].gain) -> pyxel.Tone:
    """Rounded tom-like spectrum; decay belongs to Pyxel playback."""
    return _build_preset("tom", size=size, sample_bits=sample_bits, gain=gain)


def woodblock(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
              gain: float = _PRESETS["woodblock"].gain) -> pyxel.Tone:
    """Hollow, woodblock-like static spectrum."""
    return _build_preset("woodblock", size=size, sample_bits=sample_bits, gain=gain)


def cowbell(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
            gain: float = _PRESETS["cowbell"].gain) -> pyxel.Tone:
    """Bright electronic cowbell-like PM spectrum."""
    return _build_preset("cowbell", size=size, sample_bits=sample_bits, gain=gain)


def metallic(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
             gain: float = _PRESETS["metallic"].gain) -> pyxel.Tone:
    """Complex harmonic spectrum for metallic percussion."""
    return _build_preset("metallic", size=size, sample_bits=sample_bits, gain=gain)


def click(*, size: int = DEFAULT_SIZE, sample_bits: int = DEFAULT_SAMPLE_BITS,
          gain: float = _PRESETS["click"].gain) -> pyxel.Tone:
    """High-harmonic material for short click/rim-like sounds."""
    return _build_preset("click", size=size, sample_bits=sample_bits, gain=gain)
