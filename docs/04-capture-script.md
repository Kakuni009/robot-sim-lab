# カメラ画像と部品位置の保存

[目次へ](README.md)

## 目的

`WorkcellCamera` の画像1枚と、その時点の `PartCube` の位置を同じフォルダへ保存する。
合成データの「画像」と「正解データ」を対応付ける最小の形。
部品の配置・色・照明を変えながらの連続生成は、この1枚が正しく保存できてから追加する。

## 実行場所と使い方

1. `workcell-v02-camera.usd` を開き、シミュレーションは停止した状態にする。
2. Window > Script Editor を開き、[scripts/capture_one.py](../scripts/capture_one.py) の内容を貼り付けて実行する。
3. `robot-sim-lab/outputs/capture-日時/` に画像と `label.json` ができる。`outputs/` はGit管理外。

保存先は開いているUSDファイルの場所から決めるため、USDを保存していない新規シーンでは使えない。

## 処理の流れ

| 行 | 意味 |
|---|---|
| `omni.usd.get_context().get_stage()` | GUIで開いているシーン（Stage）を取得する |
| `GetPrimAtPath(...)` / `IsValid()` | カメラと部品が存在するかを確認し、名前違いなら止める |
| `rep.create.render_product(...)` | 指定カメラから描画する出力先を作る。解像度もここで決める |
| `BasicWriter` / `initialize(rgb=True)` | Replicatorの標準Writer。RGB画像をファイルへ書き出す |
| `await rep.orchestrator.step_async(rt_subframes=4)` | 1フレーム描画して書き出す。追加のサブフレームで描画を安定させる |
| `ComputeLocalToWorldTransform` | 親のTransformも含めたワールド座標を計算する |
| `asyncio.ensure_future(capture())` | Script EditorはGUIと同じイベントループで動くため、非同期関数を登録して実行する |

`async def` / `await` は「描画の完了を待つ間、GUIを止めない」ための書き方。
通常の関数から直接 `capture()` を呼んでも実行されない点に注意する。

## label.json の中身

- 使ったシーン、カメラのパス・位置・焦点距離・水平アパーチャ・解像度
- 部品のパスとワールド座標（m）

画像内のどのピクセルに部品が写るかは、まだ保存していない。
カメラの位置と画角から計算するか、Replicatorのバウンディングボックス出力を使う。どちらにするかは次の段階で決める。

## 確認状況

- クラウド環境での構文チェックのみ（Isaac Simは未実行）。
- Isaac Sim 6.1.0での動作、Writerの出力ファイル名、画像の見た目は未確認。
  初回実行時の出力とエラーを記録する。
