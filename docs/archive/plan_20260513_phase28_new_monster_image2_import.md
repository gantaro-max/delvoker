# Implementation Plan: Phase 28 - New Monster Image 2.0 Import

## 1. Task Overview

Phase 27で追加した新規モンスター6体のImage 2.0生成PNGを、既存のPyxelリソース `assets.pyxres` に取り込む。

今回の主目的:
- `assets/source/image2/monsters/` に追加済みの新規モンスターPNGを `tools/convert_image2_assets.py` の `MONSTERS` 定義へ登録する。
- `data/enemies.json` の `sprite_u` / `sprite_v` と一致するBank 0座標へ32x32スプライトとして配置する。
- 壁テクスチャ、タイトル背景、エンディング背景を不用意に再取り込み・上書きしない。
- 戦闘画面と探索NPC描画で、新規モンスターが矩形フォールバックではなくスプライト表示される状態にする。

この指示書は実装前の設計・作業手順であり、完了後は `docs/archive/` へ移動する。

## 2. Target Files

- `/workspaces/games/tools/convert_image2_assets.py`
  - `MONSTERS` に新規6体のPNGファイル名とBank 0座標を追加する。
- `/workspaces/games/assets/source/image2/monsters/`
  - Image 2.0で作成済みのモンスターPNG置き場。
- `/workspaces/games/assets.pyxres`
  - 最終的なPyxelリソース。Bank 0へ新規6体を取り込む。
- `/workspaces/games/data/enemies.json`
  - 座標契約の確認対象。原則として今回は変更しない。
- `/workspaces/games/docs/3. 仕様詳細.md`
  - 実装後、必要に応じて新規モンスター画像取り込み仕様を同期する。
- `/workspaces/games/docs/4. 開発タスク.md`
  - Phase 28の作業結果を記録する。

## 3. Source Images

以下のPNGが存在することを確認する。

| 敵キー | ファイル名 |
| :--- | :--- |
| `kobold` | `monster_kobold.png` |
| `ooze` | `monster_ooze.png` |
| `cultist` | `monster_cultist.png` |
| `ice_hound` | `monster_ice_hound.png` |
| `dark_knight` | `monster_dark_knight.png` |
| `lich` | `monster_lich.png` |

配置先:

```
assets/source/image2/monsters/
```

## 4. Coordinate Contract

`data/enemies.json` の `sprite_u` / `sprite_v` と同じ座標を使用する。

| 敵キー | ファイル名 | Bank | sprite_u | sprite_v |
| :--- | :--- | :---: | :---: | :---: |
| `kobold` | `monster_kobold.png` | 0 | 128 | 32 |
| `ooze` | `monster_ooze.png` | 0 | 160 | 32 |
| `cultist` | `monster_cultist.png` | 0 | 192 | 32 |
| `ice_hound` | `monster_ice_hound.png` | 0 | 224 | 32 |
| `dark_knight` | `monster_dark_knight.png` | 0 | 0 | 96 |
| `lich` | `monster_lich.png` | 0 | 32 | 96 |

## 5. Implementation Steps

### Phase 28.1: Source Image Check

1. `assets/source/image2/monsters/` に新規6体のPNGが存在することを確認する。
2. ファイル名が `data/enemies.json` の敵キーと対応していることを確認する。
3. 画像の背景色は左上ピクセル色を透過色として扱うため、左上がクロマキー背景色であることを確認する。
4. モンスター本体に背景色と同じ色が混入していないか、可能な範囲で確認する。

### Phase 28.2: Conversion Script Update

1. `tools/convert_image2_assets.py` の `MONSTERS` リストに新規6体を追加する。
2. 追加位置は既存12体の後でよい。
3. 追加する定義:

```python
    ("monster_kobold.png", 128, 32),
    ("monster_ooze.png", 160, 32),
    ("monster_cultist.png", 192, 32),
    ("monster_ice_hound.png", 224, 32),
    ("monster_dark_knight.png", 0, 96),
    ("monster_lich.png", 32, 96),
```

