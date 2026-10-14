# Robot Sim Lab 解説ノート

会話で使ったスクリプトと、実際に読んだソースコードを振り返るための資料。
対象はローカルに導入済みのIsaac Sim 6.1.0.0。確認日: 2026-09-18。

## 読む順番

1. [状態確認スクリプトとPython文法](01-status-script.md)
   — Script Editorで何を実行したか、各行の意味、出力と警告の読み方。
2. [Franka Pick Placeの制御コード](02-pick-place-source.md)
   — 座標の取得、動作段階、到達判定、時間切れ、今回の実験との対応。
3. [作業セルの設定とUSD保存](03-workcell.md)
   — GUIで追加した目印、座標、保存できるものと次回の確認事項。
4. [WorkcellCameraからPNGを撮影する](04-camera-capture.md)
   — 仮想カメラの追加、Script Editorからの撮影、自動採番、初回画像の確認結果。
5. [位置変更データを手作業で作る](05-manual-position-dataset.md)
   — X座標を変えた3枚の撮影、CSVラベル、Stageからの座標取得と変更。
6. [位置変更・撮影・CSV追記を自動化する](06-position-dataset-script.md)
   — `generate_position_dataset.py` の行ごとの解説、async/await、遭遇したエラーの読み方。
7. [撮影結果を自動で検証する](07-verify-dataset.md)
   — `verify_dataset.py` の構成、`main()` の意味、3D→画素の投影計算、背景の中央値による部品検出と残像検証（図解）、63点撮影でのにじみによる誤検出、撮影順を変えた再撮影（v05）と輪郭状の残像。

今回Script Editorへ追加したのは、既存サンプルの状態を読む調査コード。
ロボットの制御コードは変更していない。目印はPythonではなくGUIで追加した。

## 既存資料との使い分け

| 資料 | 役割 |
|---|---|
| [reader.md](../reader.md) | 全体方針、日付別の進捗、次回の開始点 |
| [environment.md](../environment.md) | 起動方法・環境構築・検証状況 |
| [インストール記事下書き](../isaac-sim-install-zenn-draft.md) | 導入時の経験をまとめたZenn向け原稿 |
| このフォルダ | スクリプトや制御の仕組みを学び直す資料 |

今後、カメラ追加や画像保存のコードを作ったら、実行するコードは `scripts/` 等に置き、
このフォルダに「目的・実行場所・使い方・文法・確認結果」を解説するMarkdownを追加する。
目次にもリンクし、実行済みと未検証を区別する。

ソースへのリンクは本プロジェクトの `.venv` を参照するため、環境未構築のPCでは開けない。
パッケージ更新で行番号が変わるので、解説ではクラス名・関数名を手掛かりにする。
