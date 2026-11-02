"""Test the example's settings and MML handoff without running its UI."""

from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest

import pyxel_wavetable as wt

lab = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples" / "tone_lab.py"))
ToneSettings, Preview = lab["ToneSettings"], lab["Preview"]


@pytest.mark.parametrize("generator", lab["GENERATORS"])
def test_generator_settings(generator):
    settings = ToneSettings(generator=generator, size=64, sample_bits=4, gain=.25)
    tone = settings.generate()
    assert len(tone.wavetable) == 64
    assert tone.sample_bits == 4
    assert tone.gain == pytest.approx(.25)
    assert tone.mode == 0
    assert all(0 <= x <= 15 for x in tone.wavetable)


@pytest.mark.parametrize("generator", ["pm", "harmonics", "pulse"])
def test_generated_code_matches_settings(generator):
    settings = ToneSettings(generator=generator, ratio=5, index=2.3, duty=.125,
                            amplitudes=[.1, .2, .3, .4, .5, .6, .7, .8])
    # Only evaluate code generated here, never custom/user MML.
    from_code = eval(settings.code(), {"wt": wt})
    assert list(from_code.wavetable) == list(settings.generate().wavetable)
    assert from_code.gain == pytest.approx(settings.gain)
    assert f"wt.{generator}(" in settings.code()


@pytest.mark.parametrize("name", lab["DEFAULT_MMLS"])
def test_preview_selection_and_auto_tone(name):
    preview = Preview(name=name)
    assert preview.mml(12) == "@12 " + lab["DEFAULT_MMLS"][name]
    preview.auto_tone = False
    assert preview.mml(12) == lab["DEFAULT_MMLS"][name]


def test_custom_preserves_explicit_tone_commands():
    preview = Preview(name="custom", custom="T120 C @2 D")
    assert preview.mml(4) == "@4 T120 C @2 D"
    preview.auto_tone = False
    assert preview.mml(4) == preview.custom


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_custom_is_visible_error(text, monkeypatch):
    def unexpected_play(*args, **kwargs):
        pytest.fail("Empty MML must not reach Pyxel")

    monkeypatch.setattr(lab["pyxel"], "play", unexpected_play)
    preview = Preview(name="custom", custom=text)
    assert preview.play(4) is False
    assert "empty" in preview.error
    assert preview.custom == text


