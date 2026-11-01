# pyxel-wavetable

数式・パラメータ・波形サンプルから、通常の `pyxel.Tone` を生成する小さなPythonユーティリティです。Pyxel本体やRustコードは変更しません。生成後の発音と再生は、既存の `Sound` / `Music` / MML / `play()` / `playm()` に任せます。

## インストール

Python 3.10以上、Pyxel 2.9.9以上（3未満）を対象とします。動作確認環境はWindows、Python 3.13.5、Pyxel 2.9.9です。

プロジェクトのルートで実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m pytest -q
```

## 基本使用例

```python
import pyxel
import pyxel_wavetable as wt

pyxel.init(160, 80, title="Wavetable demo")

# 初期Toneスロットは0〜3なので、4番を使う前に追加する。
pyxel.tones.append(wt.pm(ratio=3, index=1.8))
pyxel.sounds[0].set("c1 d1 e1 g1", "4", "7", "n", 12)
pyxel.play(0, 0, loop=True)

def draw():
    pyxel.cls(1)
    pyxel.text(8, 8, "ESC: QUIT", 7)

pyxel.run(lambda: None, draw)
```

ここで `update()` に音源処理を追加する必要はありません。ライブラリ自身はPyxelの初期化・スロット登録・再生を行わず、新しいToneを返すだけです。既存アプリでは、用途に合わせてToneを追加するか、既存スロットに代入してください。

## 公開API

```python
wt.sine()
wt.triangle()
wt.saw()
wt.square()
wt.pulse(duty=0.25)
wt.harmonics([1.0, 0.5, 0.25, 0.1])
wt.pm(ratio=3, index=1.8)

import math
wt.from_function(lambda p: math.sin(p) + 0.3 * math.sin(2*p))
wt.from_samples([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5])

# API確認用の静的音色。減衰などのenvelopeは持たない。
wt.bell()
wt.bass()
wt.lead()
wt.organ()
wt.soft()
```

すべて通常の `pyxel.Tone` を返します。

| API | 引数・波形 |
| --- | --- |
| `sine` | `sin(phase)`。0から上昇 |
| `triangle` | -1から上昇し、位相πで+1、周期末に-1へ戻る |
| `saw` | -1から+1へ向かう上昇ランプ。周期末でリセット |
| `square` | `pulse(duty=0.5)` |
| `pulse(duty=0.25)` | 周期の最初のduty割合が+1、残りが-1 |
| `harmonics(amplitudes)` | 要素順に第1、第2、第3…倍音の振幅。負の振幅も使用可 |
| `pm(ratio=3, index=1.8)` | `sin(phase + index * sin(phase * ratio))` |
| `from_function(func)` | `phase = 2π*i/size` を渡す。終端2πは重複させない |
| `from_samples(samples)` | 浮動小数波形。入力の点数をそのまま使い、再サンプリングしない |

共通のキーワード引数は `size=128, sample_bits=8, gain=0.5` です。ただし `from_samples()` は `size` を取りません。
基本波形、`harmonics()`、`from_function()`、`from_samples()` は `normalize=True` も受け取ります。`pm()` とプリセットは常に正規化します。`size` と `sample_bits` はキーワード専用です。プリセットは `size` / `sample_bits` / `gain` を変更できます。

## 正規化・量子化

入力はPyxel内部の整数値ではなく、原則-1.0〜+1.0の波形値です。

1. `normalize=True` なら絶対値の最大値で除算します。小さい入力も最大振幅まで拡大します。全点0の場合は除算しません。
2. -1〜+1にクリップします。`normalize=False` では入力を直接クリップします。
3. `round((value + 1) * 0.5 * ((1 << sample_bits) - 1))` で整数化します。Pythonの偶数丸めを使います。
4. `Tone.mode=0`、`Tone.sample_bits`、`Tone.wavetable`、`Tone.gain` を設定します。

4bitなら0〜15、8bitなら0〜255、16bitなら0〜65535です。0の入力は8bitでは128となります。整数レンジの中心が半整数のため、無音や対称波形にも半LSB以内の量子化誤差が生じます。DC除去は行いません。

`gain` はサンプルに掛けず、`Tone.gain` に設定します。0は許可し、上限1には制限しません。大きなgainや複数チャンネルの合成では再生側で音割れし得ます。

`size` は正の整数、`sample_bits` は1〜16の整数、`duty` は0より大きく1未満、`index` と `gain` は有限の非負値です。gainはPyxelのfloat32に収まる値に限ります。整数引数ではboolを拒否します。空のsamples・harmonics、NaN・無限大の入力も拒否します。不正な型は主に `TypeError`、範囲外・非有限値・空入力は `ValueError` になります。

## デフォルトの理由

`DEFAULT_SIZE=128`、`DEFAULT_SAMPLE_BITS=8`、`DEFAULT_GAIN=0.5` は、このユーティリティの初期方針です。Pyxel本体の仕様や推奨値ではありません。

PoCでは、32/64点の複雑なPM波形に高周波的な粗さがあり、128点ではDirect PCMとの聴感差がかなり小さく、256点以上では現行Pyxelのクロック量子化によるピッチ誤差が目立ちました。また、4/8/16bitの聴感差は小さかったため、8bitを採用しました。

## PMの範囲と制約

`pm()` は位相変調（phase modulation、PM）の式から、固定した1周期を生成します。初期版のratioは `int` かつ1以上です。`3.0` や非整数比は受け取りません。非整数比ではキャリア1周期内で波形が閉じず、繰り返し境界に不連続が生じる可能性があるためです。

動的PM envelope、Note On/Off管理、毎フレームのwavetable更新、独自シーケンサ、BGM制御は対象外です。アンチエイリアス・帯域制限・ピッチ補正も行いません。高次倍音や大きなindexの音質は、サイズと再生音程に依存します。

## 実行例

```powershell
.\.venv\Scripts\python.exe examples/basic_tones.py
.\.venv\Scripts\python.exe examples/melody_compare.py
.\.venv\Scripts\python.exe examples/custom_wave.py
```

- `basic_tones.py`: 1〜5でSINE / SAW / PULSE / HARMONICS / PMを選択。同じメロディを再生。SPACEで停止。
- `melody_compare.py`: BELL → BASS → LEAD → ORGAN → SOFTで同じメロディを順次再生。通常の `Music` がループ全体を管理。SPACEで再開、Sで停止。
- `custom_wave.py`: `sin(p) + 0.4*sin(2p) + 0.2*sin(5p)` を一度だけ生成。SPACEで再開、Sで停止。

いずれもESCで終了します。音色の切替時はフレーズの先頭から再生します。

設計境界は [docs/design.md](docs/design.md) を参照してください。PyxelのAPIは [公式APIリファレンス](https://kitao.github.io/pyxel/web/api-reference/) を参照しています。
