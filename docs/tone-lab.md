# Tone Lab Manual

Tone Labは、`pyxel_wavetable` のgeneratorやPresetを対話的に調整し、その場でMMLを使って試聴するためのサンプルです。

```sh
python examples/tone_lab.py
```

Tone Labはライブラリ本体のAPIではなく、`examples/tone_lab.py` に実装された音作り用UIです。

## 画面構成

Tone Labは主に次の領域で構成されています。

![Tone Lab overview](images/tone-lab-overview.png)

1. **PRESET** — Presetの選択と読込
2. **TONE** — generatorとパラメータの編集
3. **WAVEFORM** — 現在の1周期wavetable表示
4. **CODE** — 現在設定に対応するPythonコード
5. **PREVIEW** — 試聴パターン、Use Current Tone、Loop
6. **MML** — CUSTOM MMLの入力・Copy/Paste
7. **STATUS** — 再生状態、フォーカス、エラー表示

右上の **PITCH ERROR** ボタンで、WAVEFORM / CODEの領域をピッチ診断へ切り替えます。**WAVE / CODE** で元へ戻せます。上の画像は波形・コード表示です。

## Presetから音作りを始める

PRESET欄では `presets.py` に定義された全10種を選択できます。

### Tonal

- Bell
- Bass
- Lead
- Organ
- Soft

### Percussion

- Tom
- Woodblock
- Cowbell
- Metallic
- Click

`<` / `>` ボタン、または `[` / `]` キーでPresetを選択し、LOADまたはEnterで読み込みます。

Presetは固定の再生モードではありません。LOADするとgeneratorとパラメータへ展開され、その後は自由に変更できます。

例えばCowbellをLOADすると、PMの編集パラメータへ展開されます。画像では `Editing: Cowbell` と、対応する波形・`wt.pm(...)` の生成コードを確認できます。

![Cowbell preset loaded into Tone Lab](images/tone-lab-preset.png)

```text
Generator: PM
ratio: 3
index: 1.7
gain: 0.40
```

パラメータを変更すると表示は `Editing: Custom` になります。同じPresetを再度LOADすれば元の値へ戻せます。

MML、Preview、Loop、Use Current Toneだけを変更してもPresetはCustomにはなりません。

## Toneを編集する

対応generator:

- PM
- Harmonics
- Pulse
- Sine
- Saw
- Triangle
- Square

共通パラメータ:

| Parameter | Tone Lab range |
| --- | --- |
| size | 32 / 64 / 128 / 256 / 512 |
| sample_bits | 1〜16 |
| gain | 0〜1、0.05刻み |

sizeは32 / 64 / 128 / 256 / 512点へ切り替えられます。変更は音色の細かさだけでなく、Pyxel 2.9.9のクロック丸めによる実ピッチにも影響します。特に高音域では確認が必要です。

まず128点を基準にし、ピッチ差が気になる場合は64点・32点も試してください。短い表では複雑な波形が粗くなる可能性もあるため、CUSTOM MMLで実際のフレーズを鳴らし、使用音域と音色の妥協点を耳で確認します。128点はピッチ精度の保証値ではなく、Tone Labも自動補正は行いません。詳しくは [Wavetable長とピッチ誤差](wavetable-pitch.md) を参照してください。

### PM

編集項目:

```text
ratio: 1〜16
index: 0〜10、0.1刻み
```

### Harmonics

H1〜H8をそれぞれ0〜1、0.05刻みで編集できます。

短いPresetの倍音配列をLOADした場合は、不足分を0で補って8項目として表示します。

### Pulse

`duty` を1/32〜31/32の範囲で調整できます。

## Pitch Error：音域ごとのピッチ誤差を確認する

Pyxelのwavetable再生では、同じ音程を指定しても、**wavetableの長さ（size）によって実際の再生ピッチに誤差が生じます**。Pyxel 2.9.9では、wavetableを読み進める再生クロックが整数単位へ丸められるためです。特に高い音域や長いwavetableでは、12平均律の目標周波数からのずれが大きくなる場合があります。

