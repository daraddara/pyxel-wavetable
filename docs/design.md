# 設計と責務の境界

```text
数式 / パラメータ / 浮動小数サンプル
    ↓ 波形生成
    ↓ ピーク正規化（任意）
    ↓ クリップとsample_bitsに応じた量子化
pyxel_wavetable
    ↓
pyxel.Tone生成

ここまでが責務
------------------------
ここから先はPyxel

Sound
Music
MML
Channel
play
playm
```

## モジュール

- `generators.py`: 入力検証、1周期の生成、正規化、量子化、Tone生成。全経路を `from_samples()` に集約する。
- `presets.py`: generatorを呼ぶ5つの小さな静的音色。独自の生成アルゴリズムを持たない。
- `__init__.py`: generator、プリセット、デフォルト定数を公開する。

標準ライブラリとPyxelだけで実装する。各呼出しは独立した新しいToneを返し、Pyxelのグローバルスロットに触れない。Tone生成に `pyxel.init()` は不要。スロットへの登録・Sound設定・再生時は利用アプリがPyxelを初期化する。

gainは `Tone.gain` にだけ設定する。サンプルに焼き込むとTone側でも掛かって二重に減衰するため、正規化・量子化から分離する。波形は浮動小数で処理し、最後にunsigned整数へ変換する。全点0は中点へ量子化する。DC除去・補間・再サンプリングは行わない。

`from_samples()` は入力の長さを維持する。他のgeneratorは `[0, 2π)` を等間隔でサンプリングし、重複する終端を含めない。sawは上昇方向。pulseは先頭からduty割合だけ正値になる。dutyの時間分解能は1/sizeなので、任意のdutyが正確に表現できるとは限らない。

## 固定PM波形

公開API `pm()` は位相変調（phase modulation、PM）の式 `sin(p + index * sin(ratio*p))` から固定波形を生成する。ratioを正の整数に限定し、キャリア1周期で波形が閉じる条件を保つ。envelopeや非整数比の複数周期テーブルは実装しない。

## 再生例の音声方針

目的は同一メロディによる静的音色の比較。音楽的な音質最適化は対象外。

| 例 | Tone | Sound | Channel | 再生とループ |
| --- | --- | --- | --- | --- |
| basic_tones | 初期スロットの後に5つ追加 | 0〜4 | 0のみ | 選択時play、フレーズをループ |
| melody_compare | 初期スロットの後に5つ追加 | 0〜4 | 0のみ | Music 0に5フレーズを登録しplaym |
| custom_wave | 初期スロットの後に1つ追加 | 0 | 0のみ | play、フレーズをループ |

全例のフレーズは8音、speed=12、volume=7、gain=0.5。通常は約0.8秒/フレーズ。SEや重複音はなく、優先順位・同時発音数は1。再選択・再開で同じチャンネルを置き換え、停止操作ではPyxelのstopを呼ぶ。フレーズ間の発音タイミングはPyxelだけが管理する。`update()` はキー操作のみで、音源更新や発音位置監視を行わない。

## 意図的に実装しないもの

- Note On/Off検出
- 発音位置監視
- 毎フレームwavetable変更
- 動的PM envelope
- 独自シーケンサ
- 独自Music
- 独自Sound
- Pyxel内部Rust拡張

Pyxel本体および `kitao/pyxel` は参照専用とし、本プロジェクトから変更しない。

## 検証と今後

pytestはモックではなく実際の `pyxel.Tone` を使い、波形の値、整数レンジ、正規化、clip、gain、独立性、入力検証を確認する。再生例では通常のSound/Musicによる接続を確認する。自動検証は主観的な音質評価を代替しない。

今後の候補は音程別の試聴評価、帯域制限の任意指定、プリセットの調整、複数周期での非整数比対応。現段階では実装せず、最小APIの利用結果を見て判断する。

## 初期実装の確認結果（2026-11-01）

- Windows / Python 3.13.5 / Pyxel 2.9.9で、pytestは62件すべて成功。
- editable install、wheel作成、wheelを別ディレクトリへ展開してのimport・PM Tone生成に成功。
- 同じPyxel 2.9.9で3つの例をheadless実行。検証用ハーネスだけで `init(headless=True)` と有限のフレームループに置き換え、元のupdate/draw、Pyxelの再生、flip、キー入力APIを実行した。
- basic_tonesは90フレームで1〜5の選択・停止・再開、custom_waveは90フレームで停止・再開を確認。melody_compareは390フレームで停止・再開とSound 0〜4の巡回を確認。全例で生成後のwavetableに変更がないことを検証し、画面も確認。
- 通常のMML（`T120 @4 V80 L8 O3 CDEG`）で生成Toneを指定し、play後に再生位置が得られることを確認。
- 補助のPyxel MCP環境（Pyxel 2.9.5）でも画面とキー切替を確認。音声レンダリングはbasic_tones/custom_waveが各3秒、Music比較が13秒で成功し、非無音の出力を確認。FFT由来の推定音名は倍音に影響されるため、音程の正確性の判定には使っていない。
- 主観的な試聴評価、Python 3.10〜3.12での実行、他OSでの実行は未実施。

ローカル検証環境は `.venv` に作成し、既存のインストール済み依存を `--system-site-packages` で利用した。Windows sandboxの一時ディレクトリへの書込み制約を避けるため、作業中だけTEMP/TMPを `.venv/tmp` に設定した。配布ライブラリにはこの設定や検証用ハーネスを含めない。
