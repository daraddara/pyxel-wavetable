"""Compare the same gen_bgm score using native Pyxel playback and Tone banks."""

from dataclasses import dataclass, replace
from pathlib import Path
import runpy

import pyxel
import pyxel_wavetable as wt

# Keep this experiment separate from the installed library and Tone Lab API.
_pitch = runpy.run_path(str(Path(__file__).with_name("_bgm_pitch.py")))
score_notes, choose_sizes = _pitch["score_notes"], _pitch["choose_sizes"]
error_bound, pitch_error = _pitch["error_bound"], _pitch["pitch_error"]

WIDTH, HEIGHT = 960, 864
FONT_PATH = Path(__file__).resolve().parent / "assets/fonts/RobotoMono-Medium.ttf"
GENRES = ("Title", "Departure", "Town", "Peaceful", "Field", "Adventure", "Battle", "Crisis")
INSTRUMENTS = ("Melody / Reverb / Bass", "Melody / Bass / Drums",
               "Melody / Sub / Bass", "Melody / Sub / Bass / Drums")
FIELDS = ("preset", "instr", "transp", "seed")
NATIVE_NAMES = ("TRIANGLE", "SQUARE", "PULSE", "NOISE")
WAVE_NAMES = ("SOFT", "LEAD", "PM (3:1, index 1.8)", "METALLIC")
BUTTONS = {
    "default": (24, 58, 260, 40), "wavetable": (300, 58, 280, 40),
    "toggle": (596, 58, 160, 40), "restart": (772, 58, 164, 40),
    "generate": (24, 294, 260, 36), "next_seed": (300, 294, 260, 36),
    "loop": (576, 294, 160, 36), "noise": (24, 536, 440, 36),
    "target": (480, 536, 456, 36),
}


@dataclass(frozen=True)
class SongSettings:
    preset: int = 4
    transp: int = 0
    instr: int = 3
    seed: int = 42

    def adjust(self, name, direction):
        bounds = {"preset": (0, 7), "instr": (0, 3), "transp": (-5, 5), "seed": (0, 999999)}
        minimum, maximum = bounds[name]
        return replace(self, **{name: max(minimum, min(maximum, getattr(self, name)+direction))})


