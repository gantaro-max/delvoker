# Phase 35: Surface Depth Shading

## 1. 背景

Phase 34で黒い格子・浮遊パネルの問題は改善したが、3Dビューの遠近感と空間表現がまだ分かりにくい。空間はより濃い色合いを基調にし、奥行きが読みやすい必要がある。

## 2. 目的

- B1F-B2Fの空間をより濃い灰色基調にする。
- 面ごとの模様は維持しつつ、白っぽさを抑える。
- 奥行きフレームごとに暗さを足し、遠近を読みやすくする。
- B3F-B4F / B5F-B10Fも階層色を維持しながら濃い空間にする。

## 3. 対象

- `tools/convert_image2_assets.py`
- `ui/renderer_3d.py`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. surfaceパターンの明色を減らし、B1F-B2Fは `13` と `5` を中心にする。
2. 中層は `5` と `1`、深層は `1` と `2` を中心にして暗さを維持する。
3. `ui/renderer_3d.py` に距離別の薄い暗色オーバーレイを追加する。
4. オーバーレイはフォールバック描画ではなく、`assets_loaded=True` のsurface描画時だけ適用する。
5. 3Dプレビューと描画スモークを確認する。

## 5. 受け入れ条件

- B1F-B2Fの可視surfaceに白 `7` を使わない。
- 奥へ行くほど暗くなり、近景・中景・遠景の区別が出る。
- B3F-B4F / B5F-B10Fの色分けを維持する。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` がクラッシュしない。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- B1F-B2Fの可視surfaceを `1,13` へ変更し、白 `7` を除外した。
- B3F-B4Fは `1,5`、B5F-B10Fは `1,2` として色分けを維持した。
- dither暗色オーバーレイは市松ノイズになるため撤回した。
- surface描画時の奥行きフレームと面境界線を黒 `0` にして、空間の箱形を読みやすくした。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` へ再取り込みした。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークとプレビュー保存が成功した。
