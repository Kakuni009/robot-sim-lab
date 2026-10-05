# 位置変更・撮影・CSV追記を自動化する

## 今回の目的

[05](05-manual-position-dataset.md) では、部品の移動、撮影、正解座標の記録を手作業で行った。
今回はこの3つを [`generate_position_dataset.py`](../scripts/generate_position_dataset.py) にまとめる。
部品のX座標を変えるたびに、画像とラベルが1組ずつ自動で残るようにする。

コードは本人がScript Editorへ入力し、「ループ → 撮影 → CSV追記」の順に一段ずつ足した。
確認日は2026-10-06。

## 実行場所と使い方

- **実行場所**: Isaac Sim 6.1.0.0 のScript Editor。`omni.usd` などは
  Isaac Sim内のPythonでしか読み込めないため、通常のPythonでは動かない。
- **前提**:
  - `workcell-v02-camera.usd` を開いておく。
  - Viewportのカメラを `WorkcellCamera` にしておく。
- **入口**: スクリプトをScript Editorに貼り付けて実行する。
  [04](04-camera-capture.md) と同じく `exec(open(...).read())` で読み込んでもよい。
- **変える値**: 撮影したいXの値を `POSITIONS` に並べる。
- **出力**:
  - 画像 `outputs/v02/pos-x<X>.png`
  - ラベル `outputs/v02/labels.csv`
  - `outputs/` はGit管理対象外。
- **再実行**: 同じ名前の画像があると止まる。撮り直す場合は、該当する画像とCSVの行を消してから実行する。

## 全体の流れ

```text
現在のStageから PartCube の座標属性を取得し、元の位置を original に保持する
カメラが WorkcellCamera か確認する
POSITIONS の各 x について:
    PartCube の X を x に変更する
    描画が1フレーム進むのを待つ
    Viewport を PNG に保存する（完了まで待つ）
    実際の座標を labels.csv に1行追記する
最後に（失敗した場合も）PartCube を original に戻す
```

1回の処理の順番は「動かす → 描画を待つ → 撮る → 記録する」に固定している。
この順番を守ることが、画像とラベルの対応を正しく保つ要点になる。

## コードを上から読む

### import（1〜11行目）

```python
import asyncio
import csv
from pathlib import Path

import omni.usd
from omni.kit.viewport.utility import (
    capture_viewport_to_file,
    get_active_viewport,
    next_viewport_frame_async,
)
```

- `asyncio`、`csv`、`pathlib` はPython標準のモジュール。`omni.*` はIsaac Sim（Omniverse Kit）のモジュール。
- 複数の名前を改行して `import` するときは、丸括弧 `( )` で囲む。
  最初は波括弧 `{ }` で書いて構文エラーになった。Pythonの `{ }` は辞書と集合の記号で、
  `import` 文では使えない。

### 設定値（14〜16行目）

```python
POSITIONS = [0.45, 0.60]
OUTPUT_DIR = Path("C:/cloud/claude_hub/robot-sim-lab/outputs/v02")
LABELS_PATH = OUTPUT_DIR / "labels.csv"
```

- 実行のたびに変える値を、ファイルの先頭に大文字の名前でまとめる。大文字にするのは「定数」を示すPythonの慣習。
- `Path` 同士の `/` は割り算ではなく、パスの連結になる。`Path` クラスが `/` の意味を
  上書きしているため。`csv` モジュールにはその上書きがない（後述のエラーと関係する）。
- `v02` という専用のフォルダに分けたのは、カメラ位置を変える前に撮った
  `workcell-camera-00x.png` と混ざらないようにするため。

### 撮影関数 `capture`（18〜21行目）

```python
async def capture(viewport, path):
    result = capture_viewport_to_file(viewport, file_path=str(path))
    if not await result.wait_for_result(completion_frames=30):
        raise RuntimeError(f"Capture failed: {path}")
```

- `capture_viewport_to_file` は、呼んだ時点ではまだ保存を終えていない。
  返ってくるのは「依頼を受け付けた」というオブジェクトで、
  その `wait_for_result` を `await` して、ファイルの書き出しが終わるのを待つ。
- 引数名は `file_path` と `completion_frames`（末尾にs）。綴りを間違えると、
  Pythonはその名前の引数が無いとエラーを出す（今回 `flie_path` と `completion_frame` で発生した）。
- 失敗したら `raise` で処理を止める。止めないと、画像の無いラベル行が書かれてしまう。

### 本体 `move_part_loop`（24〜50行目）

#### 対象の取得と元の位置の保持

```python
stage = omni.usd.get_context().get_stage()
cube = stage.GetPrimAtPath("/World/PartCube")
translate = cube.GetAttribute("xformOp:translate")
original = translate.Get()
```

- 05で確認した「Stage → Prim → 属性」の取り方と同じ。
- `original` は、最後に元の位置へ戻すための控え。9/23にX=0.6のまま
  保存せずに作業を終えたことを踏まえて追加した。

#### カメラの確認

```python
camera_path = str(viewport.camera_path)
if not camera_path.endswith("/WorkcellCamera"):
    raise RuntimeError(f"Select WorkcellCamera (current: {camera_path})")
```

