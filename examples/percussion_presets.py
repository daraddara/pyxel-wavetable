"""Static percussion spectra with decay supplied by native Pyxel MML."""

import pyxel
import pyxel_wavetable as wt


class App:
    def __init__(self):
        pyxel.init(256, 132, title="Wavetable: Percussion Presets")
        self.names = ["TOM", "WOODBLOCK", "COWBELL", "METALLIC", "CLICK"]
        tom, woodblock, cowbell, metal, click = wt.add_tones([
            wt.tom(), wt.woodblock(), wt.cowbell(), wt.metallic(), wt.click(),
        ])
        # At T120 one tick is 1/96 second. Only volume changes over time.
        self.patterns = [
            f"T120 V100 Q100 L4 @{tom} @ENV1{{127,12,0}} O2 C",
            f"T120 V100 Q100 L4 @{woodblock} @ENV1{{127,5,0}} O4 C",
            f"T120 V100 Q100 L4 @{cowbell} @ENV1{{127,10,0}} O4 C",
            f"T120 V100 Q100 L4 @{metal} @ENV1{{127,18,0}} O5 C",
            f"T120 V100 Q100 L4 @{click} @ENV1{{127,3,0}} O6 C",
        ]
        self.selected = None
        pyxel.run(self.update, self.draw)

    def update(self):
        for i, key in enumerate([pyxel.KEY_1, pyxel.KEY_2, pyxel.KEY_3,
                                 pyxel.KEY_4, pyxel.KEY_5]):
            if pyxel.btnp(key):
                self.selected = i
                pyxel.play(0, self.patterns[i])
        if pyxel.btnp(pyxel.KEY_SPACE):
            pyxel.stop(0)

    def draw(self):
        pyxel.cls(1)
        pyxel.text(8, 8, "STATIC WAVETABLE / PERCUSSION", 7)
        for i, name in enumerate(self.names):
            pyxel.text(8, 28 + i * 12, f"{i+1} {name}",
                       10 if i == self.selected else 6)
        pyxel.text(8, 96, "DECAY: NATIVE PYXEL MML ENVELOPE", 6)
        pyxel.text(8, 116, "1-5: HIT   SPACE: STOP   ESC: QUIT", 13)


if __name__ == "__main__":
    App()
