# Robot Sim Lab

NVIDIA Isaac Sim 6.1 を Windows 11 に導入し、ロボットアーム（Franka）の作業セルで
**画像データセットを自動で作り、その品質を自動で検証する**までを学んだ記録です。

## やったこと

1. Isaac Sim の導入と、Franka の Pick & Place サンプルの動作確認
2. 作業セルに仮想カメラを追加し、Script Editor から PNG を撮影
3. 部品の位置を変えながら撮影し、位置ラベルを CSV に記録する処理を自動化（63点）
4. 撮影結果の自動検証：3D 座標を画素に投影してラベルと画像の位置ずれを確認し、
   背景の中央値との差分で部品の検出と残像の有無を調べる
5. ラベル位置を画像に重ねて目視で確認するツール

## 構成

| パス | 内容 |
|---|---|
| `scripts/` | 撮影・データセット生成・検証・重ね描きのスクリプト |
| `docs/` | スクリプトごとの解説ノート（[目次](docs/README.md)） |
| `environment.md` | 実行環境・再構築・起動の手順 |
| `reader.md` | 日付ごとの進捗と、次回の開始点 |
| `*.usd` | 作業セルのシーン |

## 実行環境

Windows 11 / Python 3.12（uv）/ PyTorch 2.11 + CUDA 12.8 / Isaac Sim 6.1 / RTX 5070 Ti。
構築は `setup.ps1`、起動は `launch.ps1`。詳しくは [environment.md](environment.md)。

スクリプトの出力先は `C:/cloud/robot-sim-lab/outputs` に固定しています。
別の場所に置く場合は、各スクリプトの `OUTPUT_DIR` を書き換えてください。

## ライセンス

[MIT](LICENSE)
