"""Append Tones to Pyxel's global registry and return their indices."""

from collections.abc import Iterable

import pyxel


def add_tone(tone: pyxel.Tone) -> int:
    """Append one Tone after pyxel.init(); preserve all existing slots."""
    index = len(pyxel.tones)
    pyxel.tones.append(tone)
    return index


def add_tones(tones: Iterable[pyxel.Tone]) -> tuple[int, ...]:
    """Append Tones in input order; an empty iterable returns ()."""
    tones = list(tones)
    first_index = len(pyxel.tones)
    pyxel.tones.extend(tones)
    return tuple(range(first_index, first_index + len(tones)))
