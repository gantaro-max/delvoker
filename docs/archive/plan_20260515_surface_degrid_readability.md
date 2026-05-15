# Phase 34: Degrid Surface Readability Fix

## 1. 背景

Phase 33で16x16 surfaceタイルへ拡張し、面ごとの線方向を入れたが、黒い連続線が太い枠として見え、灰色の四角いパネルが宙に浮いているような見た目になった。

原因は、タイル内に高コントラストの黒い連続線を入れたことで、3Dビューの反復タイリング時に格子・額縁・浮遊パネルとして読まれてしまう点にある。

## 2. 目的

- surface素材から黒い連続線を除去する。
- 四角い枠・格子・浮遊パネルに見える模様を避ける。
- 方向感は連続線ではなく、短い欠け・擦れ・明暗の偏りで表現する。
- B1F-B2Fは灰色系を中心にしつつ、黒い目地を使わない。

## 3. 対象

- `assets/source/image2/surfaces/*.png`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. B1F-B2F surfaceでは黒 `0` をFar以外の模様線に使わない。
2. 天井/床は横方向の短い擦れを、左右壁/正面壁は縦方向の短い擦れを入れる。
3. 連続する水平線・垂直線・外枠状の模様を避ける。
4. B3F-B4F / B5F-B10Fも黒い格子を避け、短い方向アクセントにする。
5. `tools/convert_image2_assets.py --surfaces` で再取り込みし、プレビューを確認する。

## 5. 受け入れ条件

- B1F-B2FのCeiling / Side Wall / Front Wall / Floorに黒 `0` が含まれない。
- surfaceタイル内に外枠状・格子状の連続線が存在しない。
- B1F-B2Fプレビューで灰色の四角いパネルが浮いて見えない。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- `tools/convert_image2_assets.py` に16x16 surfaceパターン定義を追加した。
- surface取り込みはPNG読み込みではなく、定義済みパターンをBank 0へ直接書き込む方式に変更した。
- B1F-B2FのCeiling / Side Wall / Front Wall / Floorから黒 `0` を除外し、`7,13` の短い擦れ模様に変更した。
- B3F-B4Fは `3,5`、B5F-B10Fは `1,2` の短い擦れ模様にした。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` へ再取り込みした。
- B1F-B2Fの可視面に黒 `0` が含まれないことを確認した。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークとプレビュー保存が成功した。
