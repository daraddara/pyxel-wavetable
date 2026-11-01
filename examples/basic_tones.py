"""Keys 1-5 select the same melody played through different static Tones."""

import pyxel
import pyxel_wavetable as wt

MELODY = "c2 d2 e2 g2 a2 g2 e2 d2"


class App:
    def __init__(self):
        pyxel.init(240, 112, title="Wavetable: Basic Tones")
        self.names = ["SINE", "SAW", "PULSE", "HARMONICS", "PM"]
        tones = [wt.sine(), wt.saw(), wt.pulse(0.25),
                 wt.harmonics([1, 0.5, 0.25, 0.1]), wt.pm()]
        # Extend first: Pyxel starts with only four Tone slots (0-3).
        pyxel.tones.extend(tones)
        self.first_tone = len(pyxel.tones) - len(tones)
        for i in range(5):
            sound = pyxel.sounds[i]
            sound.set(MELODY, "0", "7", "n", 12)
            sound.tones[:] = [self.first_tone + i]
        self.selected = 0
        pyxel.play(0, 0, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        for i, key in enumerate([pyxel.KEY_1, pyxel.KEY_2, pyxel.KEY_3,
                                 pyxel.KEY_4, pyxel.KEY_5]):
            if pyxel.btnp(key):
                self.selected = i
                pyxel.play(0, i, loop=True)
        if pyxel.btnp(pyxel.KEY_SPACE):
            pyxel.stop(0)

    def draw(self):
        pyxel.cls(1)
        pyxel.text(8, 8, "SAME MELODY / FIVE STATIC TONES", 7)
        for i, name in enumerate(self.names):
            pyxel.text(8, 26 + i * 12, f"{i+1} {name}",
                       10 if i == self.selected else 6)
        pyxel.text(8, 96, "1-5: PLAY   SPACE: STOP   ESC: QUIT", 13)


if __name__ == "__main__":
    App()
