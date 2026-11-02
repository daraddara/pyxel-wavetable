"""Tone editor; all sequencing and MML belong to Pyxel."""

from dataclasses import dataclass, field
from pathlib import Path
from math import floor, log2

import pyxel
import pyxel_wavetable as wt
from pyxel_wavetable.presets import _preset_definitions

GENERATORS = ("pm", "harmonics", "pulse", "sine", "saw", "triangle", "square")
DEFAULT_MMLS = {
    "melody": "T120 O3 L8 C D E G A G E D",
    "bass": "T110 O2 L8 C C G G A G E C",
    "short": "T120 O4 L16 C R C R C R C R",
    "perc_low": "T120 V100 Q100 L16 @ENV1{127,10,0} O2 C R C R C8 R8 G R C R C8 R8",
    "perc_high": "T120 V100 Q100 L16 @ENV1{127,6,0} O5 C R C R C8 R8 G R C R C8 R8",
}
PREVIEWS = (*DEFAULT_MMLS, "custom")
SIZES = (32, 64, 128, 256, 512)
CHANNEL = 0
MARGIN, GAP = 8, 8
TONE_W, DETAIL_W = 176, 368
WIDTH = 2 * MARGIN + TONE_W + GAP + DETAIL_W
HEIGHT = 424
RIGHT_X = MARGIN + TONE_W + GAP
CODE_COPY = (WIDTH-MARGIN-76, 172, 68, 12)
MML_COPY = (WIDTH-MARGIN-148, 336, 68, 12)
MML_PASTE = (WIDTH-MARGIN-76, 336, 68, 12)
PRESET_PREV = (260, 34, 24, 12)
PRESET_NEXT = (292, 34, 24, 12)
PRESET_LOAD = (324, 34, 64, 12)
PITCH_TOGGLE = (WIDTH-116, 6, 108, 12)
PITCH_CONTROLS = {
    "start_down": (RIGHT_X+8, 84, 18, 12),
    "start_up": (RIGHT_X+84, 84, 18, 12),
    "end_down": (RIGHT_X+156, 84, 18, 12),
    "end_up": (RIGHT_X+232, 84, 18, 12),
}
PITCH_GRAPH = (RIGHT_X+48, 194, DETAIL_W-64, 62)
PITCH_COLORS = (11, 12, 10, 14, 9)
# Verified against the 366 measurements in docs/wavetable-pitch.csv.
# This is a Pyxel 2.9.9 prediction, not an audio measurement or correction.
PITCH_CLOCK_HZ = 1_789_773
UI_SCALE = 2
FONT_SIZE = 16
TEXT_LINE = 10  # Logical units; 20 physical pixels between text baselines.
FONT_PATH = Path(__file__).resolve().parent / "assets/fonts/RobotoMono-Medium.ttf"


def ui_rect(x, y, w, h, color):
    pyxel.rect(x*UI_SCALE, y*UI_SCALE, w*UI_SCALE, h*UI_SCALE, color)


def ui_border(x, y, w, h, color):
    pyxel.rectb(x*UI_SCALE, y*UI_SCALE, w*UI_SCALE, h*UI_SCALE, color)


def ui_line(x1, y1, x2, y2, color):
    pyxel.line(x1*UI_SCALE, y1*UI_SCALE, x2*UI_SCALE, y2*UI_SCALE, color)


def note_frequency(note):
    """MIDI convention: 60 = C4, 69 = A4; unrelated to Sound.set octaves."""
    if type(note) is not int or not 0 <= note <= 127:
        raise ValueError("note must be an integer MIDI note in 0..127")
    return 440.0 * 2 ** ((note-69)/12)


def note_name(note):
    note_frequency(note)  # Validate the same domain as the model.
    return ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")[note % 12] + str(note//12-1)


def predict_pitch(note, size):
    """Return target Hz, predicted Hz and signed cents; no Pyxel calls."""
    target = note_frequency(note)
    if type(size) is not int or size <= 0:
        raise ValueError("size must be a positive integer")
    # Positive values: Rust f64::round rounds halfway away from zero.
    clocks = max(1, floor(PITCH_CLOCK_HZ/(size*target)+0.5))
    actual = PITCH_CLOCK_HZ/(size*clocks)
    return target, actual, 1200*log2(actual/target)


