# BGM Compare

このブランチに保存した実験用PoCです。公開examplesへの採用は未決定で、ライブラリ本体の機能ではありません。

Pyxelの `gen_bgm()` で生成した同じ曲を、標準Toneとwavetable Toneで比較するサンプルです。

## 実験の目的と限界

同じMMLのToneだけを差し替え、実際の楽曲でピッチ差や音色・音量差を確認するために残しています。単音やパラメータ編集を中心とするTone Labとは異なり、複数パートをまとめて聴き比べられます。[ピッチ調査](wavetable-pitch.md)の発端となった条件（preset=4 / transp=0 / instr=3 / seed=42）も再生できます。

現状は既定size=128の固定置換で、size比較UI、周波数測定、音量整合、差分の定量評価はありません。A/B切替では先頭へ戻るため、同じ再生位置での即時比較もできません。調査の366条件を再測定するツールではなく、今後の[T4〜T6の品質評価](technical-issues.md)に向けた試聴の出発点です。ピッチ補正は行わず、128点で音程が保たれる保証もありません。

`tests/test_bgm_compare.py` はTone復元、MML維持、状態遷移などを検証しますが、GUI描画や実際の出音の品質は保証しません。公開する場合はそれらを別途確認する必要があります。

`examples/test.py` は別の初期試作です。MML内のTone指定を差し替え、二組のSound/Musicを作る経緯を残しています。アプリとは独立しており、`eval`を使うため外部入力には使わず、公開サンプルとしての整理も未実施です。

## 起動

```sh
python examples/bgm_compare.py
```

起動時にpreset=4、transp=0、instr=3、seed=42で曲を生成し、標準音でループ再生します。画面のボタンはマウスで操作でき、Roboto Monoを同梱フォントから読み込みます。

## 比較する

| 操作 | キー |
| --- | --- |
| 標準Toneへ切替 | A |
| wavetable Toneへ切替 | B |
| 再生・停止 | SPACE |
| 選択したモードで先頭から再生 | R |
| ループ切替 | L |
| ノイズを標準のまま残す／METALLICへ置換 | D |
| 終了 | ESC |

再生中のA/B切替では、同じ曲を先頭から再生し直します。停止中は音色の選択だけを変えます。曲の途中位置を保った切替やクロスフェードは行いません。

生成した4チャンネルのMMLは変更せず、Tone 0〜3の参照先だけを切り替えます。音符・テンポ・MML音量・Envelope・Vibratoは同じです。標準音のToneオブジェクトは変更せず保持し、Aで元へ戻します。曲の再生成はA/B切替から独立しています。

| Tone index | 標準音 | wavetable音 |
| --- | --- | --- |
| 0 | Triangle | `wt.soft()` |
| 1 | Square | `wt.lead()` |
| 2 | Pulse | `wt.pm(ratio=3, index=1.8)` |
| 3 | Noise | 初期状態では標準Noiseを維持。Dで `wt.metallic()` に置換 |

同じTone indexを複数パートが使う場合、それらすべてが同じ置換音色になります。パートごとに異なる音色を割り当てる方式ではありません。

ドラムに使われるノイズは、周期的なwavetableでは同じ性質を再現できません。まず標準Noiseを残して旋律の音色差を比較し、Dで金属的な周期波形へ置き換えた違いも試せます。

各wavetable Toneのgainには対応する標準Toneの値を使います。ただし波形の実効値や倍音構成は異なるため、聴感音量を一致させる処理ではありません。

## 曲を生成する

↑↓で項目を選び、←→または行右側の−／＋ボタンで値を変更し、G / GENERATEで反映します。変更前の曲の条件は `PLAYING SCORE`、未反映の変更は `PENDING` として表示します。

| 項目 | 範囲・意味 |
| --- | --- |
| preset | 0〜7。Title / Departure / Town / Peaceful / Field / Adventure / Battle / Crisis |
| instr | 0：Melody+Reverb+Bass、1：Melody+Bass+Drums、2：Melody+Sub+Bass、3：Melody+Sub+Bass+Drums |
| transp | −5〜+5半音 |
| seed | 0〜999999 |

N / NEXT SEEDはseedを1増やして生成します。同じPyxelバージョン・同じ4条件で生成すれば、同じMMLを得られます。再生中の生成は新しい曲を先頭から再生し、停止中の生成は停止を維持します。生成やMMLの検証に失敗した場合は画面にエラーを表示し、それまでの曲を保持します。

## 再生の責務

音声は `gen_bgm()` の返すMMLを通常のSound 0〜3へ設定し、Music 0でチャンネル0〜3を再生します。編成によって音符がないチャンネルは使いません。SEは重ねず、A/B切替や曲変更時は既存再生を置き換えます。

発音タイミングとループはPyxelの `playm()` が管理します。独自シーケンサ、ノート監視による発音制御、毎フレームのwavetable変調はありません。Tone数は操作ごとに増えません。ライブラリ本体やPyxel本体の変更も不要です。

- [README](../README.md)
- [Tone Lab Manual](tone-lab.md)
- [Pyxel API Reference](https://kitao.github.io/pyxel/web/api-reference/)