一方で、sizeを短くすれば常に有利というわけではありません。短いwavetableでは、PMや高次倍音を含む複雑な波形を表す点数が減るため、波形形状や音色の再現性が落ちる場合があります。

そのため `pyxel_wavetable` では、特定のsizeを常に最適とはせず、次のバランスを見て選ぶ方針としています。

- 実際に使う音域
- 許容できるピッチ誤差
- 波形・音色の再現性

Tone Labの **PITCH ERROR** 表示は、このうち「実際に使う音域に対して、各sizeでどの程度ピッチがずれるか」を事前に確認するための機能です。音を再生・録音せず、Pyxel 2.9.9で実測確認したクロックモデルから予測値を計算します。

右上の **PITCH ERROR** ボタンを押すと、WAVEFORM / CODE領域がピッチ診断表示へ切り替わります。**WAVE / CODE** で元の表示へ戻せます。

### 音域を指定する

初期音域はC3〜B5です。開始音・終了音それぞれの `−` / `+` ボタンで半音ずつ変更できます。

音名はMIDI方式（C4=60、A4=440Hz）で、選択範囲はC−1〜G9（MIDI 0〜127）です。端点では停止し、開始音が終了音を越えないように制限します。この範囲は数式上の診断範囲であり、Pyxelでの全音域の発音精度を保証するものではありません。

ここで指定するのは、**そのToneを実際に使う予定の音域**です。例えばメロディでC4〜A5だけを使うのであれば、その範囲を指定してsizeごとのピッチ誤差を比較します。

MMLから使用音域を自動抽出する機能はありません。使用する音域は手動で指定します。

### sizeごとの誤差を見る

表はsize 32 / 64 / 128 / 256 / 512について、指定音域内の全半音を同じ重みで集計します。

| 表示 | 意味 |
| --- | --- |
| MAX ABS | 指定音域内で最も大きい絶対ピッチ誤差 |
| AVG ABS | 指定音域内の絶対ピッチ誤差の平均 |

単位はcentで、100 centが半音です。現在編集中のsizeには `*` が付き、色はグラフの系列色と対応します。

MAX ABSが小さいほど、その音域内で大きく外れる音が少ないと判断できます。ただし、ここで評価しているのはクロック量子化によるピッチ誤差だけで、音色の良し悪しを示す値ではありません。

### グラフで音程ごとの誤差を見る

グラフは横軸が音程、縦軸が12平均律に対する符号付きcent誤差です。0 centより上は予測ピッチが高く、下は低くなります。

32 / 64 / 128点の3系列を基本とし、現在編集中のsizeが256または512ならその系列も追加します。Cの位置に音名を表示し、広い範囲ではラベルを間引きます。

wavetableのピッチ誤差は、音程が上がるにつれて単調に増えるわけではありません。クロック丸めの位置によって誤差の向きと大きさが変わるため、平均値だけでなく、実際に使う音程に局所的な大きなずれがないかもグラフで確認します。

sizeは左側のTONE欄で従来どおり手動変更します。Pitch Error表示がsizeを自動選択・変更することはありません。

### ±10 / ±25 centの参考線

グラフには0 cent基準線に加えて、±10 centと±25 centの参考線を表示します。

- **±10 cent** — ずれを注意して確認する目安
- **±25 cent** — 比較的大きなずれを考える目安

±10 centは破線、±25 centはより明るい実線で表示します。

これらは可聴性や許容度の絶対基準ではありません。感じ方は音色、同時発音、楽曲、聴取環境、聴取者によって変わります。Tone LabはGOOD / BADのような自動評価を行わず、size選択の判断材料だけを提供します。

