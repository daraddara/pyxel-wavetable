from pathlib import Path
import runpy
from types import SimpleNamespace

import pyxel
import pytest

lab = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/bgm_compare.py"))


def signature(tone):
    return tone.mode, tone.sample_bits, list(tone.wavetable), tone.gain


@pytest.fixture
def comparison(monkeypatch):
    tracks = ("T120 @2 @ENV1{127,10,0} O4 C", "T120 @0 O2 C", "T120 @1 O4 E", "T120 @3 O5 C")
    calls = []

    class Sound:
        def mml(self, text):
            self.text = text
            calls.append(("mml", text))

        def total_sec(self):
            return .5

    class Music:
        def set(self, *sequences):
            self.seqs = sequences

    def generate(**kwargs):
        calls.append(("generate", kwargs))
        return list(tracks)

    fake = SimpleNamespace(Tone=pyxel.Tone, Sound=Sound, Music=Music,
                           tones=[pyxel.Tone() for _ in range(4)], sounds=[None]*4,
                           musics=[None], active=False, gen_bgm=generate)
    for i, tone in enumerate(fake.tones):
        tone.gain = [1, .3, .3, .6][i]
    fake.tones[3].mode = 2

    def stop():
        fake.active = False
        calls.append(("stop",))

    def playm(index, **kwargs):
        fake.active = True
        calls.append(("playm", index, kwargs))

    fake.stop, fake.playm = stop, playm
    fake.play_pos = lambda ch: (ch, .5) if fake.active else None
    monkeypatch.setitem(lab["Comparison"].__init__.__globals__, "pyxel", fake)
    model = lab["Comparison"]()
    return model, fake, tracks, calls


def test_same_score_both_modes_and_exact_restore(comparison):
    model, fake, tracks, calls = comparison
    native = [signature(t) for t in fake.tones]
    score = fake.musics[0]
    model.restart()
    model.select_mode(True)
    assert fake.active
    assert signature(fake.tones[0]) != native[0]
    assert signature(fake.tones[3]) == native[3]
    assert model.mmls == tracks
    assert tuple(s.text for s in fake.sounds) == tracks
    assert fake.musics[0] is score
    assert len([call for call in calls if call[0] == "generate"]) == 1
    assert len([call for call in calls if call[0] == "mml"]) == 4
    model.select_mode(False)
    assert [signature(t) for t in fake.tones] == native
    assert len(fake.tones) == 4


def test_noise_replacement_is_explicit(comparison):
    model, fake, _, _ = comparison
    native = signature(fake.tones[3])
    model.select_mode(True)
    assert signature(fake.tones[3]) == native
    model.toggle_noise()
    assert fake.tones[3].mode == 0
    assert signature(fake.tones[3]) != native
    assert fake.tones[3].gain == model.native[3].gain
    model.select_mode(False)
    assert signature(fake.tones[3]) == native


def test_stopped_mode_change_stays_stopped(comparison):
    model, fake, _, _ = comparison
    assert not fake.active
    model.select_mode(True)
    assert not fake.active
    model.toggle_noise()
    assert not fake.active


def test_generation_parameters_and_loop(comparison):
    model, fake, tracks, calls = comparison
    model.loop = False
    model.restart()
    settings = lab["SongSettings"](preset=7, transp=-2, instr=1, seed=123)
    model.generate(settings)
    assert model.settings == settings
    assert ("generate", dict(preset=7, transp=-2, instr=1, seed=123, play=False)) in calls
    assert calls[-1] == ("playm", 0, {"loop": False})
    assert model.mmls == tracks


def test_generation_failure_keeps_previous_song(comparison):
    model, fake, tracks, _ = comparison
    model.restart()
    score, settings = fake.musics[0], model.settings

    def fail(**kwargs):
        raise ValueError("generation failed")

    fake.gen_bgm = fail
    with pytest.raises(ValueError):
        model.generate(lab["SongSettings"](seed=100))
    assert fake.active
    assert model.settings == settings and model.mmls == tracks
    assert fake.musics[0] is score


def test_native_noise_metadata_is_preserved(comparison):
    model, fake, _, _ = comparison
    # Pyxel's built-in noise has sample_bits=0, which the wavetable setter rejects.
    noise = SimpleNamespace(mode=2, sample_bits=0, wavetable=[], gain=.6)
    model.native = (*model.native[:3], noise)
    model.apply_bank()
    model.select_mode(True)
    assert fake.tones[3] is noise
    model.toggle_noise()
    assert fake.tones[3].mode == 0
    model.select_mode(False)
    assert fake.tones[3] is noise


@pytest.mark.parametrize("name,value,direction,expected", [
    ("preset", 7, 1, 7), ("instr", 0, -1, 0), ("transp", -5, -1, -5),
    ("seed", 0, -1, 0), ("seed", 42, 1, 43),
])
def test_settings_limits(name, value, direction, expected):
    settings = lab["SongSettings"](**{name: value})
    adjusted = settings.adjust(name, direction)
    assert getattr(adjusted, name) == expected
    assert getattr(settings, name) == value
