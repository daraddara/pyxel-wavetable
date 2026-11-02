"""Tone editor; all sequencing and MML belong to Pyxel."""

from dataclasses import dataclass, field

import pyxel
import pyxel_wavetable as wt

GENERATORS = ("pm", "harmonics", "pulse", "sine", "saw", "triangle", "square")
DEFAULT_MMLS = {
    "melody": "T120 O3 L8 C D E G A G E D",
    "bass": "T110 O2 L8 C C G G A G E C",
    "short": "T120 O4 L16 C R C R C R C R",
}
PREVIEWS = (*DEFAULT_MMLS, "custom")
SIZES = (32, 64, 128, 256, 512)
CHANNEL = 0
MARGIN, GAP = 8, 8
TONE_W, DETAIL_W = 176, 368
WIDTH = 2 * MARGIN + TONE_W + GAP + DETAIL_W
HEIGHT = 384
RIGHT_X = MARGIN + TONE_W + GAP
CODE_COPY = (WIDTH-MARGIN-76, 132, 68, 12)
MML_COPY = (WIDTH-MARGIN-148, 296, 68, 12)
MML_PASTE = (WIDTH-MARGIN-76, 296, 68, 12)


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
        pyxel.init(WIDTH, HEIGHT, title="Wavetable: Tone Lab", quit_key=pyxel.KEY_NONE)
        pyxel.mouse(True)
        self.settings = ToneSettings()
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
        return x <= pyxel.mouse_x < x+w and y <= pyxel.mouse_y < y+h

    def mouse_click(self):
        if self.inside(CODE_COPY):
            self.copy_text("code")
        elif self.inside(MML_COPY):
            self.copy_text("mml")
        elif self.inside(MML_PASTE):
            self.paste_mml()
        elif self.inside((MARGIN, 308, WIDTH-2*MARGIN, 20)):
            if not self.editing:
                self.focus_mml()
                self.view_start = 0
            self.cursor = max(0, min(len(self.preview.custom),
                                   self.view_start + (pyxel.mouse_x-MARGIN-8)//pyxel.FONT_WIDTH))
            self.selected_all = False
        else:
            self.editing = False
            self.selected_all = False
            self.focus = "code" if self.inside((RIGHT_X, 128, DETAIL_W, 120)) else "tone"
            if self.inside((MARGIN, 42, TONE_W, len(self.settings.rows())*15)):
                self.row = min(len(self.settings.rows())-1, (pyxel.mouse_y-42)//15)

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

    @staticmethod
    def panel(x, y, w, h, title):
        pyxel.rectb(x, y, w, h, 5)
        pyxel.text(x+6, y+6, title, 12)

    def button(self, rect, label):
        x, y, w, h = rect
        pyxel.rect(x, y, w, h, 5 if self.inside(rect) else 1)
        pyxel.rectb(x, y, w, h, 6)
        pyxel.text(x+(w-len(label)*pyxel.FONT_WIDTH)//2, y+3, label, 7)

    def draw(self):
        pyxel.cls(1)
        pyxel.text(MARGIN, 8, "TONE LAB / STATIC WAVETABLE EDITOR", 7)
        self.panel(MARGIN, 24, TONE_W, 224, "TONE")
        for i, name in enumerate(self.settings.rows()):
            y = 44 + 15*i
            if i == self.row:
                pyxel.rect(MARGIN+3, y-2, TONE_W-6, 11, 5)
            pyxel.text(MARGIN+8, y, name.upper(), 7)
            pyxel.text(MARGIN+105, y, self.settings.value(name), 10)
        pyxel.text(MARGIN+8, 234, f"SLOT {self.tone_index} / ONE EDITABLE TONE", 6)

        self.panel(RIGHT_X, 24, DETAIL_W, 96, "WAVEFORM / ONE CYCLE")
        tone = pyxel.tones[self.tone_index]
        values = list(tone.wavetable)
        maximum = (1 << tone.sample_bits)-1
        x0, y0, w, h = RIGHT_X+8, 44, DETAIL_W-16, 64
        pyxel.line(x0, y0+h/2, x0+w-1, y0+h/2, 5)
        previous = None
        for i, value in enumerate(values):
            point = (x0 + i*(w-1)/max(1, len(values)-1), y0+(1-value/maximum)*(h-1))
            if previous is not None:
                pyxel.line(*previous, *point, 11)
            previous = point

        self.panel(RIGHT_X, 128, DETAIL_W, 120, "CODE / import pyxel_wavetable as wt")
        if self.focus == "code":
            pyxel.rectb(RIGHT_X, 128, DETAIL_W, 120, 10)
        self.button(CODE_COPY, "COPY CODE")
        pyxel.text(RIGHT_X+8, 146, self.settings.code(), 7)
        self.panel(MARGIN, 256, WIDTH-2*MARGIN, 28, "PREVIEW")
        pyxel.text(80, 266, self.preview.name.upper(), 10)
        pyxel.text(176, 266, f"Use Current Tone: {'ON' if self.preview.auto_tone else 'OFF'}", 7)
        pyxel.text(280, 266, f"LOOP: {'ON' if self.preview.loop else 'OFF'}", 7)
        pyxel.text(360, 266, "F5: PLAY / F6: STOP", 7)

        self.panel(MARGIN, 292, WIDTH-2*MARGIN, 36,
                   "CUSTOM MML / FOCUSED" if self.editing else "MML / CLICK TEXT TO EDIT CUSTOM")
        if self.focus == "mml":
            pyxel.rectb(MARGIN, 292, WIDTH-2*MARGIN, 36, 10)
        self.button(MML_COPY, "COPY MML")
        self.button(MML_PASTE, "PASTE MML")
        text = self.preview.custom if self.preview.name == "custom" else DEFAULT_MMLS[self.preview.name]
        columns = (WIDTH-2*MARGIN-16)//pyxel.FONT_WIDTH
        if self.editing:
            self.view_start = min(self.view_start, self.cursor)
            self.view_start = max(self.view_start, self.cursor-columns+1)
        else:
            self.view_start = 0
        visible = text[self.view_start:self.view_start+columns]
        if self.editing and self.selected_all:
            pyxel.rect(MARGIN+8, 310, len(visible)*4, 8, 5)
        pyxel.text(MARGIN+8, 310, visible, 7)
        if self.editing:
            cx = MARGIN+8+(self.cursor-self.view_start)*pyxel.FONT_WIDTH
            pyxel.line(cx, 310, cx, 317, 10)

        status = "PLAYING" if pyxel.play_pos(CHANNEL) is not None else "STOPPED"
        message = self.clipboard_error or self.preview.error or f"{status} / FOCUS: {self.focus.upper()} / {self.notice}"
        # Two wrapped rows keep long parser messages inside the status region.
        columns = (WIDTH-2*MARGIN)//4
        lines = [message[i:i+columns] for i in range(0, len(message), columns)]
        pyxel.text(MARGIN, 336, "\n".join(lines[:2]), 8 if self.preview.error or self.clipboard_error else 11)
        if self.editing:
            help_text = "MML: CTRL+A ALL / CTRL+C COPY / CTRL+V PASTE / BS/DEL ERASE\nENTER/F5: PLAY  F6: STOP  TAB/ESC: LEAVE EDITOR"
        else:
            help_text = "UP/DOWN: FIELD  LEFT/RIGHT: VALUE  P: PREVIEW  A: Use Current Tone  L: LOOP\nSPACE: PLAY/STOP  F5: RESTART  S/F6: STOP  E/TAB: EDIT  ESC: QUIT"
        pyxel.text(MARGIN, 362, help_text, 6)


if __name__ == "__main__":
    App()
