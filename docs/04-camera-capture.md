# WorkcellCameraからPNGを撮影する

## 今回の目的

保存済み作業セルに仮想カメラを追加し、そのカメラから見えるRGB画像をPNGへ保存する。
これは合成データ生成へ進む前の最小確認であり、物体検出用ラベルの生成はまだ行わない。

## 実施した操作

1. `workcell-v01.usd` を開き、ロボット、部品、2つの目印が復元されることを確認した。
2. Viewportの構図を決め、カメラメニューの `Create from View` を実行した。
3. 作成されたCamera Primを `/WorkcellCamera` と命名した。
4. シーンを `workcell-v02-camera.usd` として別名保存した。
5. Script Editorから [`capture_workcell.py`](../scripts/capture_workcell.py) を実行した。

Script Editorで実行した入口は次の1行。

```python
exec(open(r"C:\cloud\claude_hub\robot-sim-lab\scripts\capture_workcell.py", encoding="utf-8").read())
```

## スクリプトの仕組み

- `get_active_viewport()` で現在のViewportを取得する。
- 選択中のカメラが `WorkcellCamera` であることを確認し、別視点の誤撮影を防ぐ。
- `next_viewport_frame_async()` で次の描画フレームを待つ。
- `capture_viewport_to_file()` で画面UIを除いたViewport画像をPNGへ保存する。
- `workcell-camera-001.png` から順に空いている番号を選び、既存画像を上書きしない。

生成画像はGit管理対象外の `outputs/` に保存する。

## 確認結果

- `outputs/workcell-camera-001.png` の生成に成功した。
- ロボット、青い部品、供給位置と運搬先の目印が画像に含まれた。
- 撮影時にロボットの一部が選択状態だったため、初回画像にはオレンジ色の輪郭が入った。
- 自動採番へ変更後、選択輪郭のない `workcell-camera-002.png` の生成に成功した。
- 続けて部品のX座標を変え、`workcell-camera-003.png` と `004.png` の生成にも成功した。

## 次の確認

手動で作った3枚と世界座標の対応は [位置変更データを手作業で作る](05-manual-position-dataset.md)
に記録した。次は位置変更・撮影・ラベル保存を一つのスクリプトへ段階的にまとめる。
