import re
import pyxel
import pyxel_wavetable as wt

pyxel.init(256, 80, title="Wavetable: Music Compare")
bell, bass, lead, organ, soft = wt.add_tones([wt.bell(), wt.bass(), wt.lead(), wt.organ(), wt.soft()])
saw = wt.add_tone(wt.saw())

tone0 = 0
tone1 = 1
tone2 = 2
tone3 = 3

ch = pyxel.gen_bgm(1, 0, 2, 20261102, False)

for i, mml in enumerate(ch):
    # @ENV や @VIB のパラメータ波括弧 {} を f文字列用にエスケープし、@[0-9] を @{tone0}〜@{tone9} に置換
    mml_escaped = mml.replace("{", "{{").replace("}", "}}")
    mml_fstr = re.sub(r"@([0-9])", r"@{tone\1}", mml_escaped)
    print(f"{i}: f'{mml_fstr}'")
    tone0 = 0
    tone1 = 1
    tone2 = 2
    tone3 = 3
    pyxel.sounds[i].mml(eval(f"f'{mml_fstr}'"))

    tone0 = saw
    tone1 = lead
    tone2 = bass
    tone3 = bell
    pyxel.sounds[i+10].mml(eval(f"f'{mml_fstr}'"))


pyxel.musics[0].set([0], [1], [2], [3])
pyxel.musics[1].set([10], [11], [12], [13])

pyxel.playm(1, loop=True)

pyxel.show()
