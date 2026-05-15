# Phase 38: Solid Dungeon Palette

## 1. 背景

Phase 37で3Dビューsurfaceテクスチャを無効化し、単色ポリゴン描画へ戻した。現行の単色3Dビューは `WALL_COLS` に緑系が含まれており、壁タイルを使わない状態ではダンジョン壁として不自然に見える。

## 2. 目的

- 3Dビューの単色ポリゴン配色から緑系を外す。
- 茶系・グレー系を中心にした自然なダンジョン壁色へ変更する。
- surface texture無効化状態の可読性を維持する。

## 3. 対象

- `constants.py`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. `WALL_COLS` から `COL_GREEN` / `COL_DARK_GREEN` を除外する。
2. 近景から遠景にかけて、グレー・茶・暗色へ落ちる配色にする。
3. `draw_3d_view(..., assets_loaded=True/False, dungeon_floor=1/3/5)` の描画スモークを確認する。

## 5. 受け入れ条件

- `WALL_COLS` に緑系カラーが含まれない。
- 3Dビューが茶系・グレー系の単色ポリゴンとして表示される。
- `draw_3d_view(..., dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- `constants.py` の `WALL_COLS` を `[13, 4, 4, 0]` に変更し、緑系を除外した。
- `ui/renderer_3d.py` の単色ポリゴン輪郭線を黒 `0` に変更し、青みを抜いた。
- `assets_loaded=True/False`、`dungeon_floor=1/3/5` の描画スモークとプレビュー保存が成功した。
- `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` にPhase 38を反映した。
