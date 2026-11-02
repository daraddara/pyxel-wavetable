"""Predictive diagnostics: no window, sound generation or playback required."""

import csv
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
lab = runpy.run_path(str(ROOT / "examples/tone_lab.py"))
predict = lab["predict_pitch"]
PitchRange = lab["PitchRange"]


def test_note_mapping_and_frequency():
    assert lab["note_name"](36) == "C2"
    assert lab["note_name"](61) == "C#4"
    assert lab["note_name"](0) == "C-1"
    assert lab["note_name"](127) == "G9"
    assert lab["note_frequency"](69) == 440
    assert lab["note_frequency"](60) == pytest.approx(261.6255653)
    assert lab["note_frequency"](48) == pytest.approx(130.81278265)


@pytest.mark.parametrize("note,size,cents", [
    (36, 128, -1.778), (48, 128, -1.778), (72, 128, -17.882),
    (72, 32, -1.778), (84, 128, 47.45), (79, 128, -15.934),
])
def test_representative_notes(note, size, cents):
    assert predict(note, size)[2] == pytest.approx(cents, abs=.01)


def test_confirmed_model_matches_measurement_csv():
    with (ROOT / "docs/wavetable-pitch.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 366
    for row in rows:
        target, actual, cents = predict(int(row["midi"]), int(row["size"]))
        assert lab["note_name"](int(row["midi"])) == row["note"]
        assert target == pytest.approx(float(row["target_hz"]), abs=1e-6)
        assert actual == pytest.approx(float(row["predicted_hz"]), abs=1e-6)
        # CSV frequency measurements have FFT interpolation error; cents are rounded.
        assert actual == pytest.approx(float(row["measured_hz"]), abs=.06)
        assert cents == pytest.approx(float(row["cents"]), abs=.001)


def test_integer_clock_and_one_clock_floor():
    target, actual, cents = predict(72, 128)
    assert actual == pytest.approx(1_789_773/(128*27))
    assert cents < 0 and actual < target
    assert predict(127, 512)[1] == 1_789_773/512


def test_range_aggregation_and_current_size():
    rows = PitchRange(72, 83).series(128)
    assert [r["size"] for r in rows] == [32, 64, 128, 256, 512]
    assert [r["size"] for r in rows if r["current"]] == [128]
    assert [r["max"] for r in rows[:3]] == pytest.approx([12.02, 19.16, 36.66], abs=.01)
    for row in rows:
        errors = [predict(note, row["size"])[2] for note in range(72, 84)]
        assert row["errors"] == tuple(errors)
        assert row["avg"] == pytest.approx(sum(abs(v) for v in errors)/12)
        assert row["max"] == max(abs(v) for v in errors)
    assert PitchRange(72, 72).series(32)[0]["avg"] == abs(predict(72, 32)[2])


@pytest.mark.parametrize("start,end", [(0, 127), (72, 72), (127, 127), (48, 83)])
def test_plot_coordinates_are_finite_and_bounded(start, end):
    series, limit = PitchRange(start, end).plot(512)
    assert limit >= 1
    assert series[-1]["current"]
    for row in series:
        assert len(row["points"]) == end-start+1
        assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y in row["points"])
        assert row["points"][0][1] == pytest.approx(.5-row["errors"][0]/(2*limit))


@pytest.mark.parametrize("note", [-1, 128, 1.2, True, "C3", None])
def test_invalid_notes(note):
    with pytest.raises(ValueError):
        predict(note, 128)


@pytest.mark.parametrize("size", [0, -1, 32.5, True, "128", None])
def test_invalid_sizes(size):
    with pytest.raises(ValueError):
        predict(72, size)


def test_reversed_and_invalid_ranges():
    with pytest.raises(ValueError):
        PitchRange(83, 48)
    with pytest.raises(ValueError):
        lab["pitch_summary"](83, 48, 32)
    with pytest.raises(ValueError):
        PitchRange(-1, 48)
    span = PitchRange(72, 72)
    span.adjust("start", 1)
    span.adjust("end", -1)
    assert (span.start, span.end) == (72, 72)
    span = PitchRange(0, 127)
    span.adjust("start", -1)
    span.adjust("end", 1)
    assert (span.start, span.end) == (0, 127)
    with pytest.raises(ValueError):
        span.adjust("other", 1)


def test_diagnostic_clicks_do_not_generate_or_play(monkeypatch):
    app = lab["App"].__new__(lab["App"])
    app.pitch_range = PitchRange()
    app.show_pitch = False
    app.settings = lab["ToneSettings"]()
    original = app.settings.code()

    def forbidden(*args, **kwargs):
        pytest.fail("diagnostic operations must not invoke audio")

    for name in ("Sound", "Music", "play", "playm", "stop"):
        monkeypatch.setattr(lab["pyxel"], name, forbidden)
    app.regenerate = forbidden
    app.inside = lambda rect: rect == lab["PITCH_TOGGLE"]
    app.mouse_click()
    assert app.show_pitch and app.focus == "pitch"
    app.inside = lambda rect: rect == lab["PITCH_CONTROLS"]["start_up"]
    app.mouse_click()
    assert app.pitch_range.start == 49
    assert app.settings.code() == original
    assert app.pitch_range.series(app.settings.size)[2]["current"]
    app.inside = lambda rect: rect == lab["PITCH_TOGGLE"]
    app.mouse_click()
    assert not app.show_pitch