def test_mml_failure_and_recovery(monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("invalid MML")

    preview = Preview(name="custom", custom="bad MML")
    monkeypatch.setattr(lab["pyxel"], "play", fail)
    assert preview.play(4) is False
    assert "invalid MML" in preview.error
    assert preview.custom == "bad MML"
    calls = []
    monkeypatch.setattr(lab["pyxel"], "play", lambda *args, **kwargs: calls.append((args, kwargs)))
    preview.custom = "O3 C D"
    assert preview.play(4) is True
    assert preview.error == ""
    assert calls == [((0, "@4 O3 C D"), {"loop": True})]


def test_parameter_steps_and_limits():
    settings = ToneSettings()
    for _ in range(300):
        for name in ["size", "sample_bits", "gain", "ratio", "index", "duty", "H1"]:
            settings.adjust(name, -1)
    assert (settings.size, settings.sample_bits, settings.gain, settings.ratio,
            settings.index, settings.duty, settings.amplitudes[0]) == (32, 1, 0, 1, 0, 1/32, 0)
    for _ in range(300):
        for name in ["size", "sample_bits", "gain", "ratio", "index", "duty", "H8"]:
            settings.adjust(name, 1)
    assert (settings.size, settings.sample_bits, settings.gain, settings.ratio,
            settings.index, settings.duty, settings.amplitudes[7]) == (512, 16, 1, 16, 10, 31/32, 1)


@pytest.fixture
def editor():
    app = lab["App"].__new__(lab["App"])
    app.settings = ToneSettings()
    app.preset_definitions = lab["_preset_definitions"]()
    app.preset_cursor = 0
    app.preview = Preview()
    app.focus, app.editing = "tone", False
    app.cursor, app.view_start, app.selected_all = 0, 0, False
    app.notice = app.clipboard_error = ""
    store = {"text": "O3 C E G"}
    app.clipboard = SimpleNamespace(read=lambda: store["text"],
                                    write=lambda text: store.update(text=text))
    return app, store


def test_copy_buttons_have_explicit_targets(editor):
    app, store = editor
    original = app.preview.custom
    app.inside = lambda rect: rect == lab["CODE_COPY"]
    app.mouse_click()
    assert store["text"] == app.settings.code()
    assert app.focus == "code" and not app.editing
    assert app.preview.custom == original
    app.preview.name = "bass"
    app.inside = lambda rect: rect == lab["MML_COPY"]
    app.mouse_click()
    assert store["text"] == lab["DEFAULT_MMLS"]["bass"]
    assert app.focus == "mml"


def test_paste_button_imports_to_custom(editor):
    app, store = editor
    app.inside = lambda rect: rect == lab["MML_PASTE"]
    app.mouse_click()
    assert app.preview.custom == store["text"]
    assert app.preview.name == "custom" and app.editing and app.focus == "mml"
    assert app.cursor == len(store["text"])


def test_paste_at_cursor_and_replace_selection(editor):
    app, store = editor
    app.focus_mml()
    app.preview.custom = "CE"
    app.cursor = 1
    store["text"] = " D "
    app.paste_mml()
    assert app.preview.custom == "C D E"
    app.selected_all = True
    store["text"] = "O3\nC\tG"
    app.paste_mml()
    assert app.preview.custom == "O3 C G"
    assert not app.selected_all


def test_clipboard_error_preserves_mml(editor):
    app, _ = editor
    original = app.preview.custom

    def fail():
        raise RuntimeError("clipboard unavailable")

    app.clipboard.read = fail
    app.paste_mml()
    assert "clipboard unavailable" in app.clipboard_error
    assert app.preview.custom == original
    assert not app.editing


@pytest.mark.parametrize("playing", [False, True])
def test_preview_switch_restarts_only_when_playing(editor, monkeypatch, playing):
    app, _ = editor
    app.tone_index = 4
    app.preview.loop = False
    app.preview.auto_tone = False
    events = []
    monkeypatch.setattr(lab["pyxel"], "play_pos", lambda ch: (0, .5) if playing else None)
    monkeypatch.setattr(lab["pyxel"], "stop", lambda ch: events.append(("stop", ch)))
    monkeypatch.setattr(app, "regenerate", lambda: None)
    monkeypatch.setattr(lab["pyxel"], "play", lambda *args, **kwargs: events.append(("play", args, kwargs)))
    app.cycle_preview()
    assert app.preview.name == "bass"
    assert events == ([("stop", 0), ("play", (0, lab["DEFAULT_MMLS"]["bass"]), {"loop": False})]
                      if playing else [])


def test_switch_to_invalid_custom_stops_old_loop(editor, monkeypatch):
    app, _ = editor
    app.tone_index = 4
    app.preview.name = next(reversed(lab["DEFAULT_MMLS"]))
    app.preview.custom = ""
    stopped = []
    monkeypatch.setattr(lab["pyxel"], "play_pos", lambda ch: (0, .5))
    monkeypatch.setattr(lab["pyxel"], "stop", stopped.append)
    monkeypatch.setattr(app, "regenerate", lambda: None)
    app.cycle_preview()
    assert app.preview.name == "custom"
    assert stopped == [0]
    assert "empty" in app.preview.error


@pytest.mark.parametrize("playing", [False, True])
def test_space_toggles_playback(editor, monkeypatch, playing):
    app, _ = editor
    events = []
    monkeypatch.setattr(lab["pyxel"], "play_pos", lambda ch: (0, .5) if playing else None)
    monkeypatch.setattr(lab["pyxel"], "stop", lambda ch: events.append("stop"))
    monkeypatch.setattr(app, "play", lambda: events.append("play"))
    app.toggle_playback()
    assert events == ["stop" if playing else "play"]


def test_space_in_mml_editor_does_not_toggle(editor, monkeypatch):
    app, _ = editor
    app.focus_mml()
    app.clipboard.poll = lambda: None
    events = []
    monkeypatch.setattr(lab["pyxel"], "btnp", lambda key, *args: key == lab["pyxel"].KEY_SPACE)
    monkeypatch.setattr(lab["pyxel"], "btn", lambda key: False)
    monkeypatch.setattr(app, "toggle_playback", lambda: events.append("toggle"))
    monkeypatch.setattr(app, "edit_mml", lambda: events.append("edit"))
    app.update()
    assert events == ["edit"]


@pytest.mark.parametrize("definition", lab["_preset_definitions"](), ids=lambda d: d.name)
def test_preset_expands_to_editable_generator(definition):
    settings = ToneSettings.from_preset(definition)
    assert settings.preset_name == definition.name
    assert settings.generator == definition.generator
    assert settings.gain == definition.gain
    assert len(settings.amplitudes) == 8
    tone = settings.generate()
    original = getattr(wt, definition.name)()
    assert list(tone.wavetable) == list(original.wavetable)
    assert tone.gain == original.gain
    if definition.generator == "harmonics":
        assert settings.amplitudes == list(definition.amplitudes) + [0.0]*(8-len(definition.amplitudes))
    assert f"wt.{definition.generator}(" in settings.code()
    assert f"wt.{definition.name}(" not in settings.code()


def test_specific_preset_values():
    definitions = {d.name: d for d in lab["_preset_definitions"]()}
    bell = ToneSettings.from_preset(definitions["bell"])
    lead = ToneSettings.from_preset(definitions["lead"])
    cowbell = ToneSettings.from_preset(definitions["cowbell"])
    bass = ToneSettings.from_preset(definitions["bass"])
    assert (bell.ratio, bell.index) == (5, 1.6)
    assert (lead.ratio, lead.index) == (2, 1.2)
    assert (cowbell.ratio, cowbell.index, cowbell.gain) == (3, 1.7, .4)
    assert bass.amplitudes == [1, .4, .15, 0, 0, 0, 0, 0]


@pytest.mark.parametrize("preset,parameter,direction", [
    ("bell", "generator", 1), ("bell", "size", 1), ("bell", "sample_bits", 1),
    ("bell", "gain", 1), ("bell", "ratio", 1), ("bell", "index", 1), ("bass", "H1", -1),
])
def test_tone_edits_mark_custom(preset, parameter, direction):
    definition = next(d for d in lab["_preset_definitions"]() if d.name == preset)
    settings = ToneSettings.from_preset(definition)
    settings.adjust(parameter, direction)
    assert settings.preset_name is None


def test_reloading_preset_and_non_tone_edits(editor, monkeypatch):
    app, _ = editor
    app.preset_cursor = next(i for i, d in enumerate(app.preset_definitions) if d.name == "cowbell")
    monkeypatch.setattr(app, "regenerate", lambda: None)
    monkeypatch.setattr(lab["pyxel"], "play_pos", lambda ch: None)
    app.load_preset()
    assert app.settings.preset_name == "cowbell"
    app.focus_mml()
    app.selected_all = True
    app.insert_mml("T120 O3 C E G")
    app.cycle_preview()
    app.preview.loop = False
    app.preview.auto_tone = False
    assert app.settings.preset_name == "cowbell"
    app.settings.adjust("index", 1)
    assert app.settings.preset_name is None
    app.load_preset()
    assert app.settings.preset_name == "cowbell"
    assert (app.settings.ratio, app.settings.index, app.settings.gain) == (3, 1.7, .4)
    assert app.preview.custom == "T120 O3 C E G"
    assert app.preview.loop is False
    assert app.preview.auto_tone is False


def test_editing_harmonics_does_not_mutate_definition():
    definition = next(d for d in lab["_preset_definitions"]() if d.name == "bass")
    first, second = ToneSettings.from_preset(definition), ToneSettings.from_preset(definition)
    first.adjust("H2", 1)
    assert second.amplitudes[1] == definition.amplitudes[1] == .4


def test_pulse_edit_and_no_op_limit():
    settings = ToneSettings(generator="pulse", preset_name="example")
    settings.adjust("duty", 1)
    assert settings.preset_name is None
    settings = ToneSettings(ratio=1, preset_name="example")
    settings.adjust("ratio", -1)
    assert settings.preset_name == "example"
