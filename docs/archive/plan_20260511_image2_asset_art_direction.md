# Implementation Plan: Image 2.0 Missing Asset Request Specification

## 1. Task Overview

Delvoker の見た目をリッチにするため、Image 2.0 等の画像生成AIへ再依頼する未実装アセットの制作仕様と、受領した画像を `assets.pyxres` へ取り込む実装手順を定義する。

この指示書の目的:
- 未実装のモンスター2体、壁テクスチャ3種、タイトル背景、エンディング背景の制作依頼条件を明確にする。
- Image 2.0 の出力をそのまま使わず、Pyxel標準16色・指定Bank・指定座標へ変換する前提を固定する。
- 既存の `assets.pyxres` Bank 0/1/2 構成を壊さず、差し替え可能な素材管理フローを作る。
- 既に作成済みのモンスター10体は再依頼・再生成しない。

今回依頼する素材:
- `monster_dungeon_master.png`
- `monster_archdemon.png`
- `wall_b1_b2.png`
- `wall_b3_b4.png`
- `wall_b5_plus.png`
- `background_title.png`
- `background_ending.png`

今回依頼しない素材:
- `monster_slime.png`
- `monster_bat.png`
- `monster_skeleton.png`
- `monster_goblin.png`
- `monster_orc_chief.png`
- `monster_revenant.png`
- `monster_wraith.png`
- `monster_golem.png`
- `monster_mimic.png`
- `monster_wyvern.png`

## 2. Current Runtime Asset Contract

現行コードが参照している `assets.pyxres` の構成は以下。

| Image Bank | 用途 | サイズ / 配置 |
| :---: | :--- | :--- |
| Bank 0 | モンスター、探索NPC、壁テクスチャ | モンスター: 32×32、壁: 8×8 |
| Bank 1 | タイトル背景 | 256×256 全画面 |
| Bank 2 | エンディング背景 | 256×256 全画面 |

### Bank 0: Monster Sprite Layout

今回の再依頼対象は `monster_dungeon_master.png` と `monster_archdemon.png` の2体のみ。以下の表は参照用として残す。

| 座標 `(U,V)` | ファイル名 | 表示名 |
| :---: | :--- | :--- |
| `(0,0)` | `monster_slime.png` | Slime |
| `(32,0)` | `monster_bat.png` | Bat |
| `(64,0)` | `monster_skeleton.png` | Skeleton |
| `(96,0)` | `monster_goblin.png` | Goblin |
| `(128,0)` | `monster_orc_chief.png` | Orc Chief |
| `(160,0)` | `monster_revenant.png` | Revenant |
| `(192,0)` | `monster_wraith.png` | Wraith |
| `(224,0)` | `monster_golem.png` | Golem |
| `(0,32)` | `monster_mimic.png` | Mimic |
| `(32,32)` | `monster_wyvern.png` | Wyvern |
| `(64,32)` | `monster_dungeon_master.png` | Dungeon Master |
| `(96,32)` | `monster_archdemon.png` | Archdemon |

### Bank 0: Wall Tile Layout

| 座標 `(U,V)` | ファイル名 | 用途 |
| :---: | :--- | :--- |
| `(0,64)` | `wall_b1_b2.png` | B1F-B2F |
| `(8,64)` | `wall_b3_b4.png` | B3F-B4F |
| `(16,64)` | `wall_b5_plus.png` | B5F以降 |

### Bank 1 / 2 Backgrounds

| Bank | ファイル名 | 用途 |
| :---: | :--- | :--- |
| 1 | `background_title.png` | タイトル画面 |
| 2 | `background_ending.png` | エンディング画面 |

## 3. Source File Delivery Format

Image 2.0 への依頼では、`.pyxres` ではなく PNG を納品対象とする。

### Required Deliverables

| 種別 | 推奨生成サイズ | 最終変換サイズ | 背景 |
| :--- | :---: | :---: | :--- |
| 個別モンスター2体 | 512×512 PNG | 32×32 | 透明、または完全な単色 #00ff00 |
| 壁テクスチャ | 512×512 PNG | 8×8 | 不透明でよい |
| タイトル背景 | 1024×1024 PNG | 256×256 | 不透明 |
| エンディング背景 | 1024×1024 PNG | 256×256 | 不透明 |

### File Naming

受領画像は以下へ保存する想定。

