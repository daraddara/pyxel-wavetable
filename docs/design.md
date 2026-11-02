# 設計と責務の境界

```text
数式 / パラメータ / 浮動小数サンプル
    ↓ 波形生成
    ↓ ピーク正規化（任意）
    ↓ クリップとsample_bitsに応じた量子化
pyxel_wavetable
    ↓
pyxel.Tone生成
    ↓（必要に応じて明示的に呼出し）
add_tone / add_tones
    ↓
Tone index取得

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
- `presets.py`: generatorを呼ぶ10個の小さな静的音色。うち5個はパーカッション系。不変の内部定義 `_PresetDefinition` と読み取り専用レジストリで、音色値・既定gain・カテゴリを一元管理する。公開関数は同じ定義で生成し、既存のシグネチャ・既定値・結果を維持する。独自の生成アルゴリズムを持たない。
- `registration.py`: Toneを `pyxel.tones` の末尾へ登録し、通常のindexを返す。
- `__init__.py`: generator、プリセット、登録API、デフォルト定数を公開する。

標準ライブラリとPyxelだけで実装する。generatorの各呼出しは独立した新しいToneを返し、Pyxelのグローバルスロットに触れない。Tone生成に `pyxel.init()` は不要。登録APIは初期化済みの `pyxel.tones` にだけ作用し、Sound設定や再生は行わない。スロットへの登録・Sound設定・再生時は利用アプリがPyxelを初期化する。

`add_tone(tone)` は現在の長さをindexとして取得し、末尾に追加して `int` を返す。`add_tones(tones)` はiterableを一度list化して入力順に追加し、連続したindexのtupleを返す。空入力は `()` で、既存Toneを変更しない。上書き・削除・名前解決・ToneRef・ToneBankは導入しない。登録先の変更を複数スレッドから同時に行う仕組みは対象外。

返されたindexは既存Pyxel APIに直接渡す。Pyxel 2.9.9のSound文字列は各文字を個別のTone番号として解釈するため、`Sound.set(..., str(index), ...)` は0〜9に限る。複数桁のindexはMMLの `@{index}` で利用できる。例では新しく初期化したPyxelの標準4 Toneの後に追加し、4〜8の範囲を使う。`sound.tones[:]` による後付け設定は使わない。

gainは `Tone.gain` にだけ設定する。サンプルに焼き込むとTone側でも掛かって二重に減衰するため、正規化・量子化から分離する。波形は浮動小数で処理し、最後にunsigned整数へ変換する。全点0は中点へ量子化する。DC除去・補間・再サンプリングは行わない。

`from_samples()` は入力の長さを維持する。他のgeneratorは `[0, 2π)` を等間隔でサンプリングし、重複する終端を含めない。sawは上昇方向。pulseは先頭からduty割合だけ正値になる。dutyの時間分解能は1/sizeなので、任意のdutyが正確に表現できるとは限らない。

## 固定PM波形

公開API `pm()` は位相変調（phase modulation、PM）の式 `sin(p + index * sin(ratio*p))` から固定波形を生成する。ratioを正の整数に限定し、キャリア1周期で波形が閉じる条件を保つ。envelopeや非整数比の複数周期テーブルは実装しない。

## 再生例の音声方針

目的は同一メロディによる静的音色の比較と、静的スペクトルに既存MML Envelopeを組み合わせた打楽器系音色の確認。音楽的な音質最適化は対象外。

| 例 | Tone | Sound | Channel | 再生とループ |
| --- | --- | --- | --- | --- |
| basic_tones | 初期スロットの後に5つ追加 | 0〜4 | 0のみ | 選択時play、フレーズをループ |
| melody_compare | 初期スロットの後に5つ追加 | 0〜4 | 0のみ | Music 0に5フレーズを登録しplaym |
| custom_wave | 初期スロットの後に1つ追加 | 0 | 0のみ | play、フレーズをループ |
| percussion_presets | 初期スロットの後に5つ追加 | MML文字列を直接使用 | 0のみ | キー1〜5で単音、ループなし |

メロディ比較3例のフレーズは8音、speed=12、volume=7、gain=0.5。通常は約0.8秒/フレーズ。SEや重複音はなく、優先順位・同時発音数は1。再選択・再開で同じチャンネルを置き換え、停止操作ではPyxelのstopを呼ぶ。フレーズ間の発音タイミングはPyxelだけが管理する。`update()` はキー操作のみで、音源更新や発音位置監視を行わない。

パーカッション例は独立した5つのMML文字列を使う。T120 / V100 / Q100 / L4で、各キー押下時にチャンネル0を置き換える。同時発音は1、初期状態は無音。TOM / WOODBLOCK / COWBELL / METALLIC / CLICKの音程はそれぞれO2 / O4 / O4 / O5 / O6のC、Envelopeは初期音量127から12 / 5 / 10 / 18 / 3 tickで0へ減衰する。gainは各プリセットの既定値。短時間での再押下や停止も通常のplay/stopに任せる。これは音色の方向性を示すもので、非周期ノイズや実楽器の精密再現は対象外。

## 意図的に実装しないもの

Tone Lab（`examples/tone_lab.py`）はexample/UI層で、ライブラリ本体のAPIや依存には含めない。`ToneSettings` は既存generatorへの引数と表示コードを組み立て、`Preview` は既存MMLを選んでPyxelへ渡すだけとする。ユーザーのコードやMMLをevalせず、MMLの解析・発音タイミングはPyxelに任せる。

Tone Labは内部一覧取得用の `_preset_definitions()` を参照する。名前や数値をUI側に複製せず、生成済みToneも逆解析しない。カテゴリは表示用のtonal/percussionで、パッケージの公開APIには追加しない。

```text
不変のPreset定義
    ├─ 公開Preset関数10種 → pyxel.Tone
    └─ Tone Labの一覧 → LOAD → 独立したToneSettings
                                   ↓
                           通常のgenerator → 編集用Tone
