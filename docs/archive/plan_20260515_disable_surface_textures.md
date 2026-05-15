# Phase 37: Disable 3D Surface Textures

## 1. 背景

Phase 31-36で3Dビューsurface素材の配色、線方向、16x16化、格子回避、濃色化、撤回を試したが、タイル反復によるちらつき・格子感・空間の読みづらさが収束しなかった。

小さいsurfaceタイルで遠近と空間表現を作る方針は現時点では不安定であり、ゲーム画面としての可読性を優先して単色ポリゴン描画へ戻す。

## 2. 目的

- 3Dビューのsurfaceテクスチャ描画を無効化する。
- 既存の単色遠近ポリゴン描画を常用する。
- ダンジョン探索画面の可読性と安定性を優先する。
- surface素材と変換定義は残すが、実描画では使用しない。

## 3. 対象

- `ui/renderer_3d.py`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. `ui/renderer_3d.py` にsurface textureの有効/無効フラグを置く。
2. デフォルトは無効にし、`assets_loaded=True` でも単色ポリゴン描画を使う。
3. 既存surface取り込みコードは将来再検討用に残す。
4. `draw_3d_view(..., assets_loaded=True/False, dungeon_floor=1/3/5)` の描画スモークを確認する。

## 5. 受け入れ条件

- `assets_loaded=True` でもsurfaceタイルが描画されない。
- 3Dビューが単色遠近ポリゴンとして表示される。
- `draw_3d_view(..., dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- `ui/renderer_3d.py` に `USE_SURFACE_TEXTURES = False` を追加した。
- `assets_loaded=True` の場合でもsurfaceタイルを描画せず、既存の単色遠近ポリゴン描画を使うようにした。
- surface素材とBank 0取り込み定義は将来再検討用に残した。
- `draw_3d_view(..., assets_loaded=True/False, dungeon_floor=1/3/5)` の描画スモークとプレビュー保存が成功した。
- `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` にPhase 37を反映した。