- Viewportが別のカメラ（Perspectiveなど）のままだと、違う視点の画像が撮れてしまう。
  それを撮影の前に止めるための確認。

#### ループ本体

```python
for x in POSITIONS:
    path = OUTPUT_DIR / f"pos-x{x:.2f}.png"
    if path.exists():
        raise RuntimeError(f"Already exists: {path}")
    translate.Set(type(original)(x, original[1], original[2]))
    await next_viewport_frame_async(viewport)
    await capture(viewport, path)
    append_label(path.name, translate.Get())
    print(f"Captured {path.name} at {translate.Get()}")
```

| 行 | 意味 |
|---|---|
| `f"pos-x{x:.2f}.png"` | f文字列の `:.2f` は「小数点以下2桁で表示」。`0.6` は `0.60` になる。ファイル名の長さを揃えるため |
| `path.exists()` | 既存の画像を上書きしないための確認 |
| `type(original)(x, ...)` | `original` と同じ型でベクトルを作る。属性の型は `double3` で、値は `Gf.Vec3d`。YとZは元の値を使い、Xだけを変える |
| `await next_viewport_frame_async` | 座標を変えた直後の画面は、まだ古い位置の絵のまま。1フレーム描画させてから撮影する |
| `append_label(..., translate.Get())` | 設定したつもりの `x` ではなく、Stageから読み直した実際の値を記録する |

#### `finally` で元の位置に戻す

```python
try:
    ...
finally:
    translate.Set(original)
    print(f"Restored to {translate.Get()}")
```

`finally` の中身は、ループが最後まで進んだときも、途中で例外が出たときも必ず実行される。
CSVで失敗した回にも `Restored to (0.5, …)` が出て、部品は0.5に戻った。

### ラベル追記 `append_label`（52〜58行目）

```python
def append_label(image_name, position):
    is_new = not LABELS_PATH.exists()
    with open(LABELS_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["image", "x", "y", "z"])
        writer.writerow([image_name, position[0], position[1], position[2]])
```

- `"a"` は追記モード。ファイルが無ければ作り、あれば末尾に書き足す。`"w"` にすると毎回中身が消える。
- `with` は、ブロックを抜けるとき（例外のときも）ファイルを閉じる。
- `newline=""` は、csvモジュールの公式ドキュメントが求めている指定。付けないとWindowsで行の間に空行が入る。
- 見出し行を書くかどうかは、ファイルを開く**前**に `exists()` で判定する。
  `open(..., "a")` の時点でファイルが作られるため、開いた後に判定すると常に「ある」になってしまう。
- `encoding` は指定していない。前回Script Editorで `encoding` 付きの書き込みがエラーになったため。
  中身は英数字だけなので、文字コードの違いは生じない。

`append_label` は `move_part_loop` より後に定義されているが、問題なく動く。
関数の中の名前は、呼ばれた時点で探されるからである。`move_part_loop` が実際に動くのは
スクリプトを最後まで読み込んだ後なので、その時点で `append_label` はすでに定義されている。

### 起動（60行目）

```python
asyncio.ensure_future(move_part_loop())
```

- Isaac SimのUIは、内部でasyncioのイベントループを回し続けている。
  `ensure_future` は、そのループに `move_part_loop` を「後で実行する仕事」として登録する。
- Script Editorの実行自体はすぐ終わる。その後、UIの描画と交互に `await` の位置で進む。
- `time.sleep` で待つと、UIのスレッドが止まって描画も進まない。フレームを待つには `await` を使う。

## `async def` と `def` の違い

| | `def` | `async def` |
|---|---|---|
| 呼び出したとき | 中身がすぐに最後まで実行される | 中身はまだ実行されない。「後で実行できる処理」（コルーチン）が返るだけ |
| 中身を実行するには | 呼ぶだけでよい | `await` するか、`ensure_future` でイベントループに登録する |
| 途中で一時停止できるか | できない | `await` の位置で一時停止できる。停止している間は、他の処理（UIの描画など）が進む |
| `await` を書けるか | 書けない（構文エラー） | 書ける |

`await` は `async def` の中でしか書けない。そのため、関数を `async def` にする理由は
「中で `await` を使いたいから」になる。

### なぜ `await` を書くのか

理由は2つある。

**1. 時間のかかる処理が終わるまで、次の行に進まないため**

撮影もフレームの描画も、頼んだ瞬間には終わらない。`await` を付けずに先へ進むと、
終わっていない処理の結果を前提に次の行が実行されてしまう。

| `await` を外した場合 | 起きること |
|---|---|
| `next_viewport_frame_async` | 部品を動かす前の絵のまま撮影する。画像とCSVの座標が食い違う |
| `wait_for_result` | 保存が終わる前に次へ進む。保存に失敗してもラベルが書かれる |

**2. 待っている間に、待っている相手を動かすため（Isaac Simではこちらが重要）**

フレームを描画するのはIsaac Sim自身で、しかもこのスクリプトと同じ1本の流れ（メインスレッド）の上で動いている。