```
assets/source/image2/
  monsters/
    monster_dungeon_master.png
    monster_archdemon.png
  walls/
    wall_b1_b2.png
    wall_b3_b4.png
    wall_b5_plus.png
  backgrounds/
    background_title.png
    background_ending.png
```

## 4. Global Art Constraints for Image 2.0

すべての依頼に共通する制約:

- No text, no letters, no numbers, no logo, no watermark.
- No UI frame, no menu elements, no captions.
- Retro dark fantasy dungeon RPG style.
- Strong silhouette and high contrast.
- Readable after reduction to Pyxel 16 colors.
- Avoid photorealism for monsters; use illustrated pixel-art-friendly forms.
- Avoid pure black inside important subject details because Pyxel color index 0 is transparent for sprites.
- Use dark gray, navy, purple, or brown instead of true black for visible dark regions.
- Keep the subject centered with padding.
- Do not crop wings, horns, weapons, or silhouettes.
- Avoid soft glows that become muddy after 16-color reduction.
- Avoid tiny details that disappear at 32×32 or 8×8.

## 5. Monster Art Direction

### Monster Generation Requirements

各モンスターは個別PNGとして生成する。AIにスプライトシートを直接作らせない。

理由:
- 生成AIは厳密な32×32グリッドや座標配置を崩しやすい。
- 個別画像をこちらで32×32へ縮小・減色・Bank 0へ配置する方が安全。

各依頼に必ず含める条件:

```text
Create one centered full-body monster sprite concept for a retro dark fantasy dungeon RPG.
The final image will be reduced to a 32x32 Pyxel sprite, so use a bold readable silhouette, simple shapes, and high contrast.
Use a perfectly flat solid #00ff00 chroma-key background.
Do not use #00ff00 anywhere in the monster.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No cast shadow, no floor plane, no background scenery.
Keep the entire creature inside the image with generous padding.
```

### Monster-Specific Prompts

今回の再依頼では以下2体のみを生成する。その他10体は生成済みのため、Image 2.0 へ再依頼しない。

| ファイル | Subject Prompt |
| :--- | :--- |
| `monster_dungeon_master.png` | Robed dungeon master wizard boss, staff, hood, arcane menace, readable human-like silhouette. |
| `monster_archdemon.png` | Final boss archdemon, horns, wings, claws, powerful demon silhouette, not too detailed. |

### Dungeon Master Full Prompt

Use this prompt for `monster_dungeon_master.png`.

```text
Create one centered full-body monster sprite concept for a retro dark fantasy dungeon RPG.
Subject: Dungeon Master, a robed dungeon wizard boss with a hooded face, staff, arcane menace, and a readable human-like silhouette.
The design should feel like a mid-boss or dungeon ruler, mysterious and dangerous, but still simple enough to read at 32x32.
Use bold shapes: robe, hood, staff, glowing eyes, one clear magical accent.
The final image will be reduced to a 32x32 Pyxel sprite.
Use a perfectly flat solid #00ff00 chroma-key background.
Do not use #00ff00 anywhere in the monster.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No cast shadow, no floor plane, no background scenery.
Keep the entire creature inside the image with generous padding.
Avoid pure black in important visible body details because Pyxel color index 0 is transparent.
Retro dark fantasy dungeon RPG style, high contrast, painterly pixel-art-friendly illustration.
```

### Archdemon Full Prompt

Use this prompt for `monster_archdemon.png`.

```text
Create one centered full-body monster sprite concept for a retro dark fantasy dungeon RPG.
Subject: Archdemon, the final boss, with huge horns, wings, claws, a powerful demonic torso, and a terrifying readable silhouette.
The design should feel massive and final-boss-like, but still simple enough to read at 32x32.
Use bold shapes: horns, wings, claws, glowing eyes, broad shoulders.
The final image will be reduced to a 32x32 Pyxel sprite.
Use a perfectly flat solid #00ff00 chroma-key background.
Do not use #00ff00 anywhere in the monster.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No cast shadow, no floor plane, no background scenery.
Keep the entire creature inside the image with generous padding.
Avoid pure black in important visible body details because Pyxel color index 0 is transparent.
Retro dark fantasy dungeon RPG style, high contrast, painterly pixel-art-friendly illustration.
```

## 6. Wall Texture Art Direction