```

LOADは定義を新しい編集状態へコピーし、Harmonicsの不足分だけ0で埋める。定義の倍音はtuple、編集側は独立したlistなので、編集で元の定義を変えない。Presetの選択カーソルと読み込み済みの名前は分け、LOAD後だけ名前を表示する。通常のパラメータ増減で実際の生成コードが変わったら名前を外してCustomとする。MML・Preview・Loop・Use Current Toneは音色生成条件ではないため名前を維持する。再LOADで元の値へ戻り、試聴設定やTone indexは保持する。コード表示は常に展開したgenerator設定を使う。対応generatorのPresetを定義へ追加すれば、Tone Labの一覧には個別の追加コードなしで現れる。

PキーでPreviewを切り替えるとき、再生中なら既存再生を停止して新しいPreviewを先頭から即再生する。停止中なら選択だけを変える。CUSTOMが不正なら停止状態でエラーを表示し、以前のループを残さない。ループ・Use Current Toneは現在の設定を使う。

MML編集中を除き、SPACEは再生中なら停止、停止中なら選択したPreviewを先頭から再生するトグルとする。F5は常に先頭から再生、S/F6は停止。MML編集中のSPACEは空白入力に使い、再生状態を変えない。

起動時に `add_tone()` で編集用スロットを1つ確保し、設定変更・PLAY時だけ公開Tone属性へ生成結果を反映する。通常フレームではToneを再生成せず、パラメータ編集でも再発音しない。再生位置の参照は画面のPLAYING/STOPPED表示だけに使い、ノート監視やタイミング制御には使わない。Use Current ToneはMML先頭にindexを付加するだけで、ユーザーが書いた後続の `@n` は変更しない。

MML編集はフォーカスを明示し、文字入力とショートカットを分ける。文字入力はPyxelの公開 `input_text` を使う。MMLのCopy/PasteとCODEのCopyは、対象欄内のボタンで操作でき、黄色い枠とステータスで対象を示す。MML本文のクリックでカーソル位置を指定する。CODEは読み取り専用で、貼り付けたPythonを実行する機能は追加しない。

Pyxel Editorの内部バッファ方式を参照したが、外部テキストとの交換にはOSクリップボードが必要なため、example内の `TextClipboard` が標準ライブラリのtkinterを遅延初期化して読み書きする。隠したTkウィンドウはクリップボード所有権を維持するため保持し、初期化後はUIのupdateでTkのイベントも処理して外部アプリからの取得要求へ応答する。これは音源や発音タイミングの更新ではない。Pyxel本体やライブラリ本体へ依存を追加せず、クリップボード例外は画面へ表示してMMLを保持する。入力と解析エラーを保持し、修正後の再生で復帰する。生成コード・エラー表示を含むUIは英数字を使う。

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