def pitch_summary(start, end, size):
    note_frequency(start)
    note_frequency(end)
    if start > end:
        raise ValueError("range start must not exceed end")
    errors = tuple(predict_pitch(note, size)[2] for note in range(start, end+1))
    return {"size": size, "errors": errors, "max": max(map(abs, errors)),
            "avg": sum(map(abs, errors))/len(errors)}


@dataclass
class PitchRange:
    start: int = 48  # C3
    end: int = 83  # B5

    def __post_init__(self):
        note_frequency(self.start)
        note_frequency(self.end)
        if self.start > self.end:
            raise ValueError("range start must not exceed end")

    def adjust(self, endpoint, direction):
        if endpoint not in ("start", "end") or direction not in (-1, 1):
            raise ValueError("expected start/end and direction -1/+1")
        lower, upper = (0, self.end) if endpoint == "start" else (self.start, 127)
        setattr(self, endpoint, max(lower, min(upper, getattr(self, endpoint)+direction)))

    def series(self, current_size):
        return [dict(pitch_summary(self.start, self.end, size),
                     current=size == current_size, color=color)
                for size, color in zip(SIZES, PITCH_COLORS)]

    def plot(self, current_size):
        series = [row for row in self.series(current_size) if row["size"] <= 128 or row["current"]]
        limit = max(1, max(row["max"] for row in series)) * 1.1
        # Normalized coordinates keep extremes and single-note ranges in bounds.
        for row in series:
            row["points"] = tuple((i/max(1, self.end-self.start), .5-error/(2*limit))
                                  for i, error in enumerate(row["errors"]))
        return series, limit


class TextClipboard:
    """Optional desktop clipboard support, confined to this example."""

    def __init__(self):
        self.root = None

    def window(self):
        if self.root is None:
            import tkinter
            self.root = tkinter.Tk()
            self.root.withdraw()
        return self.root

    def read(self):
        return self.window().clipboard_get()

    def write(self, text):
        root = self.window()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()

    def poll(self):
        if self.root is not None:
            self.root.update()


@dataclass
class ToneSettings:
    generator: str = "pm"
    size: int = wt.DEFAULT_SIZE
    sample_bits: int = wt.DEFAULT_SAMPLE_BITS
    gain: float = wt.DEFAULT_GAIN
    ratio: int = 3
    index: float = 1.8
    duty: float = 0.25
    amplitudes: list[float] = field(default_factory=lambda: [1, .5, .25, .1, 0, 0, 0, 0])
    preset_name: str | None = None

    @classmethod
    def from_preset(cls, definition):
        settings = cls(generator=definition.generator, size=definition.size,
                       sample_bits=definition.sample_bits, gain=definition.gain,
                       ratio=definition.ratio, index=definition.index,
                       preset_name=definition.name)
        if definition.generator == "harmonics":
            settings.amplitudes = list(definition.amplitudes)
            settings.amplitudes += [0.0] * max(0, 8-len(settings.amplitudes))
        return settings

    def generate(self):
        common = dict(size=self.size, sample_bits=self.sample_bits, gain=self.gain)
        if self.generator == "pm":
            return wt.pm(ratio=self.ratio, index=self.index, **common)
        if self.generator == "harmonics":
            return wt.harmonics(self.amplitudes, **common)
        if self.generator == "pulse":
            return wt.pulse(duty=self.duty, **common)
        return getattr(wt, self.generator)(**common)

    def rows(self):
        rows = ["generator", "size", "sample_bits", "gain"]
        if self.generator == "pm":
            rows += ["ratio", "index"]
        elif self.generator == "pulse":
            rows += ["duty"]
        elif self.generator == "harmonics":
            rows += [f"H{i+1}" for i in range(8)]
        return rows

    def value(self, name):
        if name.startswith("H"):
            return f"{self.amplitudes[int(name[1:])-1]:.2f}"
        value = getattr(self, name)
        return f"{value:.5f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)

    def adjust(self, name, direction):
        before = self.code()
        if name == "generator":
            self.generator = GENERATORS[(GENERATORS.index(self.generator) + direction) % len(GENERATORS)]
        elif name == "size":
            self.size = SIZES[max(0, min(len(SIZES)-1, SIZES.index(self.size) + direction))]
        elif name == "sample_bits":
            self.sample_bits = max(1, min(16, self.sample_bits + direction))
        elif name == "ratio":
            self.ratio = max(1, min(16, self.ratio + direction))
        elif name == "duty":
            self.duty = max(1/32, min(31/32, self.duty + direction/32))
        else:
            if name.startswith("H"):
                i = int(name[1:])-1
                self.amplitudes[i] = round(max(0, min(1, self.amplitudes[i] + direction*.05)), 2)
            else:
                step, maximum = (.1, 10) if name == "index" else (.05, 1)
                setattr(self, name, round(max(0, min(maximum, getattr(self, name) + direction*step)), 2))
        if self.code() != before:
            self.preset_name = None

    def code(self):
        lines = [f"wt.{self.generator}("]
        if self.generator == "pm":
            lines += [f"    ratio={self.ratio},", f"    index={self.index:.2f},"]
        elif self.generator == "pulse":
            lines += [f"    duty={self.duty},"]
        elif self.generator == "harmonics":
            values = [f"{a:.2f}" for a in self.amplitudes]
            lines += ["    [" + ", ".join(values[:4]) + ",",
                      "     " + ", ".join(values[4:]) + "],"]
        lines += [f"    size={self.size},", f"    sample_bits={self.sample_bits},",
                  f"    gain={self.gain:.2f},", ")"]
        return "\n".join(lines)


