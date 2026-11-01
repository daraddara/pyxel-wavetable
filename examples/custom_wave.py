"""Generate a custom waveform once, then use ordinary Sound/play."""

import math

import pyxel
import pyxel_wavetable as wt


class App:
    def __init__(self):
        pyxel.init(256, 80, title="Wavetable: Custom Function")
        tone = wt.from_function(
            lambda p: math.sin(p) + 0.4 * math.sin(2*p) + 0.2 * math.sin(5*p)
        )
        pyxel.tones.append(tone)
        pyxel.sounds[0].set("c2 d2 e2 g2 a2 g2 e2 d2", "0", "7", "n", 12)
        pyxel.sounds[0].tones[:] = [len(pyxel.tones) - 1]
        pyxel.play(0, 0, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            pyxel.play(0, 0, loop=True)
        if pyxel.btnp(pyxel.KEY_S):
            pyxel.stop(0)

    def draw(self):
        pyxel.cls(1)
        pyxel.text(8, 8, "FROM_FUNCTION / STATIC WAVE", 7)
        pyxel.text(8, 26, "sin(p) + .4*sin(2p) + .2*sin(5p)", 10)
        pyxel.text(8, 42, "128 SAMPLES / 8 BITS / GAIN 0.5", 6)
        pyxel.text(8, 64, "SPACE: RESTART   S: STOP   ESC: QUIT", 13)


if __name__ == "__main__":
    App()
