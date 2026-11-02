import csv
import math
from pathlib import Path
import runpy

import pytest

ROOT = Path(__file__).resolve().parents[1]
pitch = runpy.run_path(str(ROOT / "examples/_bgm_pitch.py"))


def test_generated_subset_tracks_nested_repeats_octaves_and_tones():
    notes, vib = pitch["score_notes"]((
        "T120 @VIB1{60,20,25} @ENV1{0,0,127} @2 O4 [C >D <]2 @0 [E [F#]2]2 R4 &8.",
    ))
    assert notes == ((64, 66), (), (60, 74), ())
    assert vib == 25


@pytest.mark.parametrize("text", ["O5 C @D20", "[C]0", "[C", "C]2", "@4 C", "O20 C", "[C]999999", "O5 C !"])
def test_unhandled_input_is_rejected(text):
    with pytest.raises(ValueError):
        pitch["score_notes"]((text,))


def test_repeat_notes_use_compile_time_octaves_and_playback_tone_state():
    notes, _ = pitch["score_notes"](("@0 O2 [C >]3 C",))
    assert notes[0] == (36, 48)
    notes, _ = pitch["score_notes"](("@0 O4 [C @1 D]2",))
    assert notes[0] == (60,)
    assert notes[1] == (60, 62)


def test_pitch_equation_against_committed_measurements():
    with (ROOT / "docs/wavetable-pitch.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            assert pitch["pitch_error"](int(row["midi"]), int(row["size"])) == pytest.approx(float(row["cents"]), abs=.001)


@pytest.mark.parametrize("target", [10, 25])
def test_largest_candidate_meets_conservative_target(target):
    notes = ((48, 60), (), (72, 83), ())
    sizes = pitch["choose_sizes"](notes, 25, target)
    for group, size in zip(notes, sizes):
        assert pitch["error_bound"](group, size, 25) <= target
        if group:
            larger = [s for s in pitch["SIZES"] if s > size]
            assert all(pitch["error_bound"](group, s, 25) > target for s in larger)
    assert pitch["choose_sizes"](notes, 25, None) == (128,)*4


@pytest.mark.parametrize("target", [10, 25])
def test_bound_includes_dense_vibrato_sweep(target):
    notes = ((72, 83), (), (), ())
    size = pitch["choose_sizes"](notes, 25, target)[0]
    bound = pitch["error_bound"](notes[0], size, 25)
    for step in range(2401):
        # Sweep C5..B5 and +/-25 cents, including between authored notes.
        note = 71.75+11.5*step/2400
        assert abs(pitch["pitch_error"](note, size)) <= bound+1e-9


def test_unattainable_target_is_not_reported_as_met():
    with pytest.raises(ValueError, match="cannot be met"):
        pitch["choose_sizes"](((127,), (), (), ()), 25, 10)
    assert math.isinf(pitch["error_bound"]((127,), 512, 25))