@dataclass
class Preview:
    name: str = "melody"
    custom: str = DEFAULT_MMLS["melody"]
    auto_tone: bool = True
    loop: bool = True
    error: str = ""

    def mml(self, tone_index):
        text = self.custom if self.name == "custom" else DEFAULT_MMLS[self.name]
        if not text.strip():
            raise ValueError("CUSTOM MML is empty")
        return f"@{tone_index} {text}" if self.auto_tone else text

    def play(self, tone_index):
        try:
            pyxel.play(CHANNEL, self.mml(tone_index), loop=self.loop)
        except Exception as exc:
            self.error = f"MML ERROR: {exc}"
            return False
        self.error = ""
        return True


class App:
    def __init__(self):
        pyxel.init(WIDTH*UI_SCALE, HEIGHT*UI_SCALE, title="Wavetable: Tone Lab",
                   quit_key=pyxel.KEY_NONE, display_scale=1)
        self.font = pyxel.Font(str(FONT_PATH), FONT_SIZE)
        self.char_width = self.font.text_width("M") / UI_SCALE
        pyxel.mouse(True)
        self.settings = ToneSettings()
        self.pitch_range = PitchRange()
        self.show_pitch = False
        self.preset_definitions = _preset_definitions()
        self.preset_cursor = 0
        self.preview = Preview()
        self.tone_index = wt.add_tone(self.settings.generate())
        self.row = 0
        self.editing = False
        self.focus = "tone"
        self.clipboard = TextClipboard()
        self.notice = ""
        self.clipboard_error = ""
        self.cursor = len(self.preview.custom)
        self.selected_all = False
        self.view_start = 0
        pyxel.run(self.update, self.draw)

    def regenerate(self):
        # Mutate one existing slot, only on a parameter change or PLAY.
        generated = self.settings.generate()
        target = pyxel.tones[self.tone_index]
        target.mode = generated.mode
        target.sample_bits = generated.sample_bits
        target.wavetable[:] = generated.wavetable
        target.gain = generated.gain

    def load_preset(self):
        definition = self.preset_definitions[self.preset_cursor]
        self.settings = ToneSettings.from_preset(definition)
        self.row = 0
        self.editing, self.selected_all = False, False
        self.focus = "tone"
        self.regenerate()
        self.notice = f"LOADED {definition.name.upper()} AS EDITABLE PARAMETERS"

    def browse_preset(self, direction):
        self.preset_cursor = (self.preset_cursor+direction) % len(self.preset_definitions)
        self.editing, self.selected_all = False, False
        self.focus = "tone"

    def play(self):
        try:
            self.regenerate()
        except Exception as exc:
            self.preview.error = f"TONE ERROR: {exc}"
            return
        self.preview.play(self.tone_index)

    def focus_mml(self):
        self.preview.name = "custom"
        self.editing = True
        self.focus = "mml"
        self.cursor = len(self.preview.custom)
        self.selected_all = False

    def cycle_preview(self):
        playing = pyxel.play_pos(CHANNEL) is not None
        self.preview.name = PREVIEWS[(PREVIEWS.index(self.preview.name)+1) % len(PREVIEWS)]
        if playing:
            pyxel.stop(CHANNEL)
            self.play()

    def toggle_playback(self):
        if pyxel.play_pos(CHANNEL) is not None:
            pyxel.stop(CHANNEL)
        else:
            self.play()

    def insert_mml(self, text):
        text = "".join(c if 32 <= ord(c) < 127 else " "
                       for c in text if c.isprintable() or c.isspace())
        if self.selected_all:
            self.preview.custom = ""
            self.cursor = 0
            self.selected_all = False
        self.preview.custom = self.preview.custom[:self.cursor] + text + self.preview.custom[self.cursor:]
        self.cursor += len(text)

    def copy_text(self, area):
        self.focus = area
        if area == "code":
            self.editing = False
            self.selected_all = False
            text = self.settings.code()
        else:
            text = self.preview.custom if self.preview.name == "custom" else DEFAULT_MMLS[self.preview.name]
        try:
            self.clipboard.write(text)
        except Exception as exc:
            self.clipboard_error = f"CLIPBOARD ERROR: {exc}"
            return
        self.clipboard_error = ""
        self.notice = f"COPIED {area.upper()} TO OS CLIPBOARD"

    def paste_mml(self):
        try:
            text = self.clipboard.read()
        except Exception as exc:
            self.clipboard_error = f"CLIPBOARD ERROR: {exc}"
            return
        if not self.editing:
            # Import into CUSTOM when a read-only preview was displayed.
            self.focus_mml()
            self.selected_all = True
        self.insert_mml(text)
        self.clipboard_error = ""
        self.notice = "PASTED INTO CUSTOM MML"

    @staticmethod
    def inside(rect):
        x, y, w, h = rect
        return x <= pyxel.mouse_x/UI_SCALE < x+w and y <= pyxel.mouse_y/UI_SCALE < y+h

    def mouse_click(self):
        if self.inside(PITCH_TOGGLE):
            self.show_pitch = not self.show_pitch
            self.editing, self.selected_all = False, False
            self.focus = "pitch" if self.show_pitch else "tone"
        elif self.show_pitch and any(self.inside(rect) for rect in PITCH_CONTROLS.values()):
            for action, rect in PITCH_CONTROLS.items():
                if self.inside(rect):
                    endpoint, direction = action.split("_")
                    self.pitch_range.adjust(endpoint, -1 if direction == "down" else 1)
            self.editing, self.selected_all, self.focus = False, False, "pitch"
        elif self.show_pitch and self.inside((RIGHT_X, 64, DETAIL_W, 224)):
            self.editing, self.selected_all, self.focus = False, False, "pitch"
        elif self.inside(PRESET_PREV):
            self.browse_preset(-1)
        elif self.inside(PRESET_NEXT):
            self.browse_preset(1)
        elif self.inside(PRESET_LOAD):
            self.load_preset()
        elif not self.show_pitch and self.inside(CODE_COPY):
            self.copy_text("code")
        elif self.inside(MML_COPY):
            self.copy_text("mml")
        elif self.inside(MML_PASTE):
            self.paste_mml()
        elif self.inside((MARGIN, 348, WIDTH-2*MARGIN, 20)):
            if not self.editing:
                self.focus_mml()
                self.view_start = 0
            self.cursor = max(0, min(len(self.preview.custom),
                                   self.view_start + int((pyxel.mouse_x/UI_SCALE-MARGIN-8)//self.char_width)))
            self.selected_all = False
        else:
            self.editing = False
            self.selected_all = False
            self.focus = "code" if self.inside((RIGHT_X, 168, DETAIL_W, 120)) else "tone"
            if self.inside((MARGIN, 82, TONE_W, len(self.settings.rows())*15)):
                self.row = min(len(self.settings.rows())-1, int((pyxel.mouse_y/UI_SCALE-82)//15))

    def edit_mml(self):
        if pyxel.btn(pyxel.KEY_CTRL) and pyxel.btnp(pyxel.KEY_A):
            self.selected_all = True
        elif pyxel.btnp(pyxel.KEY_LEFT, 12, 2):
            self.cursor = max(0, self.cursor-1)
            self.selected_all = False
        elif pyxel.btnp(pyxel.KEY_RIGHT, 12, 2):
            self.cursor = min(len(self.preview.custom), self.cursor+1)
            self.selected_all = False
        elif pyxel.btnp(pyxel.KEY_HOME):
            self.cursor = 0
            self.selected_all = False
        elif pyxel.btnp(pyxel.KEY_END):
            self.cursor = len(self.preview.custom)
            self.selected_all = False

        text = self.preview.custom
        back = pyxel.btnp(pyxel.KEY_BACKSPACE, 12, 2)
        delete = pyxel.btnp(pyxel.KEY_DELETE, 12, 2)
        # input_text is Pyxel's native text-input path, including OS paste if delivered.
        inserted = "".join(c if 32 <= ord(c) < 127 else " "
                           for c in pyxel.input_text if c.isprintable() or c.isspace())
        if self.selected_all and (inserted or back or delete):
            text, self.cursor = "", 0
            self.selected_all = False
        elif back and self.cursor:
            text = text[:self.cursor-1] + text[self.cursor:]
            self.cursor -= 1
        elif delete:
            text = text[:self.cursor] + text[self.cursor+1:]
        if inserted:
            text = text[:self.cursor] + inserted + text[self.cursor:]
            self.cursor += len(inserted)
        self.preview.custom = text

    def update(self):
        try:
            self.clipboard.poll()
        except Exception as exc:
            self.clipboard_error = f"CLIPBOARD ERROR: {exc}"
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.mouse_click()
            return
        if pyxel.btn(pyxel.KEY_CTRL):
            if pyxel.btnp(pyxel.KEY_C) and self.focus in ("code", "mml"):
                self.copy_text(self.focus)
                return
            if pyxel.btnp(pyxel.KEY_V) and self.focus == "mml":
                self.paste_mml()
                return
        if pyxel.btnp(pyxel.KEY_F5):
            self.play()
        if pyxel.btnp(pyxel.KEY_F6):
            pyxel.stop(CHANNEL)
        if self.editing:
            if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_TAB):
                self.editing = False
                self.focus = "tone"
                self.selected_all = False
            else:
                self.edit_mml()
                if pyxel.btnp(pyxel.KEY_RETURN):
                    self.play()
            return
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_E) or pyxel.btnp(pyxel.KEY_TAB):
            self.focus_mml()
            return
        if pyxel.btnp(pyxel.KEY_P):
            self.cycle_preview()
        if pyxel.btnp(pyxel.KEY_LEFTBRACKET):
            self.browse_preset(-1)
        if pyxel.btnp(pyxel.KEY_RIGHTBRACKET):
            self.browse_preset(1)
        if pyxel.btnp(pyxel.KEY_RETURN):
            self.load_preset()
        if pyxel.btnp(pyxel.KEY_A):
            self.preview.auto_tone = not self.preview.auto_tone
        if pyxel.btnp(pyxel.KEY_L):
            self.preview.loop = not self.preview.loop
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.toggle_playback()
        if pyxel.btnp(pyxel.KEY_S):
            pyxel.stop(CHANNEL)
        rows = self.settings.rows()
        if pyxel.btnp(pyxel.KEY_UP, 12, 3):
            self.focus = "tone"
            self.row = (self.row-1) % len(rows)
        if pyxel.btnp(pyxel.KEY_DOWN, 12, 3):
            self.focus = "tone"
            self.row = (self.row+1) % len(rows)
        direction = int(pyxel.btnp(pyxel.KEY_RIGHT, 12, 3)) - int(pyxel.btnp(pyxel.KEY_LEFT, 12, 3))
        if direction:
            self.focus = "tone"
            self.settings.adjust(rows[self.row], direction)
            self.regenerate()

    def text(self, x, y, text, color):
        for row, line in enumerate(text.split("\n")):
            pyxel.text(x*UI_SCALE, (y+row*TEXT_LINE)*UI_SCALE, line, color, self.font)

    def panel(self, x, y, w, h, title):
        ui_border(x, y, w, h, 5)
        self.text(x+6, y+6, title, 12)

    def button(self, rect, label):
        x, y, w, h = rect
        ui_rect(x, y, w, h, 5 if self.inside(rect) else 1)
        ui_border(x, y, w, h, 6)
        self.text(x+(w-self.font.text_width(label)/UI_SCALE)//2, y, label, 7)

    def draw(self):
        pyxel.cls(1)
        self.text(MARGIN, 8, "TONE LAB / STATIC WAVETABLE EDITOR", 7)
        self.button(PITCH_TOGGLE, "WAVE / CODE" if self.show_pitch else "PITCH ERROR")
        self.panel(MARGIN, 24, WIDTH-2*MARGIN, 32, "PRESET / [ ] BROWSE, ENTER LOAD")
        definition = self.preset_definitions[self.preset_cursor]
        self.text(MARGIN+8, 44, f"{definition.category.title()} / {definition.name.title()}", 7)
        self.button(PRESET_PREV, "<")
        self.button(PRESET_NEXT, ">")
        self.button(PRESET_LOAD, "LOAD")
        self.text(404, 38, "Editing: " + (self.settings.preset_name or "Custom").title(), 10)
        self.panel(MARGIN, 64, TONE_W, 224, "TONE")
        for i, name in enumerate(self.settings.rows()):
            y = 84 + 15*i
            if i == self.row:
                ui_rect(MARGIN+3, y-2, TONE_W-6, 11, 5)
            self.text(MARGIN+8, y, name.upper(), 7)
            self.text(MARGIN+105, y, self.settings.value(name), 10)
        self.text(MARGIN+8, 274, f"SLOT {self.tone_index} / ONE EDITABLE TONE", 6)

        if self.show_pitch:
            self.draw_pitch()
        else:
            self.draw_wave_code()
        self.draw_preview()

    def draw_wave_code(self):
        self.panel(RIGHT_X, 64, DETAIL_W, 96, "WAVEFORM / ONE CYCLE")
        tone = pyxel.tones[self.tone_index]
        values = list(tone.wavetable)
        maximum = (1 << tone.sample_bits)-1
        x0, y0, w, h = RIGHT_X+8, 84, DETAIL_W-16, 64
        ui_line(x0, y0+h/2, x0+w-1, y0+h/2, 5)
        previous = None
        for i, value in enumerate(values):
            point = (x0 + i*(w-1)/max(1, len(values)-1), y0+(1-value/maximum)*(h-1))
            if previous is not None:
                ui_line(*previous, *point, 11)
            previous = point

        self.panel(RIGHT_X, 168, DETAIL_W, 120, "CODE / import pyxel_wavetable as wt")
        if self.focus == "code":
            ui_border(RIGHT_X, 168, DETAIL_W, 120, 10)
        self.button(CODE_COPY, "COPY CODE")
        self.text(RIGHT_X+8, 186, self.settings.code(), 7)

    def draw_pitch(self):
        self.panel(RIGHT_X, 64, DETAIL_W, 224, "PITCH ERROR / PYXEL 2.9.9 PREDICTION")
        for action, rect in PITCH_CONTROLS.items():
            self.button(rect, "-" if action.endswith("down") else "+")
        self.text(RIGHT_X+32, 85, note_name(self.pitch_range.start), 7)
        self.text(RIGHT_X+115, 85, "TO", 6)
        self.text(RIGHT_X+180, 85, note_name(self.pitch_range.end), 7)
        self.text(RIGHT_X+8, 102, "SIZE     MAX ABS     AVG ABS   (* EDITING)", 6)
        for i, row in enumerate(self.pitch_range.series(self.settings.size)):
            label = f"{'*' if row['current'] else ' '} {row['size']:3}    {row['max']:6.1f} c    {row['avg']:6.1f} c"
            self.text(RIGHT_X+8, 114+i*12, label, row["color"])
        self.text(RIGHT_X+8, 178, "GRAPH: 32 / 64 / 128 + EDITING SIZE", 6)
        series, limit = self.pitch_range.plot(self.settings.size)
        x, y, w, h = PITCH_GRAPH
        ui_border(x, y, w, h, 5)
        ui_line(x, y+h/2, x+w-1, y+h/2, 6)
        for label, yy in [(f"+{limit:.0f}", y), ("0 c", y+h/2-4), (f"-{limit:.0f}", y+h-8)]:
            self.text(RIGHT_X+4, yy, label, 6)
        for note in range(self.pitch_range.start, self.pitch_range.end+1):
            if note % 12 == 0:
                xx = x+(note-self.pitch_range.start)*(w-1)/max(1, self.pitch_range.end-self.pitch_range.start)
                ui_line(xx, y, xx, y+h-1, 5)
                # At wide ranges show alternating C labels to avoid collisions.
                if self.pitch_range.end-self.pitch_range.start <= 72 or note % 24 == 0:
                    self.text(xx-4, y+h+2, note_name(note), 6)
        for row in series:
            previous = None
            for px, py in row["points"]:
                point = (x+px*(w-1), y+py*(h-1))
                if previous is not None:
                    ui_line(*previous, *point, row["color"])
                ui_rect(*point, 1.5 if row["current"] else 1, 1.5 if row["current"] else 1, row["color"])
                previous = point
        self.text(RIGHT_X+8, 276, "MODEL ONLY / NO AUDIO / NO CORRECTION", 6)

    def draw_preview(self):
        self.panel(MARGIN, 296, WIDTH-2*MARGIN, 28, "PREVIEW")
        self.text(80, 306, self.preview.name.upper(), 10)
        self.text(176, 306, f"Use Current Tone: {'ON' if self.preview.auto_tone else 'OFF'}", 7)
        self.text(296, 306, f"LOOP: {'ON' if self.preview.loop else 'OFF'}", 7)
        self.text(360, 306, "F5: PLAY / F6: STOP", 7)

        self.panel(MARGIN, 332, WIDTH-2*MARGIN, 36,
                   "CUSTOM MML / FOCUSED" if self.editing else "MML / CLICK TEXT TO EDIT CUSTOM")
        if self.focus == "mml":
            ui_border(MARGIN, 332, WIDTH-2*MARGIN, 36, 10)
        self.button(MML_COPY, "COPY MML")
        self.button(MML_PASTE, "PASTE MML")
        text = self.preview.custom if self.preview.name == "custom" else DEFAULT_MMLS[self.preview.name]
        columns = int((WIDTH-2*MARGIN-16)/self.char_width)
        if self.editing:
            self.view_start = min(self.view_start, self.cursor)
            self.view_start = max(self.view_start, self.cursor-columns+1)
        else:
            self.view_start = 0
        visible = text[self.view_start:self.view_start+columns]
        if self.editing and self.selected_all:
            ui_rect(MARGIN+8, 350, len(visible)*self.char_width, TEXT_LINE, 5)
        self.text(MARGIN+8, 350, visible, 7)
        if self.editing:
            cx = MARGIN+8+(self.cursor-self.view_start)*self.char_width
            ui_line(cx, 350, cx, 350+TEXT_LINE-1, 10)

        status = "PLAYING" if pyxel.play_pos(CHANNEL) is not None else "STOPPED"
        message = self.clipboard_error or self.preview.error or f"{status} / FOCUS: {self.focus.upper()} / {self.notice}"
        # Two wrapped rows keep long parser messages inside the status region.
        columns = int((WIDTH-2*MARGIN)/self.char_width)
        lines = [message[i:i+columns] for i in range(0, len(message), columns)]
        self.text(MARGIN, 376, "\n".join(lines[:2]), 8 if self.preview.error or self.clipboard_error else 11)
        if self.editing:
            help_text = "MML: CTRL+A ALL / CTRL+C COPY / CTRL+V PASTE / BS/DEL ERASE\nENTER/F5: PLAY  F6: STOP  TAB/ESC: LEAVE EDITOR"
        else:
            help_text = "UP/DOWN: FIELD  LEFT/RIGHT: VALUE  P: PREVIEW  A: Use Current Tone  L: LOOP\nSPACE: PLAY/STOP  F5: RESTART  S/F6: STOP  E/TAB: EDIT  ESC: QUIT"
        self.text(MARGIN, 402, help_text, 6)


if __name__ == "__main__":
    App()
