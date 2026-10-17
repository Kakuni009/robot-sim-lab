# 実行環境

## 構成

- Python 3.12.13（uvで取得した専用ランタイム）
- PyTorch 2.11.0+cu128
- Isaac Sim 6.1.0.0（インストール済み）
- NVIDIAドライバ595.97 / RTX 5070 Ti 16GB

Pythonは `.runtime/python/`、仮想環境は `.venv/`、パッケージキャッシュは `.cache/`。
これらはGit管理対象外。Isaac Simの実行時キャッシュはアプリ既定のユーザーフォルダにも作られる。
Isaac Labは動作学習へ進む段階で追加する。

## 再構築

PowerShellで実行する。uvがPATH上に必要。

```powershell
cd C:\cloud\robot-sim-lab
.\setup.ps1
```

PyTorchは公式CUDA 12.8インデックス、Isaac SimはPyPIとNVIDIA公式インデックスから取得する。
大容量パッケージの取得と展開に時間・空き容量が必要。

## 起動

```powershell
cd C:\cloud\robot-sim-lab
.\launch.ps1
```

初回にNVIDIAのライセンス同意が表示された場合は、内容を確認して応答する。
初回起動はシェーダーなどのキャッシュ生成で時間がかかる場合がある。

互換性チェッカー:

```powershell
.\launch.ps1 -Mode check
```

CUDA計算とヘッドレス起動・終了の簡易テスト:

```powershell
.\launch.ps1 -Mode smoke
```

このテストはアプリの初期化と更新を確認する。ロボット制御、物理挙動、画像生成の品質は別途検証する。

## 検証状況

- Python環境作成: 成功。
- CUDA行列計算: 成功。GPU名を実測で確認。
- Isaac Sim: ヘッドレス初期化、30回のアプリ更新、終了コード0を確認。初回初期化は約68秒。
- `pip check`: `No broken requirements found.`
- 拡張キャッシュの登録ファイル86,374件を確認し、欠落0件。
- GUI起動とFranka Pick Placeの把持・運搬はユーザー操作で確認済み（2026-09-17）。配置変更時の停止などは [reader.md](reader.md) の進捗記録を参照。
- 互換性チェッカーのGUI、物理挙動の定量評価、画像生成は未検証。
- PowerShellスクリプト構文 / Python構文 / ランタイムのGit除外: 確認済み。
- Windowsの `LongPathsEnabled` は0。システム設定は変更していない。

## インストール時の問題と解決

通常のpipでは、深いディレクトリの展開がパス長制限で失敗した。
出力: `OSError: [Errno 2] No such file or directory` と長いパス対応を有効にする旨のヒント。
レジストリ変更は `Requested registry access is not allowed.` で失敗し、値は変更されなかった。
Pythonのprefixに拡張パス表記を付ける方法も、相対パス `../../Scripts/coacd` で
`OSError: [Errno 22] Invalid argument` となった。

最終的に **Isaac Simのインストーラーをuvへ切り替えて成功**。
`scripts/install_isaac.py` はuvを呼び出す。専用環境の重複した依存メタデータもuvが整理した。
起動ログにはIntel内蔵GPUをスキップする警告とUSD関連の警告があるが、
RTX 5070 Tiで初期化とアプリ更新は成功した。アセット変換の互換性は今後の実装で検証する。

## 起動時の問題: スマート アプリ コントロール（2026-09-30）

以前は起動できていた `launch.ps1` が、`uv trampoline failed to spawn Python child process`
（`os error 4551`）で失敗した。`.venv\Scripts\python.exe` 単体でも
「アプリケーション制御ポリシーによってこのファイルがブロックされました」となった。

- `Get-MpComputerStatus` の `SmartAppControlState` は `On`。
- `Microsoft-Windows-CodeIntegrity/Operational` に3033/3077/3118を記録。対象は `.venv\Scripts\python.exe`。
- uv取得のPython本体と仮想環境の `python.exe` は `NotSigned`。
- `.venv` 内の exe/dll/pyd は Valid 2752件、NotSigned 392件。署名なしは torch/lib、scipy、numpy、
  PyOpenGL、mujoco などPyPIの一般的なライブラリに集中していた。

署名付きPythonへの置き換えではライブラリ側が残るため、ユーザー判断でスマート アプリ コントロールをオフにした。
その後、GUI起動と `workcell-v02-camera.usd` の表示を確認した。`-Mode smoke` の再実行は未記録。
評価モードからオンに切り替わった時期は未確認。経緯は
Zenn 記事の下書きにまとめた (記事原稿は別リポジトリで管理)。

匿名テレメトリの2設定は、起動スクリプトと簡易テストで無効にしている。

## 参照

- [Isaac Sim Python環境の公式手順](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_python.html)
- [Isaac Sim動作要件](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)