- 普通の `def` の中で `time.sleep` などを使って描画を待つと、スクリプトが流れを握ったままになる。
  Isaac Simは描画に取りかかれず、待っているフレームが永遠に来ない。UIも固まる。
- `await next_viewport_frame_async(viewport)` に来ると、`move_part_loop` は一時停止し、Isaac Simに制御を返す。
  その間にIsaac SimはUIの処理と次のフレームの描画を行い、終わると止まった行の次から再開する。

つまり `await` は、ただ待つだけではない。「待っている間は順番を譲るので、終わったらここに戻してほしい」という合図である。
スレッドを使った並列処理ではなく、1本の流れが `await` の位置で順番を譲り合っている。

### このスクリプトでの使い分けと連鎖

```text
append_label          : 待つものがない             → def
capture               : 保存の完了を待つ            → async def（中で await）
move_part_loop        : フレームと capture を待つ   → async def（中で await）
Script Editorの最上位  : await を書けない場所        → ensure_future で登録する
```

`await` が必要な処理を呼ぶ関数は、その関数自身も `async def` にする必要があり、`async` が外側へ連鎖していく。
連鎖のいちばん外側はScript Editorの最上位だが、ここには `await` を書けない。
そこで `ensure_future` を使い、「後でイベントループの上で実行してほしい」とIsaac Simに渡している。

### よくある落とし穴

`async def` の関数は、`await` を付けずに呼ぶと何も起きない。

```python
capture(viewport, path)          # コルーチンが作られるだけで、撮影されない
await capture(viewport, path)    # 撮影し、完了まで待つ
```

付け忘れてもエラーでは止まらない。Pythonは後から
`RuntimeWarning: coroutine ... was never awaited` という警告を出すだけなので、気づきにくい。

### 動きを確かめる実験（未検証）

```python
import asyncio

async def hello():
    print("A")
    await asyncio.sleep(1)
    print("B")

c = hello()
print(type(c))
asyncio.ensure_future(c)
print("C")
```

予想される出力の順番:

1. `<class 'coroutine'>`: `hello()` を呼んでも `A` は出ず、コルーチンが返るだけ。
2. `C`: `ensure_future` は登録するだけで、スクリプトはそのまま先に進む。
3. `A`: スクリプトが終わり、イベントループが登録された処理を始める。
4. `B`: 1秒後に、`await` で止まっていた処理が再開する。

Script Editorではまだ実行していない。実行したら結果をここに追記する。

## 遭遇したエラーと読み方

### `UnboundLocalError: cannot access local variable 'writer'`

原因は `csv.writer(f)` を `csv/writer(f)` と打ち間違えたこと。

- Pythonは `csv / writer(f)`、つまり「`csv` を `writer(f)` で割る」と読む。
- 同じ関数の中に `writer = ...` という代入があるため、`writer` はこの関数のローカル変数として扱われる。
- 右辺を計算する時点では、`writer` にまだ値が入っていない。そのため「代入前のローカル変数を使った」というエラーになる。

エラー文が打ち間違いを直接指していないので、`^^^^` の印が付いた行を目で確かめるのが早い。

### `Task exception was never retrieved`

`ensure_future` で起動した処理の中で例外が出ると、このような形で表示される。
例外の本体はTracebackの最終行にあるので、まずそこを読む。

### 失敗後に残るファイル

CSVで失敗した回には、撮影に成功した `pos-x0.45.png` と、0バイトの `labels.csv` が残った。

- 画像が残っていると、再実行時に `Already exists` で止まる。
- 空のCSVが残っていると、ファイルは「ある」と判定され、見出し行が書かれなくなる。

そのため、2つとも削除してから再実行した。
見出し行の判定を `not exists() or stat().st_size == 0` に変えれば、空のCSVが残っても見出しが書かれる（未実施）。

## 確認結果

X=0.45、0.60での実行時の出力:

```text
Captured pos-x0.45.png at (0.45, 0, 0.025800000876188278)
Captured pos-x0.60.png at (0.6, 0, 0.025800000876188278)
Restored to (0.5, 0, 0.025800000876188278)
```

`outputs/v02/labels.csv`（CRLF改行、BOMなし）:

```csv
image,x,y,z
pos-x0.45.png,0.45,0.0,0.025800000876188278
pos-x0.60.png,0.6,0.0,0.025800000876188278
```

- 先に実行したX=0.55、0.65の画像でも、Xを増やすと部品は画面の下へ動いた（画面の下が +X）。
- X=0.65では、部品が供給目印の下端にかかり始める。
- Zの `0.025800000876188278` は丸め誤差。単精度で表した0.0258を、倍精度の値として持っているため。

## 現時点の制約

- 変えるのはXだけ。Yを変えても、ファイル名にYが入らないので名前が重複する。
- ラベルは3Dの世界座標だけで、画像上のピクセル位置やバウンディングボックスは無い。
- `POSITIONS` に同じ値が2つあると、2つ目で `Already exists` になって止まる。
- 出力先は絶対パスで書いてあるので、別のPCではそのまま使えない。

次の作業は [reader.md](../reader.md) の「次回の開始点」を参照。
