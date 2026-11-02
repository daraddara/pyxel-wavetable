# pyxel-wavetable

数式・パラメータ・波形サンプルから、通常の `pyxel.Tone` を生成し、必要に応じて `pyxel.tones` に登録する小さなPythonユーティリティです。Pyxel本体やRustコードは変更しません。生成後の発音と再生は、既存の `Sound` / `Music` / MML / `play()` / `playm()` に任せます。

## インストール

Python 3.10以上、Pyxel 2.9.9以上（3未満）が必要です。

ソースコードを取得し、プロジェクトのルートで利用するPython環境にインストールします。環境管理ツールは任意です。以下はpipを使う例です。

```sh
python -m pip install .
```

このREADMEの `python` は、パッケージをインストールしたPython環境の実行コマンドを指します。環境に応じて `python3` などに読み替えてください。インストールとサンプル実行には同じPython環境を使います。

開発やテストを行う場合は、テスト用の依存もインストールします。

```sh
python -m pip install -e ".[test]"
python -m pytest -q
```

## 基本使用例

```python
import pyxel
import pyxel_wavetable as wt

pyxel.init(160, 80, title="Wavetable demo")

pm = wt.add_tone(wt.pm(ratio=3, index=1.8))
pyxel.sounds[0].set("c1 d1 e1 g1", str(pm), "7", "n", 12)
pyxel.play(0, 0, loop=True)

def draw():
    pyxel.cls(1)
    pyxel.text(8, 8, "ESC: QUIT", 7)

pyxel.run(lambda: None, draw)
```

ここで `update()` に音源処理を追加する必要はありません。generatorは新しいToneを返し、`add_tone()` / `add_tones()` は明示的に呼ばれた場合だけ末尾へ登録します。Pyxelの初期化・Sound設定・再生は利用アプリが行います。

## Toneの登録

`pyxel.init()` の後で登録します。既存のToneを上書き・置換せず、常に末尾へ追加します。戻り値は通常のTone indexで、独自の参照型や再生APIはありません。

### 単体登録

```python
pm = wt.add_tone(wt.pm(ratio=3, index=1.8))
```

シグネチャは `add_tone(tone: pyxel.Tone) -> int` です。`pm` は `pyxel.tones` 内のindexです。標準の4 Toneだけが存在すれば4を返し、`pyxel.tones[pm]` で参照できます。

### 複数登録

```python
sine, saw, pm = wt.add_tones([
    wt.sine(),
    wt.saw(),
    wt.pm(),
])
```

シグネチャは `add_tones(tones: Iterable[pyxel.Tone]) -> tuple[int, ...]` です。入力順のindexをtupleで返します。標準の4 Toneから開始すれば `(4, 5, 6)` です。list以外にgeneratorも使えます。

```python
indices = wt.add_tones(wt.sine() for _ in range(3))
assert wt.add_tones([]) == ()  # 登録状態は変わらない
```

### Soundで利用

```python
sound = pyxel.sounds[0]
sound.set("c2 d2 e2 g2", str(pm), "7", "n", 12)
# 既存Soundの音色だけを変更する場合
sound.set_tones(str(pm))
```

Pyxel 2.9.9の `Sound.set()` / `set_tones()` の文字列は、1文字につき1つのToneを指定します。上記の `str(index)` はindexが0〜9の場合に使えます。10以上では、例えば `"12"` はTone 1・2の列になるため、複数桁のindexをそのまま指定できるMMLを使ってください。登録API自体はindexを9までに制限しません。

### MMLで利用

```python
mml = f"@{pm} O3 C D E G"
pyxel.play(0, mml, loop=True)
```

通常のPyxel MMLの `@<tone index>` をそのまま使います。Sound / Music / MMLのラッパーや `Sound.set()` 専用ヘルパーは提供しません。

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

上記のgenerator・プリセットはすべて通常の `pyxel.Tone` を返します。登録APIの戻り値は前述の `int` / `tuple[int, ...]` です。

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

## パーカッション系プリセット

静的wavetableで音色の方向性を作る5つのプリセットです。実物の楽器を忠実に再現するものではなく、プリセット自身に減衰やピッチ変化はありません。

| API | 音色の方向性 | 実装 | デフォルトgain |
| --- | --- | --- | --- |
| `tom()` | 丸い電子タム系 | 低次倍音中心の `harmonics()` | 0.55 |
| `woodblock()` | 乾いた中空感のある木質系 | 奇数倍音を強めた `harmonics()` | 0.45 |
| `cowbell()` | 明るい電子的な金属打楽器系 | `pm(ratio=3, index=1.7)` | 0.40 |
| `metallic()` | 金属打楽器向けの複雑な倍音 | `harmonics()` | 0.35 |
| `click()` | 高域成分の多いclick/rim系素材 | `harmonics()` | 0.35 |

