# Phase 31: 3D Surface Readability Fix

## 1. 背景

Phase 29-30で導入した3Dビューsurface素材について、B1F時点で赤みが強く、ちらつく千鳥格子状に見えて可読性が大きく損なわれている。

構造としては前方・左右壁の奥行き表現は成立しているため、描画ジオメトリではなくsurface素材の配色・パターン密度を修正対象とする。

## 2. 目的

- B1F-B2Fをニュートラルな石壁色へ戻す。
- 高コントラストな市松/千鳥格子に見えるパターンを避ける。
- 横壁・前方壁・床・天井・奥面の面差は維持する。
- Pyxel色番号0-15のみを使い、ゲーム内ASCII制約に影響を出さない。

## 3. 対象

- `assets/source/image2/surfaces/*.png`
- `assets.pyxres`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

## 4. 実装方針

1. surface PNGを低ノイズの8x8タイル設計から再生成する。
2. B1F-B2Fは赤/ピンク系を使わず、暗青・石灰・淡青灰の低コントラスト配色にする。
3. B3F-B4FとB5F-B10Fも同じ密度ルールに合わせ、ちらつきやすい交互配置を避ける。
4. `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` に再取り込みする。
5. 3Dビュー描画スモークと静的制約を確認する。

## 5. 受け入れ条件

- B1F-B2F surfaceタイルに赤系色（Pyxel 8/14/15）を使わない。
- どのsurfaceタイルも1px交互の市松模様を主パターンにしない。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1)` がクラッシュしない。
- `tools/convert_image2_assets.py --surfaces` が成功する。
- 実装後、マスター仕様と開発タスクを同期し、この指示書を `docs/archive/` へ移動する。

## 6. Execution Result

Status: Completed.

- `assets/source/image2/surfaces/*.png` を低ノイズの8x8タイル設計から再生成した。
- B1F-B2Fは赤系・ピンク系を除外し、石壁色へ変更した。
- B3F-B4F / B5F-B10Fも同じ密度方針で再生成した。
- `tools/convert_image2_assets.py --surfaces` で `assets.pyxres` へ再取り込みした。
- B1F-B2F surfaceタイルに Pyxel色 `8,14,15` が含まれないことを確認した。
- `draw_3d_view(..., assets_loaded=True, dungeon_floor=1/3/5)` の描画スモークが成功した。
