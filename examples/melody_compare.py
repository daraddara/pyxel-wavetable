"""Pyxel Music sequences five versions of the same melody, without a scheduler."""

import pyxel
import pyxel_wavetable as wt


class App:
    def __init__(self):
        pyxel.init(256, 80, title="Wavetable: Music Compare")
        tone_indices = wt.add_tones([
            wt.bell(), wt.bass(), wt.lead(), wt.organ(), wt.soft(),
        ])
        for i, tone_index in enumerate(tone_indices):
            pyxel.sounds[i].set("c2 d2 e2 g2 a2 g2 e2 d2", str(tone_index), "7", "n", 12)
        # All sequencing and looping belongs to ordinary Pyxel Music.
        pyxel.musics[0].set([0, 1, 2, 3, 4], [], [], [])
        pyxel.playm(0, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            pyxel.playm(0, loop=True)
        if pyxel.btnp(pyxel.KEY_S):
            pyxel.stop()

    def draw(self):
        pyxel.cls(1)
        pyxel.text(8, 8, "PYXEL MUSIC / SAME MELODY", 7)
        pyxel.text(8, 26, "BELL > BASS > LEAD > ORGAN > SOFT", 10)
        pyxel.text(8, 42, "SEQUENCING: PYXEL MUSIC", 6)
        pyxel.text(8, 64, "SPACE: RESTART   S: STOP   ESC: QUIT", 13)


if __name__ == "__main__":
    App()