壁テクスチャは 8×8 に縮小されるため、写実的な壁画像より「パターンの方向性」が重要。

共通依頼条件:

```text
Create a seamless square dungeon wall texture for a retro dark fantasy RPG.
It will be reduced to an 8x8 Pyxel tile, so use large readable stone patterns and high contrast.
No text, no symbols, no creatures, no objects, no lighting gradients, no perspective.
The texture must tile seamlessly on all edges.
```

| ファイル | Subject Prompt |
| :--- | :--- |
| `wall_b1_b2.png` | Bright stone brick dungeon wall, clean early-floor masonry, slightly worn. |
| `wall_b3_b4.png` | Damp mossy stone wall, deeper dungeon, wet cracks, green moss accents. |
| `wall_b5_plus.png` | Dark ominous black marble and bone-like dungeon wall, final depths, cursed atmosphere. |

Use these prompts for the three wall files.

```text
Create a seamless square dungeon wall texture for a retro dark fantasy RPG.
Subject: bright early-floor stone brick wall, clean but slightly worn masonry, readable block pattern.
The final image will be reduced to an 8x8 Pyxel tile, so use large simple stone shapes and strong contrast.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No creatures, no objects, no symbols, no perspective.
No dramatic lighting gradients.
The texture must tile seamlessly on all edges.
```

```text
Create a seamless square dungeon wall texture for a retro dark fantasy RPG.
Subject: damp mossy deeper-dungeon stone wall, wet cracks, green moss accents, darker and older than the first-floor wall.
The final image will be reduced to an 8x8 Pyxel tile, so use large simple stone shapes and strong contrast.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No creatures, no objects, no symbols, no perspective.
No dramatic lighting gradients.
The texture must tile seamlessly on all edges.
```

```text
Create a seamless square dungeon wall texture for a retro dark fantasy RPG.
Subject: dark ominous final-depth wall made of black marble, bone-like veins, cursed stone, and subtle demonic atmosphere.
The final image will be reduced to an 8x8 Pyxel tile, so use large simple patterns and strong contrast.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No creatures, no objects, no symbols, no perspective.
No dramatic lighting gradients.
The texture must tile seamlessly on all edges.
```

## 7. Background Art Direction

背景は最終的に 256×256 で描画される。タイトル文字やメニュー文字はゲーム側で描くため、画像内に文字を入れない。

### Title Background

File: `background_title.png`

Art direction:
- The title background should depict a dungeon city, not only a dungeon doorway.
- Show a fortified underground or cliffside city built around a massive dungeon entrance.
- Include stacked stone buildings, bridges, stairs, market-like silhouettes, watchtowers, and torchlit streets.
- The city should feel like the player's home base at the edge of the abyss: inhabited, dangerous, and adventurous.
- Keep the central horizontal band calm enough for `D E L V O K E R`, menu options, and name input text overlays.

Prompt:

```text
Create a square 1024x1024 background illustration for the title screen of a retro dark fantasy dungeon RPG named Delvoker.
Show a dungeon city: a fortified underground or cliffside settlement built around a massive dungeon entrance, with stacked stone buildings, bridges, stairs, watchtowers, torchlit streets, and old masonry descending into darkness.
The city should feel inhabited, dangerous, and adventurous, like a home base at the edge of the abyss.
Leave the central horizontal area visually calm enough for menu text overlay.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No signs with readable writing.
High contrast, readable composition, suitable for reduction to a 256x256 Pyxel 16-color background.
Avoid photorealism; use painterly pixel-art-friendly illustration.
```

### Ending Background

File: `background_ending.png`

Prompt:

```text
Create a square 1024x1024 ending screen background illustration for a retro dark fantasy dungeon RPG.
Show dawn light over a conquered dungeon city and a sealed ruined demon gate, peaceful but heroic mood, treasure glints, distant mountains or sky, and signs that the danger has passed.
Leave the central area visually calm enough for ending text overlay.
No text, no letters, no numbers, no logo, no watermark, no UI, no frame.
No signs with readable writing.
High contrast, readable composition, suitable for reduction to a 256x256 Pyxel 16-color background.
Avoid photorealism; use painterly pixel-art-friendly illustration.
```

## 8. Conversion Requirements

受領後、以下の変換を行う。