class Comparison:
    """One unchanged score, played by Music; this example owns slots 0-3."""

    def __init__(self):
        # Keep the original objects intact, including native noise metadata.
        self.native = tuple(list(pyxel.tones)[:4])
        self.target = 10
        self.wavetable = False
        self.replace_noise = False
        self.loop = True
        self.settings = SongSettings()
        self.mmls = ()
        self.durations = ()
        self.generate(self.settings)

    def make_bank(self, notes, vibrato, target, replace_noise=None):
        replace_noise = self.replace_noise if replace_noise is None else replace_noise
        evaluated = notes if replace_noise else (*notes[:3], ())
        sizes = choose_sizes(evaluated, vibrato, target)
        bank = tuple(factory(size=size, gain=original.gain)
                     for factory, size, original in zip((wt.soft, wt.lead, wt.pm, wt.metallic), sizes, self.native))
        return sizes, bank

    def cycle_target(self):
        target = {10: 25, 25: None, None: 10}[self.target]
        sizes, bank = self.make_bank(self.notes, self.vibrato, target)
        was_playing = self.playing()
        pyxel.stop()
        self.target, self.sizes, self.wave = target, sizes, bank
        self.apply_bank()
        if was_playing:
            self.restart()

    def playing(self):
        return any(pyxel.play_pos(channel) is not None for channel in range(4))

    def apply_bank(self):
        for i, original in enumerate(self.native):
            use_wave = self.wavetable and (i != 3 or self.replace_noise)
            pyxel.tones[i] = self.wave[i] if use_wave else original

    def generate(self, settings):
        # Build/validate the new score first; leave the old one intact on failure.
        mmls = tuple(pyxel.gen_bgm(preset=settings.preset, transp=settings.transp,
                                   instr=settings.instr, seed=settings.seed, play=False))
        if len(mmls) != 4:
            raise ValueError("gen_bgm must return four channel MML strings")
        sounds = [pyxel.Sound() for _ in mmls]
        for sound, mml in zip(sounds, mmls):
            sound.mml(mml)
        notes, vibrato = score_notes(mmls)
        sizes, bank = self.make_bank(notes, vibrato, self.target)
        durations = tuple(sound.total_sec() for sound in sounds)
        music = pyxel.Music()
        music.set(*[[i] if duration != 0 else [] for i, duration in enumerate(durations)])
        was_playing = self.playing()
        pyxel.stop()
        for i, sound in enumerate(sounds):
            pyxel.sounds[i] = sound
        pyxel.musics[0] = music
        self.settings, self.mmls, self.durations = settings, mmls, durations
        self.notes, self.vibrato, self.sizes, self.wave = notes, vibrato, sizes, bank
        self.apply_bank()
        if was_playing:
            self.restart()

    def restart(self):
        pyxel.stop()
        self.apply_bank()
        pyxel.playm(0, loop=self.loop)

    def select_mode(self, wavetable):
        if wavetable == self.wavetable:
            return
        was_playing = self.playing()
        pyxel.stop()
        self.wavetable = wavetable
        self.apply_bank()
        if was_playing:
            self.restart()

    def toggle_noise(self):
        replace_noise = not self.replace_noise
        sizes, bank = self.make_bank(self.notes, self.vibrato, self.target, replace_noise)
        was_playing = self.playing()
        pyxel.stop()
        self.replace_noise, self.sizes, self.wave = replace_noise, sizes, bank
        self.apply_bank()
        if was_playing:
            self.restart()


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Pyxel gen_bgm: Default vs Wavetable", display_scale=1)
        pyxel.mouse(True)
        self.font = pyxel.Font(str(FONT_PATH), 16)
        self.comparison = Comparison()
        self.pending = self.comparison.settings
        self.row = 0
        self.error = ""
        self.comparison.restart()
        pyxel.run(self.update, self.draw)

    def act(self, action):
        try:
            c = self.comparison
            if action == "default":
                c.select_mode(False)
            elif action == "wavetable":
                c.select_mode(True)
            elif action == "toggle":
                pyxel.stop() if c.playing() else c.restart()
            elif action == "restart":
                c.restart()
            elif action == "generate":
                c.generate(self.pending)
            elif action == "next_seed":
                self.pending = replace(self.pending, seed=(self.pending.seed+1) % 1000000)
                c.generate(self.pending)
            elif action == "loop":
                was_playing = c.playing()
                c.loop = not c.loop
                if was_playing:
                    c.restart()
            elif action == "noise":
                c.toggle_noise()
            elif action == "target":
                c.cycle_target()
            self.error = ""
        except Exception as exc:
            self.error = str(exc)

    @staticmethod
    def inside(rect):
        x, y, w, h = rect
        return x <= pyxel.mouse_x < x+w and y <= pyxel.mouse_y < y+h

    def update(self):
        actions = {pyxel.KEY_A: "default", pyxel.KEY_B: "wavetable", pyxel.KEY_SPACE: "toggle",
                   pyxel.KEY_R: "restart", pyxel.KEY_G: "generate", pyxel.KEY_N: "next_seed",
                   pyxel.KEY_L: "loop", pyxel.KEY_D: "noise", pyxel.KEY_F: "target"}
        for key, action in actions.items():
            if pyxel.btnp(key):
                self.act(action)
        if pyxel.btnp(pyxel.KEY_UP, 12, 3):
            self.row = (self.row-1) % len(FIELDS)
        if pyxel.btnp(pyxel.KEY_DOWN, 12, 3):
            self.row = (self.row+1) % len(FIELDS)
        direction = int(pyxel.btnp(pyxel.KEY_RIGHT, 12, 3)) - int(pyxel.btnp(pyxel.KEY_LEFT, 12, 3))
        if direction:
            self.pending = self.pending.adjust(FIELDS[self.row], direction)
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            for action, rect in BUTTONS.items():
                if self.inside(rect):
                    self.act(action)
                    return
            for i, name in enumerate(FIELDS):
                for sign, x in [(-1, 824), (1, 884)]:
                    if self.inside((x, 142+i*34, 48, 26)):
                        self.row = i
                        self.pending = self.pending.adjust(name, sign)

    def text(self, x, y, text, color=7):
        pyxel.text(x, y, text, color, self.font)

    def button(self, rect, label, selected=False):
        x, y, w, h = rect
        pyxel.rect(x, y, w, h, 5 if selected or self.inside(rect) else 1)
        pyxel.rectb(x, y, w, h, 10 if selected else 6)
        self.text(x+(w-self.font.text_width(label))//2, y+(h-20)//2, label)

    def draw(self):
        pyxel.cls(1)
        c = self.comparison
        self.text(24, 16, "GEN_BGM / SAME SCORE, DIFFERENT TONES", 12)
        self.button(BUTTONS["default"], "A: DEFAULT", not c.wavetable)
        self.button(BUTTONS["wavetable"], "B: WAVETABLE", c.wavetable)
        self.button(BUTTONS["toggle"], "SPACE: STOP" if c.playing() else "SPACE: PLAY")
        self.button(BUTTONS["restart"], "R: RESTART")
        self.text(24, 108, "A/B switches restart the SAME song from the beginning.", 6)
        pyxel.rectb(16, 136, WIDTH-32, 144, 5)
        for i, name in enumerate(FIELDS):
            y = 144+i*34
            if self.row == i:
                pyxel.rect(20, y, 790, 26, 5)
            value = getattr(self.pending, name)
            description = GENRES[value] if name == "preset" else INSTRUMENTS[value] if name == "instr" else ""
            self.text(28, y, f"{name.upper():<8} {value:<7} {description}")
            self.button((824, y-2, 48, 26), "-")
            self.button((884, y-2, 48, 26), "+")
        self.button(BUTTONS["generate"], "G: GENERATE")
        self.button(BUTTONS["next_seed"], "N: NEXT SEED")
        self.button(BUTTONS["loop"], "LOOP: ON" if c.loop else "LOOP: OFF")
        active = c.settings
        suffix = " / PENDING: press G" if self.pending != active else ""
        self.text(24, 344, f"PLAYING SCORE: preset={active.preset} instr={active.instr} transp={active.transp} seed={active.seed}"+suffix, 10)
        self.text(24, 378, "TONE BANK: native index -> wavetable replacement", 12)
        for i, native_name in enumerate(NATIVE_NAMES):
            wave_name = WAVE_NAMES[i] if i != 3 or c.replace_noise else "KEEP NATIVE NOISE"
            self.text(32, 408+i*28, f"{i}: {native_name:<10} -> {wave_name}", 7)
        self.button(BUTTONS["noise"], "D: NOISE -> METALLIC" if c.replace_noise else "D: KEEP NATIVE NOISE", c.replace_noise)
        self.button(BUTTONS["target"], f"F: TARGET {c.target} c" if c.target else "F: FIXED SIZE 128")
        self.text(24, 584, "Score notes, tempo, volume and MML envelopes stay unchanged.", 6)
        self.text(24, 608, "Tone gain values match originals; perceived loudness may differ.", 6)
        if self.error:
            self.text(24, 634, ("ERROR: "+self.error)[:90], 8)
        else:
            self.text(24, 634, "PLAYING" if c.playing() else "STOPPED", 11)
        self.text(24, 666, "UP/DOWN: field  LEFT/RIGHT: value  Buttons: click  ESC: quit", 6)
        self.text(24, 704, "PYXEL 2.9.9 MODEL / FIXED SIZE PER TONE / NO NOTE CORRECTION", 12)
        for i, (notes, size) in enumerate(zip(c.notes, c.sizes)):
            if i == 3 and not c.replace_noise:
                info = "NATIVE NOISE (not pitch-evaluated)"
            elif not notes:
                info = "UNUSED"
            else:
                maximum = max(abs(pitch_error(note, size)) for note in notes)
                bound = error_bound(notes, size, c.vibrato)
                info = f"size {size:3}  base max {maximum:5.1f} c  bound {bound:5.1f} c"
            self.text(32, 732+i*22, f"Tone {i}: {info}", 7)
        self.text(24, 824, "Targets vs 12-TET, not A/B difference or hearing thresholds. Short tables alter timbre.", 6)


if __name__ == "__main__":
    App()