4. `MONSTERS` 内で座標が重複していないことを確認する。
5. 既存モンスター12体の座標は変更しない。

### Phase 28.3: Monster-Only Import

1. 以下のコマンドでモンスターのみ取り込む。

```bash
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B tools/convert_image2_assets.py --monsters
```

2. `--all` は使用しない。
3. `--walls` / `--backgrounds` は使用しない。
4. 実行ログで新規6体が `[OK] monster ... -> (u,v)` として出力されることを確認する。
5. `assets.pyxres` が更新されることを確認する。

### Phase 28.4: Readback Verification

1. `assets.pyxres` をロードし、Bank 0の新規6座標に非0ピクセルが存在することを確認する。
2. 確認対象:
   - `(128, 32)` から32x32
   - `(160, 32)` から32x32
   - `(192, 32)` から32x32
   - `(224, 32)` から32x32
   - `(0, 96)` から32x32
   - `(32, 96)` から32x32
3. 透明色0だけの空タイルになっていないことを確認する。
4. 可能なら各タイルの使用色数も確認し、極端に1-2色しかない場合は元PNGを再確認する。

### Phase 28.5: Runtime Display Check

1. 新規敵を直接 `_start_battle(enemy_key)` できる簡易確認、または該当階層でのエンカウントにより戦闘画面を確認する。
2. 対象:
   - `kobold`
   - `ooze`
   - `cultist`
   - `ice_hound`
   - `dark_knight`
   - `lich`
3. 戦闘画面で矩形フォールバックではなく、モンスター画像が表示されることを確認する。
4. 黒背景で輪郭が読めることを確認する。
5. 左右反転表示時にも大きな位置ズレがないことを確認する。
6. 探索NPCとして出現した場合も、距離別スケールで画像が表示されることを確認する。

### Phase 28.6: Documentation Sync

1. `docs/3. 仕様詳細.md` の敵スプライト表に新規6体の座標を追記する。
2. `docs/4. 開発タスク.md` に Phase 28 を追加し、完了状態を記録する。
3. 実装・検証完了後、この指示書を `docs/archive/` へ移動する。

## 6. Pyxel Constraints

- Bank 0の画像領域は256x256。
- 各モンスターは32x32タイルとして扱う。
- 透過色は色番号0。
- Pyxel色は0-15のみ。
- `pyxel.blt(..., colkey=0)` により色0を透過する。
- `sprite_u` / `sprite_v` は32の倍数を基本とする。
- 既存座標を上書きしない。
- 新規座標は `data/enemies.json` と `tools/convert_image2_assets.py` で一致させる。

## 7. Acceptance Criteria

- `tools/convert_image2_assets.py` の `MONSTERS` に新規6体が追加されている。
- `assets.pyxres` Bank 0の指定座標に新規6体の32x32スプライトが存在する。
- `data/enemies.json` の `sprite_u` / `sprite_v` と取り込み座標が一致している。
- 戦闘画面で新規6体が矩形フォールバックではなく画像表示される。
- 探索NPC描画でも新規敵キーに対応した画像が表示される。
- 壁テクスチャ、タイトル背景、エンディング背景は今回の取り込みで変更しない。
- `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が同期されている。

## 8. Recommended Verification

1. JSON/コード確認:

```bash
python -B -m py_compile tools/convert_image2_assets.py main.py data.py
python -B -m json.tool data/enemies.json
```

2. モンスターのみ取り込み:

```bash
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B tools/convert_image2_assets.py --monsters
```

3. Bank 0読み戻し:

```bash
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B -c "import pyxel; pyxel.init(16,16,display_scale=1); pyxel.load('assets.pyxres'); coords=[(128,32),(160,32),(192,32),(224,32),(0,96),(32,96)]; print([(c, sum(1 for y in range(c[1], c[1]+32) for x in range(c[0], c[0]+32) if pyxel.images[0].pget(x,y)!=0)) for c in coords]); pyxel.quit()"
```

4. すべての新規座標で非0ピクセル数が0より大きいことを確認する。