縦軸の片側の範囲は `max(25.0, 表示系列の最大絶対誤差 × 1.1)` centです。最低でも−25〜+25 centを表示し、それを超える誤差では自動拡張します。これにより、小さな誤差だけのときに数centのずれがグラフ全体へ大きく拡大されることを避けます。

上部の `RANGE` に表示範囲、`GUIDE` に参考線の値を表示します。大きな誤差では±10 / ±25 centの線が中央付近に集まりますが、数値ラベルは引出線で実際のY位置へ結び、重なりを避けます。

### この表示が示しているもの

Pitch Error表示は、**wavetable sizeと目標音程から決まるクロック量子化による再生周期の誤差**を予測しています。

数値は[366条件の測定で確認したPyxel 2.9.9の整数クロックモデル](wavetable-pitch.md)に基づきます。録音やFFTによる実測値ではなく、Sound生成・再生・WAV出力も使いません。表示切替や音域変更によってPreviewを開始・停止・再スタートすることもありません。

この誤差は基本的にwavetable sizeと再生する音程で決まります。そのため、1つのwavetableが1周期を表す通常のsine、triangle、saw、pulse、harmonics、整数ratioのPMなどでは共通の判断材料として利用できます。音色やgainはこのクロック誤差の計算には影響しません。

一方で、次の問題はPitch Errorの数値には含まれません。

- 短いwavetableによる波形形状・音色の変化
- aliasing
- 倍音構成
- 聴感上の音量
- 基音が弱い、または存在しない特殊な波形での知覚音高

Tone Labはピッチの自動補正も行いません。Pitch Error表示で候補となるsizeを絞った後は、PreviewやCUSTOM MMLで実際の音色を確認し、使用音域・ピッチ精度・音色の妥協点を選んでください。

## Waveform

WAVEFORM欄には、現在のToneの1周期wavetableを表示します。

表示は `sample_bits` の整数レンジを振幅へ換算したもので、`gain` 適用前の波形形状です。

パラメータ変更時には同じ編集用Toneスロットを更新します。操作のたびに `pyxel.tones` へ新しいToneを追加しません。

## Preview

既定Preview:

```text
melody
bass
short
perc_low
perc_high
custom
```

Pキーで切り替えます。

再生中に切り替えると、新しいPreviewを先頭から再生します。停止中は選択だけ変更します。

### melody

通常のメロディで音色を確認します。

```text
T120 O3 L8 C D E G A G E D
```

### bass

低音域での聞こえ方を確認します。

```text
T110 O2 L8 C C G G A G E C
```

### short

短い発音を確認します。

```text
T120 O4 L16 C R C R C R C R
```

### perc_low / perc_high

既存のPyxel MML Envelopeを使った、パーカッション確認用Previewです。

`perc_low` は低音域、`perc_high` は高音域を中心に確認するためのパターンです。

## Use Current Tone

`Use Current Tone: ON` の場合、再生時に現在編集中のTone indexをMML先頭へ自動的に付加します。

例:

```text
入力:
T120 O3 L8 C D E G

実際の再生:
@4 T120 O3 L8 C D E G
```

CUSTOM MML内に別の `@n` が書かれている場合は、その位置から通常のPyxel Tone切替が有効です。

OFFの場合はMMLを変更せず、そのままPyxelへ渡します。

AキーでON/OFFを切り替えます。

## CUSTOM MML

CUSTOMを選ぶと任意のMMLを入力できます。

![Editing custom MML in Tone Lab](images/tone-lab-custom-mml.png)

画像は `T140 O4 L8 C E G > C < G E C` を入力した状態です。黄色い枠とカーソルが入力先を示し、STATUSには `FOCUS: MML` が表示されます。

編集開始:

```text
E
TAB
MML本文をクリック
```

編集時の主な操作:

| Operation | Key |
| --- | --- |
| カーソル移動 | ← / → |
| 行頭 / 行末 | HOME / END |
| 削除 | Backspace / Delete |
| 全選択 | Ctrl+A |
| Copy | Ctrl+C |
| Paste | Ctrl+V |
| 再生 | Enter / F5 |
| 停止 | F6 |
| 編集終了 | TAB / ESC |

