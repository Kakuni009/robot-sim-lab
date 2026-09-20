# 状態確認スクリプトとPython文法

[目次へ](README.md)

## 何のために使ったか

CubeのXを0.8 mにすると、つかんで持ち上げた後に止まった。
アプリ自体は操作できたが、PowerShellには失敗理由が表示されなかったため、
実行中のサンプルに状態を問い合わせた。

## 実行場所とコード

Isaac Simの **Window > Script Editor** を開き、入力欄に貼り付けて
**Run（Ctrl+Enter）** を押す。失敗直後、RESET・LOADを行う前に実行する。
通常のPowerShellや別のPythonプロセスでは、動作中のサンプルを調べられない。

以下は当日実行した調査コード。ファイルへの書き込みや制御パラメーターの変更は行わない。
ただし、広くオブジェクトを探索するため、実行時に警告が出た（後述）。

```python
import gc
from isaacsim.robot_motion.examples.manipulation.interactive.pick_place.pick_place_example import FrankaPickPlaceInteractive

for obj in gc.get_objects():
    if isinstance(obj, FrankaPickPlaceInteractive):
        print(obj.get_controller_status())
```

## 各行の意味

### import: 機能を読み込む

`import gc` はPython標準のメモリ管理用モジュールを読み込む。
`gc.get_objects()` は、ガベージコレクターが追跡しているオブジェクトの一覧を返す。
Python内のすべての値が必ず含まれるわけではない。

`from モジュール名 import 名前` は、指定したモジュールから特定の名前を読み込む文法。
長いドット区切りの部分はモジュールの階層で、最後の `FrankaPickPlaceInteractive` はクラス名。
クラスは設計図、インスタンスはその設計図から作られた実体と考える。
このimportだけで、新しいロボットやサンプルを作っているわけではない。

### for: 一つずつ調べる

`for obj in gc.get_objects():` は、一覧から一つずつ取り出し、変数 `obj` に入れる。
行末の `:` と次行のインデントで、繰り返す処理の範囲を表す。
`obj` という名前は自分で決められる変数名で、Pythonの予約語ではない。

### if / isinstance: 対象を選ぶ

`isinstance(obj, FrankaPickPlaceInteractive)` は、そのクラスまたは派生クラスの
インスタンスかを判定する。`if` の条件が真のときだけ、さらに字下げされた行を実行する。

### メソッド呼び出しとprint

`obj.get_controller_status()` は、見つかったサンプルのメソッドを呼び出す。
`.` は対象が持つ属性やメソッドへのアクセス、`()` は関数・メソッドの呼び出しを表す。
取得した結果を外側の `print(...)` が文字として表示する。

## 出力は辞書

ユーザーの実行結果画像で確認した内容（読みやすく改行）:

```python
{
    'phase': 'FAILED',
    'active_cube': 0,
    'done': False,
    'failed': False,
    'failure_reason': 'LIFT timed out after 5.000 s (position error 0.0215 m, orientation error 0.0219 rad).'
}
```

`{キー: 値}` は辞書（dict）。文字列は引用符で囲み、`False` は真偽値なので囲まない。

| キー | 意味 |
|---|---|
| phase | 内側の制御器の動作段階。この出力ではFAILED |
| active_cube | 対象Cubeの番号。0は最初のCube |
| done | タスク全体が完了したか |
| failed | タスク側が返す失敗フラグ |
| failure_reason | タスク側または制御器側に保持された失敗理由 |

この出力には `failed: False` と `phase: FAILED` が併存した。
`failed` だけを見て成功と判断しない。`PickPlaceTask.failed` は内部状態による条件分岐があり、
phaseとは取得経路が異なる。ただし、この実行時の不一致の原因は未確定。

## 警告と限界

実行時には `torch.distributed.reduce_op` のFutureWarningと、Script Editorの
`Failed to parse error` 警告も出た。結果の辞書は取得できている。
警告はこの探索コードの `isinstance` 行で発生したもので、先に起きたLIFT停止とは別。

この方法は一時的な調査用。複数のサンプルが残っていれば複数行出る可能性があり、
何も見つからなければ何も出ない。通常の実装ではサンプルへの参照を変数に保持し、
gcによる探索をせず直接メソッドを呼ぶ。

このコードは当日実行済み。資料作成時は構文のみ再検証し、GUI上では再実行していない。
