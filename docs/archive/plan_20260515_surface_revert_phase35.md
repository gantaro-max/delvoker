# Phase 36: Revert Phase 35 Surface Depth Changes

## 1. 背景

Phase 35で空間を濃くするため、B1F-B2Fのsurfaceを `1,13` へ変更し、奥行きフレームを黒 `0` にした。しかし実画面ではPhase 34より見た目が悪化した。

Phase 34では黒い格子・浮遊パネルの問題が改善していたため、Phase 35の色調整と黒フレーム強調を撤回し、Phase 34相当を再ベースにする。

## 2. 目的

- Phase 35で悪化した見た目を戻す。
- B1F-B2FをPhase 34相当の `7,13` 灰色系surfaceへ戻す。
- surface描画時の黒フレーム強調を撤回する。
- B3F-B4F / B5F-B10FもPhase 34相当の色分けへ戻す。

## 3. 対象

- `tools/convert_image2_assets.py`
- `ui/renderer_3d.py`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. B1F-B2Fの可視surfaceを `7,13` へ戻す。
2. B3F-B4Fを `3,5`、B5F-B10Fを `1,2` へ戻す。
3. `ui/renderer_3d.py` のsurface描画時黒フレーム強調を撤回し、従来の `COL_DARK_GRAY` フレームへ戻す。
4. `tools/convert_image2_assets.py --surfaces` で再取り込みする。
5. プレビューと描画スモークを確認する。

## 5. 受け入れ条件

- B1F-B2Fの可視surfaceが `7,13` で構成される。
- surface描画時の奥行きフレームが黒強調されない。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed, then superseded by Phase 37.

- B1F-B2Fの可視surfaceを `7,13` へ戻した。
- B3F-B4Fを `3,5`、B5F-B10Fを `1,2` へ戻した。
- surface描画時の黒フレーム強調を撤回した。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` へ再取り込みした。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークとプレビュー保存が成功した。
- ただしsurfaceタイル調整そのものが収束しないため、Phase 37でsurface texture描画を無効化した。