MML欄は1行エディターです。長いMMLはカーソル位置に合わせて横スクロールします。

入力イベントに改行やタブが含まれる場合は空白へ変換します。

### Copy / Paste buttons

MML欄には次のボタンがあります。

- COPY MML
- PASTE MML

CODE欄には:

- COPY CODE

があります。

COPY MMLは現在表示中のMML全文、COPY CODEは生成コード全文をOSクリップボードへコピーします。PASTE MMLは編集中ならカーソル位置へ挿入し、Ctrl+Aで全選択していれば置換します。未編集のPreviewから押すとCUSTOMへ切り替え、貼り付けた内容を設定します。

Copy/PasteにはPythonの `tkinter` とデスクトップ環境が必要です。Pythonの配布方法によってはTkが別途必要になります。ライブラリ本体は `tkinter` に依存しません。コピー内容はTone Labを開いたまま別アプリへ貼り付けてください。

Tkが利用できない環境やClipboardへアクセスできない環境では `CLIPBOARD ERROR` を表示し、現在のMMLは保持します。

## Generated code

CODE欄には、現在の編集状態をgenerator呼び出しとして表示します。

PresetをLOADした場合でも、Preset関数ではなく展開後のgenerator設定を表示します。

![Generated Python code in Tone Lab](images/tone-lab-code.png)

画像はCowbellからratioとindexを変更し、COPY CODEを押した状態です。`Editing: Custom` となり、CODE欄の枠とSTATUSの `COPIED CODE TO OS CLIPBOARD` で操作対象と結果を確認できます。表示されているコードは次のとおりです。

```python
wt.pm(
    ratio=5,
    index=2.10,
    size=128,
    sample_bits=8,
    gain=0.40,
)
```

Harmonicsの例:

```python
wt.harmonics(
    [1.00, 0.40, 0.15, 0.00,
     0.00, 0.00, 0.00, 0.00],
    size=128,
    sample_bits=8,
    gain=0.50,
)
```

音を調整し、CUSTOM MMLで実際のフレーズを試してから、COPY CODEで自分のPyxelアプリへ持ち帰る使い方を想定しています。

## Playback

MML編集中でない場合:

| Operation | Key |
| --- | --- |
| Play / Stop toggle | SPACE |
| 先頭からPlay | F5 |
| Stop | S / F6 |
| Preview切替 | P |
| Use Current Tone | A |
| Loop | L |
| Tone項目選択 | ↑ / ↓ |
| 値変更 | ← / → |
| Preset選択 | [ / ] |
| Preset LOAD | Enter |
| MML編集 | E / TAB |
| Quit | ESC |

MML編集中は文字キーとSPACEを入力用に使うため、通常のショートカットにはなりません。

## Error handling

CUSTOM MMLは編集中に構文エラーになることがあります。

Tone LabはMML再生時の例外で終了せず、STATUS欄に `MML ERROR` を表示します。

入力内容は保持されるので、そのまま修正して再生できます。正常に再生できた時点でエラー表示をクリアします。

空のCUSTOM MMLもエラーとして扱います。

## Tone slot behavior

Tone Labは編集用Toneを1つだけ使います。Preset切替やパラメータ変更のたびにTone indexが増えることはありません。内部の更新方式は [Design](design.md) を参照してください。

## Scope

Tone Labは次の機能を実装しません。

- 独自MMLパーサ
- 独自シーケンサ
- Note On/Off管理
- 動的PM Envelope
- 毎フレームのwavetable変調
- 独自Sound / Music

MMLの解析、タイミング、再生はPyxelへ任せます。

## Related documentation

- [README](../README.md)
- [Design](design.md)
- [Pyxel API Reference](https://kitao.github.io/pyxel/web/api-reference/)
