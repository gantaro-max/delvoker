# Phase 33: Directional Surface Line Patterns

## 1. 背景

Phase 32でsurfaceタイルを単純化したが、面ごとの方向性が弱く、壁と床の区別が分かりにくくなった。

8x8タイルは画面全体へ反復されるため、線を入れる場合は面ごとに方向を明確に分ける必要がある。左右の壁は縦線、天井と床は横線を強調し、面の向きを視覚的に区別する。

## 2. 目的

- 左右壁は縦線模様を強調する。
- 天井と床は横線模様を強調する。
- 市松・千鳥格子・斜め格子に見える交互配置は避ける。
- 3Dビューの奥行きジオメトリは維持する。

## 3. 対象

- `assets/source/image2/surfaces/*.png`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. side wallは石目や明暗模様を持たせ、その中で縦方向の目地・割れを強調する。
2. ceiling / floorは石目や明暗模様を持たせ、その中で横方向の目地・割れを強調する。
3. front wallは壁面として、模様の中で縦方向の目地・割れをやや強くする。
4. B1F-B2Fは青系・赤系を避け、灰色系を中心にする。
5. B3F-B4F / B5F-B10Fも同じ方向ルールで更新する。
6. 8x8で線だけが強く出る場合は、surfaceタイルを16x16へ拡張する。
7. `tools/convert_image2_assets.py --surfaces` で再取り込みする。
8. 色番号と3D描画スモークを確認する。

## 5. 受け入れ条件

- side wall / front wallは線だけではなく模様を持ち、その中で縦方向のアクセントが強い。
- ceiling / floorは線だけではなく模様を持ち、その中で横方向のアクセントが強い。
- B1F-B2Fで青系・赤系を使わない。
- 市松・千鳥格子状の交互配置が存在しない。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- Reopened after visual review: the first Phase 33 output became line-only rather than patterned surfaces with directional emphasis.
- `tools/convert_image2_assets.py` と `ui/renderer_3d.py` を16x16 surfaceタイルに更新した。
- `assets/source/image2/surfaces/*.png` を、石目模様の中で方向アクセントを持つ16x16タイルとして再生成した。
- B1F-B2Fは天井/床を `0,7,13` の横方向アクセント、横壁/正面壁を `0,7,13` の縦方向アクセント、奥面を `0,13` の暗色模様にした。
- B3F-B4F / B5F-B10Fも同じ線方向ルールで更新した。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` の Bank 0 `V=128` 行へ再取り込みした。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークとプレビュー保存が成功した。
