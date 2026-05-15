# Phase 32: Simplify 3D Surface Tiles

## 1. 背景

Phase 31でB1F-B2Fの赤みは解消したが、青みが残り、千鳥格子状のちらつきやタイル反復の見苦しさは解消しきれていない。

8x8タイルを3Dビュー全面に敷き詰めるため、細かい石目・割れ・ドット装飾は反復時にノイズとして目立つ。タイル画像は絵として作り込むより、単純な面色と少数の大きな線に限定する必要がある。

## 2. 目的

- B1F-B2Fの青みとちらつきを抑える。
- surfaceタイルをほぼ単色にし、細かいドットや交互配置を廃止する。
- B3F-B4F / B5F-B10Fも同じ低情報量のタイルへ更新する。
- 3Dビューの奥行きジオメトリは維持する。

## 3. 対象

- `assets/source/image2/surfaces/*.png`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. 8x8 surfaceタイルを「主色 + 0-2本の太めの線」まで単純化する。
2. B1F-B2Fは灰色 `13` を主色にし、青系の主色を使わない。
3. 横壁は縦ストリップで引き伸ばされるため、細かい縦模様を入れない。
4. `tools/convert_image2_assets.py --surfaces` で再取り込みする。
5. B1F-B2Fの色番号と3D描画スモークを確認する。

## 5. 受け入れ条件

- B1F-B2Fの主色が青系ではなく `13` 中心である。
- B1F-B2Fタイルに1px交互のパターンが存在しない。
- surfaceタイルの視覚情報量がPhase 31より少ない。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- `assets/source/image2/surfaces/*.png` をほぼ単色の8x8タイルとして再生成した。
- B1F-B2Fは灰色 `13` と黒 `0` のみを使う構成に変更した。
- 横壁は完全単色にし、縦ストリップ描画でちらつく細かい模様を廃止した。
- B3F-B4F / B5F-B10Fも同じ低情報量のタイルへ更新した。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` へ再取り込みした。
- B1F-B2F surfaceタイルが `0,13` または `13` のみで構成されることを確認した。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークが成功した。
