# 位置変更データを手作業で作る

## 目的

自動生成の前に、部品の位置変更、カメラ撮影、正解座標の記録を手作業で経験する。
一度に変える条件はX座標だけとし、画像の変化を切り分けられるようにした。

## 生成したデータ

`outputs/` はGit管理対象外。次のファイルがローカルに生成されたことを確認した。

| 画像 | `/World/PartCube` の世界座標X | Y | Z |
|---|---:|---:|---:|
| `workcell-camera-002.png` | 0.5 | 0.0 | 0.0258 |
| `workcell-camera-003.png` | 0.6 | 0.0 | 0.0258 |
| `workcell-camera-004.png` | 0.7 | 0.0 | 0.0258 |

カメラ、ロボット、照明、マーカーは同じ条件を維持した。画像を比較し、Xを増やすごとに
青い部品が画像上で同じ方向へ移動することを確認した。世界座標のX方向と画像の水平・垂直方向は
一致せず、カメラの姿勢によって投影方向が決まる。

`outputs/labels.csv` には次の対応を保存した。

```csv
image,x,y,z
workcell-camera-002.png,0.5,0.0,0.0258
workcell-camera-003.png,0.6,0.0,0.0258
workcell-camera-004.png,0.7,0.0,0.0258
```

これは画像と3D世界座標の対応であり、画像上の2Dバウンディングボックスではない。

## Script Editorで確認したPythonとUSD API

位置の列を順番に処理する最小ループを実行した。

```python
positions = [0.5, 0.6, 0.7]

for index, x in enumerate(positions, start=1):
    print(f"Image {index}: set PartCube X to {x}")
```

現在のStageからPrimを取得し、存在とパスを確認した。

```python
import omni.usd

stage = omni.usd.get_context().get_stage()
cube = stage.GetPrimAtPath("/World/PartCube")

print(cube.IsValid())
print(cube.GetPath())
```

`xformOp:translate` から現在位置を読み、元の座標型とY・Zを維持してXだけを変更した。

```python
translate = cube.GetAttribute("xformOp:translate")
position = translate.Get()

new_position = type(position)(
    0.6,
    position[1],
    position[2],
)

translate.Set(new_position)
print(translate.Get())
```

最後の実行ではLive Stage上のXが0.5から0.6へ変わった。実行時刻は保存済みUSDの更新時刻より後で、
この最後の変更はディスクへ保存されていない。次回はUSDを開き直してX=0.5を確認してから始める。

## 遭遇した点

- Script Editorでは日本語IME入力が動作しなかったため、コードと出力は英語に統一した。
- `Path.write_text(..., encoding="utf-8")` がScript Editor上で引数エラーになった。
  `encoding` を外した再実行でCSV保存に成功し、実ファイルの内容とUTF-8 BOMなしを確認した。
- `0.0258` は内部の浮動小数点表現で `0.025800000876188278` と表示された。
  これは丸め誤差であり、今回の値変更による異常ではない。

## 次回の開始点

1. `workcell-v02-camera.usd` を開き直し、`/World/PartCube` のXが0.5であることを確認する。
2. 今日確認した「ループ」「座標変更」「フレーム待ち」「撮影」を少しずつ一つにまとめる。
3. 各画像のファイル名と座標を、撮影と同時にラベルへ追記する。
4. 自動生成後は部品をX=0.5へ戻し、画像とCSVを目視確認する。
