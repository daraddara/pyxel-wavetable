from dataclasses import FrozenInstanceError
import inspect

import pytest
import pyxel_wavetable as wt
from pyxel_wavetable.presets import _PRESETS, _preset_definitions


def test_preset_inventory():
    definitions = _preset_definitions()
    assert {d.name for d in definitions} == {
        "bell", "bass", "lead", "organ", "soft", "tom", "woodblock", "cowbell", "metallic", "click",
    }
    assert len({d.name for d in definitions}) == len(definitions) == 10
    assert sum(d.category == "tonal" for d in definitions) == 5
    assert sum(d.category == "percussion" for d in definitions) == 5


@pytest.mark.parametrize("definition", _preset_definitions(), ids=lambda d: d.name)
def test_definition_and_public_defaults(definition):
    assert definition.generator in ("pm", "harmonics")
    if definition.generator == "pm":
        assert type(definition.ratio) is int and definition.ratio >= 1
        assert definition.index >= 0
    else:
        assert isinstance(definition.amplitudes, tuple) and definition.amplitudes
    signature = inspect.signature(getattr(wt, definition.name))
    for name in ["size", "sample_bits", "gain"]:
        assert signature.parameters[name].default == getattr(definition, name)


def test_definitions_are_immutable():
    with pytest.raises(FrozenInstanceError):
        _PRESETS["bell"].ratio = 1
    with pytest.raises(TypeError):
        _PRESETS["bell"] = _PRESETS["lead"]
