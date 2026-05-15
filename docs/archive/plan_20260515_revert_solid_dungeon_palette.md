# Phase 39: Revert Solid Dungeon Palette

## 1. 背景

Phase 38で3Dビューの単色ポリゴン配色を茶系・グレー系へ変更したが、実画面では不自然に見えたため撤回する。

## 2. 目的

- Phase 38の配色変更を元に戻す。
- `WALL_COLS` をPhase 37時点の配色へ戻す。
- 3Dビューの輪郭線を黒 `0` から `COL_DARK_GRAY` へ戻す。

## 3. 対象

- `constants.py`
- `ui/renderer_3d.py`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 受け入れ条件

- `WALL_COLS` がPhase 37相当へ戻っている。
- 3Dビュー輪郭線が `COL_DARK_GRAY` に戻っている。
- `draw_3d_view(..., assets_loaded=True/False, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 5. Execution Result

Status: Completed.

- `constants.py` の `WALL_COLS` を `[11, 3, 3, 1]` へ戻した。
- `ui/renderer_3d.py` の単色ポリゴン輪郭線を `COL_DARK_GRAY` へ戻した。
- `assets_loaded=True/False`、`dungeon_floor=1/3/5` の描画スモークとプレビュー保存が成功した。
- `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` にPhase 39を反映した。
