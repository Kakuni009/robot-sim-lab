# Franka Pick Placeの制御コードを読む

[目次へ](README.md)

## どのファイルが何を担当するか

リンクはインストール済みIsaac Sim 6.1.0.0の実ファイル。
今回、これらのライブラリ本体は編集していない。

| ファイル | 主な役割・読む関数 |
|---|---|
| [pick_place_example_extension.py](../.venv/Lib/site-packages/isaacsim/exts/isaacsim.robot_motion.examples/isaacsim/robot_motion/examples/manipulation/interactive/pick_place/pick_place_example_extension.py) | ボタンとUI。`_on_pick_place_button_event()`、`_update_status()` |
| [pick_place_example.py](../.venv/Lib/site-packages/isaacsim/exts/isaacsim.robot_motion.examples/isaacsim/robot_motion/examples/manipulation/interactive/pick_place/pick_place_example.py) | GUIとタスクの接続。`execute_pick_place_async()`、`_pick_place_physics_callback()` |
| [pick_place_task.py](../.venv/Lib/site-packages/isaacsim/exts/isaacsim.robot_motion.examples/isaacsim/robot_motion/examples/manipulation/pick_place_task.py) | 物体座標、状態取得、動作結果の検証。`_capture_setpoint()`、`step()`、`status()` |
| [controllers/pick_place.py](../.venv/Lib/site-packages/isaacsim/exts/isaacsim.robot_motion.examples/isaacsim/robot_motion/examples/manipulation/controllers/pick_place.py) | 段階ごとの目標と遷移。`_target()`、`_phase_complete()`、`forward()` |

## ボタンからロボットが動くまで

```text
START PICK PLACE
  → execute_pick_place_async(): 制御をリセットし、物理更新のコールバックを登録
  → 物理更新ごとに _pick_place_physics_callback()
  → PickPlaceTask.step(dt): 状態を読み、必要なら目標を取得
  → PickPlaceController.forward(): 現在の段階の指令を生成
  → scenario.apply_robot_state(): ロボットへ指令を適用
```

コールバックは「物理更新が起きたら呼んでもらう関数」。`dt` はその時間刻み。
完了した場合や `step()` がFalseを返す場合はコールバックを解除する。
そのため、ロボットの制御が停止してもアプリの画面操作は続けられる。

## 物体は画像認識していない

`PickPlaceTask._capture_setpoint()` は、Cubeの `get_world_poses()` からワールド座標を取得する。
シミュレーターが管理する物体の状態を直接読むので、カメラも検出モデルも使わない。
`step()` の `_needs_reset` が真のときに目標を取得し、制御器の `reset()` へ渡す。
制御器は目標を保持するため、移動するCubeを常時追跡する仕組みとは異なる。

既定の配置は、供給位置 `(0.5, 0.0, 0.0258)`、運搬先 `(0.0, 0.5, 0.0258)`。
GUIで確認した初期CubeのZは0.02575 m。コードの丸められた既定値と区別して記録する。
複数Cubeやグリッパー種類による高さ補正もあるため、汎用コード全体を単純な固定座標処理と混同しない。

## 状態遷移で作業を分ける

`PickPlacePhase` は `Enum`（列挙型）で、動作段階に名前を付けている。

| 段階 | 動作 |
|---|---|
| APPROACH_PICK | 部品の上へ近づく |
| DESCEND_PICK | つかむ位置へ下りる |
| GRASP | グリッパーを閉じる |
| LIFT | 持ち上げる |
| APPROACH_PLACE | 運搬先の上へ移動する |
| DESCEND_PLACE | 置く位置へ下りる |
| RELEASE | グリッパーを開く |
| RETREAT | 手先を退避する |
| DONE / FAILED | 制御器の完了 / 失敗 |

このように「今の段階」と「次へ進む条件」で動作を構成する仕組みを状態機械と呼ぶ。
Cubeが着地して静止したかは、タスク側の `_finish_active_goal()` でも別途確認する。
制御器のDONEとタスク全体の完了は同じ判定ではない。

## 持ち上げ目標と到達判定

`_target()` はLIFTで、取得した把持目標のZに `lift_height`（既定0.30 m）を加える。
その後、把持位置と制御対象フレームの位置・向きの変換を行う。
「Cube中心から単純に30 cmの点」と「実際に制御する手先の目標」は厳密には区別する。

`_phase_complete()` は現在の手先と目標の位置・向きのずれを計算する。
通常の既定条件は次のとおり。

- 位置誤差が0.015 m（1.5 cm）以内
- 向きの誤差が0.12 rad（約6.9度）以内
- 両方を満たした状態が0.10秒以上続く

GRASPには別の位置許容値を設定でき、GRASP・RELEASEではグリッパーの完了も確認する。
浮き上がっただけではLIFT完了とは限らない。

## 時間切れが起きる場所

`forward()` は、到達条件を満たさず、その段階の制限時間に達したとき、
段階名と誤差を含む `RuntimeError` を発生させる。
同じ関数内の `except` が受け取り、`_fail()` で失敗状態を保存して `None` を返す。
アプリ全体へ未処理例外を投げ続ける構造ではない。

LIFTの既定制限は5.0秒。`step()` が `dt` を加算するシミュレーション時間であり、
人間が時計で測った実時間と常に一致するとは限らない。

今回X=0.8で得た結果は、LIFTの5秒経過時点で位置誤差0.0215 m、向き誤差0.0219 rad。
位置誤差だけが許容範囲を超えていた。したがって時間切れは確認できたが、
関節制限・姿勢・制御速度など、誤差が残った根本原因までは確定していない。
コードに「Xが0.8以上なら停止」という境界値があるわけではない。

## なぜPowerShellに失敗理由が出なかったか

UIの `_update_status()` はReadyやScene clearedなどを表示・printするが、
このUIには制御器の失敗理由を定期表示する接続がない。
一方 `get_controller_status()` → `PickPlaceTask.status()` で内部の辞書を取得できる。
そのため、[調査スクリプト](01-status-script.md)で直接読み出した。

資料の数値・関数はローカルソースと照合済み。制御変更や新たな動作試験は行っていない。