いずれも通常の `pyxel.Tone` を返し、キーワード引数 `size=128`、`sample_bits=8`、`gain` を変更できます。

```python
# pyxel.init() の後で登録する
tom, cowbell = wt.add_tones([wt.tom(), wt.cowbell()])
pyxel.play(0, f"T120 V100 Q100 L4 @{cowbell} @ENV1{{127,10,0}} O4 C")
```

減衰は既存の [Pyxel MML Envelope](https://raw.githubusercontent.com/kitao/pyxel/main/docs/mml-commands.md) に任せます。`@ENV1{127,10,0}` は初期音量127から10 tickで0へ下げます。1 tickは四分音符の1/48で、T120なら約10.4msです。波形やPM indexを発音中に変更せず、独自Envelope APIも追加しません。

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

プロジェクトのルートから、インストール先と同じPython環境で実行します。

```sh
python examples/basic_tones.py
python examples/melody_compare.py
python examples/custom_wave.py
python examples/percussion_presets.py
```

- `basic_tones.py`: `add_tones()` で登録し、返されたindexを `Sound.set()` に直接渡す。1〜5でSINE / SAW / PULSE（duty=0.125）/ HARMONICS / PMを選択。同じメロディを再生。SPACEで停止。
- `melody_compare.py`: BELL → BASS → LEAD → ORGAN → SOFTで同じメロディを順次再生。通常の `Music` がループ全体を管理。SPACEで再開、Sで停止。
- `custom_wave.py`: `sin(p) + 0.4*sin(2p) + 0.2*sin(5p)` を一度だけ生成。SPACEで再開、Sで停止。
- `percussion_presets.py`: 1〜5でTOM / WOODBLOCK / COWBELL / METALLIC / CLICKを単音再生。`add_tones()` で登録し、各音色の減衰には通常のMML Envelopeを使用。SPACEで停止。

いずれもESCで終了します。メロディ比較では音色の切替時にフレーズの先頭から再生します。

## Tone Lab：パラメータを調整して試聴する

ほかのサンプルと同じPython環境で実行します。

```sh
python examples/tone_lab.py
```

上側のPRESETで音作りの出発点を読み込み、左側のTONEで設定を調整します。右側のWAVEFORMで1周期の形状、CODEでそのまま利用できる生成コードを確認できます。下側にはPREVIEW、MML入力欄、再生状態・エラーと操作説明を表示します。

文字は同梱のRoboto Mono Mediumを16px、行間20pxで描画します。画面の描画領域は1136×848です。OSにフォントをインストールする必要はありません。配布元とフォント固有のライセンスは [examples/assets/fonts/README.md](examples/assets/fonts/README.md) に記載しています。

`presets.py` の全10種を、共通の定義から一覧表示します。TonalはBell / Bass / Lead / Organ / Soft、PercussionはTom / Woodblock / Cowbell / Metallic / Clickです。PRESET欄の `<` / `>` ボタンまたは `[` / `]` キーで選び、LOADボタンまたはEnterで読み込みます。MML編集中のEnterは引き続き試聴用です。

読み込み時にはgenerator・共通パラメータ・PM設定または倍音値を編集状態へ展開し、短い倍音配列は8要素まで0で埋めます。Presetは固定の再生モードではなく、自由に変更できる初期値です。`Editing: Bell` などの表示は、音色生成に関係する値を変更すると `Editing: Custom` になります。範囲端で値が変わらなかった操作や、MML編集・Preview切替・Loop・Use Current Toneの切替では変わりません。

同じPresetをLOADし直せば元の定義値に戻ります。MMLやPreview、Loopの設定は保持し、Toneスロットも追加しません。生成コードは `wt.bell()` ではなく、展開後の `wt.pm(...)` / `wt.harmonics(...)` を表示・コピーします。値を調整し、CUSTOM MMLで自分のフレーズを試してから、そのコードを自分のプログラムへ持ち帰れます。

| 操作（MML編集中を除く） | キー |
| --- | --- |
| パラメータの選択・増減 | ↑↓で項目選択、←→で変更 |
| Presetの選択・読込 | `<` / `>` ボタンまたは `[` / `]` キーで選択、LOAD / Enterで読込 |
| Preview切替 | P：melody → bass → short → perc_low → perc_high → custom。再生中は新しいPreviewを先頭から即再生、停止中は選択のみ |
| 現在ToneをMML先頭に自動付加 | A：Use Current Tone ON/OFF |
| ループ切替 | L |
| 再生・停止 | SPACEで再生/停止をトグル。F5で先頭から再生、S / F6で停止 |
| CUSTOM MML編集に入る | E / TAB |
| 終了 | ESC（編集中は編集を終了するだけ） |

対応generatorはPM / Harmonics / Pulse / Sine / Saw / Triangle / Squareです。初期値はPM、size=128、sample_bits=8、gain=0.5、ratio=3、index=1.8です。

| パラメータ | UIでの範囲・刻み |
| --- | --- |
| size | 32 / 64 / 128 / 256 / 512 |
| sample_bits | 1〜16、1刻み |
| gain | 0〜1、0.05刻み |
| PM ratio / index | ratio：整数1〜16、index：0〜10を0.1刻み |
| Pulse duty | 1/32〜31/32、1/32刻み |
| Harmonics H1〜H8 | 各0〜1、0.05刻み |

これらはTone Labの操作範囲で、ライブラリの入力範囲を変更するものではありません。初期倍音は `[1, 0.5, 0.25, 0.1, 0, 0, 0, 0]` です。

既定のPreviewは以下の5種類です。

```text
melody: T120 O3 L8 C D E G A G E D
bass:   T110 O2 L8 C C G G A G E C
short:  T120 O4 L16 C R C R C R C R
perc_low:  T120 V100 Q100 L16 @ENV1{127,10,0} O2 C R C R C8 R8 G R C R C8 R8
perc_high: T120 V100 Q100 L16 @ENV1{127,6,0} O5 C R C R C8 R8 G R C R C8 R8
```

`perc_low` はタムなどの低音系、`perc_high` はウッドブロック・カウベル・クリックなどの高音系を試すためのパターンです。同じリズムをO2 / O5で再生し、既存MML Envelopeでそれぞれ約104ms / 63msで音量を0へ下げます。ToneそのものやPresetの設定は変えず、発音と減衰をPyxelに任せます。再生中にPで切り替えると、選んだパターンを即座に先頭から再生します。

CUSTOM入力は `pyxel.input_text` を使う1行エディターです。ASCIIのMMLを入力でき、長い文字列はカーソルに合わせて横スクロールします。←→ / HOME / ENDで移動、Backspace / Deleteで削除、Ctrl+Aで全選択、Enter / F5で再生、F6で停止、TAB / ESCで編集を終了します。編集中の文字キーやSPACEは入力用で、Preview切替などのショートカットにはなりません。改行・タブが入力イベントに含まれる場合は空白へ変換します。

MML欄に **COPY MML / PASTE MML**、読み取り専用のCODE欄に **COPY CODE** ボタンがあります。MML本文をクリックすると、その位置へカーソルを移動してCUSTOM編集に入ります。操作対象の欄は黄色い枠、STATUSには `FOCUS: MML` / `CODE` / `TONE` を表示します。

COPY MMLは現在表示中のMML全文、COPY CODEは生成コード全文をOSクリップボードへコピーします。PASTE MMLは編集中ならカーソル位置へ挿入し、Ctrl+Aで全選択していれば置換します。未編集のPreviewから押した場合は、CUSTOMへ切り替えて貼り付けた内容を設定します。改行は空白へ変換します。Ctrl+C / Ctrl+Vも対象欄のフォーカスに従います。CODEは生成結果なのでPaste操作はありません。

Tone Labのクリップボード操作には、Pythonの `tkinter` とデスクトップ環境が必要です。Pythonの配布方法によってはTkが別途必要になります。Tkがない環境やクリップボードを利用できない環境では、操作時に `CLIPBOARD ERROR` を表示し、MMLを保持します。ライブラリ本体は `tkinter` に依存しません。コピー内容はTone Labを開いたまま別アプリへ貼り付けてください。通常の文字入力にはPyxelの `input_text` を使います。

Use Current Toneは初期状態ONで、再生時に `@<編集中Toneのindex>` を先頭へ付けます。CUSTOM内に別の `@n` を書いた場合は、その位置から通常のPyxelの音色切替が有効です。OFFではMMLを変更せず渡します。空CUSTOMやMML構文エラーは画面に表示し、入力を保持します。修正して正常に再生するとエラー表示が消えます。

編集用Toneは起動時に1つだけ登録します。波形は設定変更時とPLAY時に同じスロットへ反映し、操作のたびにindexを増やしません。パラメータ変更で再生を再開せず、発音中の聞こえ方の変化はPyxel側の動作に任せます。タイミング管理・動的Envelope・独自MMLパーサは持ちません。波形表示はsample_bitsの整数レンジを振幅に変換した表示で、gain適用前の形状です。

設計境界は [docs/design.md](docs/design.md) を参照してください。PyxelのAPIは [公式APIリファレンス](https://kitao.github.io/pyxel/web/api-reference/) を参照しています。