1. PNGを読み込む。
2. モンスターは #00ff00 背景を透明扱いにする。
3. `monster_dungeon_master.png` と `monster_archdemon.png` を32×32へ縮小する。
4. 壁テクスチャ3枚を8×8へ縮小する。
5. 背景2枚を256×256へ縮小する。
6. Pyxel標準16色へ最近色で減色する。
7. スプライト背景はカラーインデックス0にする。
8. Bank 0/1/2 の指定座標へ配置する。
9. 既に取り込み済みのモンスター10体を壊さない。
10. `assets.pyxres` として保存する。

### Pyxel Palette Constraint

最終的に使用できる色はPyxel標準16色のみ。

| Index | 用途メモ |
| :---: | :--- |
| 0 | 黒 / スプライト透過色 |
| 1-15 | 可視色 |

重要:
- モンスタースプライトの背景は必ず index 0。
- モンスター本体の重要な輪郭に index 0 を多用しない。
- 戦闘画面・探索画面とも黒背景が多いため、輪郭には 5/6/7/13 などの明るめ色を残す。

## 9. Import Implementation Plan

### Phase 25.1: Source Asset Intake

1. `assets/source/image2/` 配下を作成する。
2. Image 2.0 から受領した未実装7ファイルを、3章の命名規則通りに配置する。
3. `monster_dungeon_master.png` / `monster_archdemon.png` / 壁3種 / 背景2種が揃っているか確認する。
4. 生成済みモンスター10体は再生成・上書きしない。

### Phase 25.2: Conversion Script

1. `tools/convert_image2_assets.py` を作成する。
2. PIL/Pillow が利用可能なら使用する。未導入なら導入せず、使用可能な標準/既存環境で対応する。
3. Pyxel標準パレットへの最近色変換を実装する。
4. 各PNGを指定サイズへリサイズし、`pyxel.images[bank].pset()` で配置する。
5. 既存 Bank 0/1/2 のうち、未実装7素材の配置領域だけを更新し、他のモンスター領域は触らない。
6. 変換後に `assets.pyxres` を保存する。

### Phase 25.3: Runtime Verification

1. `python -B -m py_compile main.py npc.py constants.py systems/persistence.py ui/renderer_3d.py`
2. Pyxelで `assets.pyxres` をロードし、Bank 0/1/2 の代表ピクセルを確認する。
3. 戦闘画面で全モンスターが表示されることを確認する。
4. ダンジョン探索画面でNPCスプライトが距離別表示されることを確認する。
5. B1F-B2F、B3F-B4F、B5F以降で壁テクスチャが切り替わることを確認する。
6. タイトル・名前入力・エンディング画面で背景とテキストが干渉しないことを確認する。

### Phase 25.4: Documentation Sync

1. `docs/3. 仕様詳細.md` に Image 2.0 素材取り込み仕様を追記する。
2. `docs/4. 開発タスク.md` に Phase 25 完了チェックを追加する。
3. 完了後、この指示書を `docs/archive/` へ移動する。

## 10. Acceptance Criteria

- 受領PNGが命名規則通りに配置されている。
- `assets.pyxres` の Bank 0/1/2 が既存コードの参照座標と一致している。
- `monster_dungeon_master.png` と `monster_archdemon.png` は32×32でも種類が判別できる。
- 壁テクスチャは8×8タイルとして繰り返しても破綻しない。
- タイトル背景は「ダンジョン都市」として読める。
- エンディング背景は「危機が去った後のダンジョン都市/魔門」として読める。
- タイトル・エンディング背景に文字やロゴが含まれない。
- タイトル・名前入力・エンディングのゲーム内テキストが読める。
- `assets.pyxres` 未ロード時のフォールバック動作は壊れていない。

## 11. Notes for Image 2.0 Requester

- 「画像内に Delvoker の文字を入れる」依頼はしない。タイトル文字はゲーム側で描く。
- 「スプライトシートを作る」依頼は避ける。モンスターは個別PNGで依頼する。
- 今回再依頼するモンスターは `monster_dungeon_master.png` と `monster_archdemon.png` のみ。
- 「完全なピクセルアート32×32」をAIへ直接要求しすぎない。高解像度の読みやすい形を作り、ローカルで32×32へ変換する。
- 生成結果が暗すぎる場合は、輪郭と顔だけ明るくする再依頼を行う。
- 細部が多すぎる場合は、形を単純化する再依頼を行う。
