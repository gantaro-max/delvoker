---
Target Plan File: `docs/plan_phase5_traps.md`
---

# 1. Task Overview
ダンジョン探索の緊張感を高めるため、見えない罠（トラップ）を実装します。
1. 新しいタイル種別（Spike Trap, Poison Trap）の定義。
2. マップ生成時に部屋の中にランダムにトラップを配置するロジックの実装。
3. トラップを踏んだ際ダメージや状態異常が発生し、メッセージを表示する処理の実装。
4. トラップは一度発動すると通常の床に戻る「使い捨て」仕様とする。

# 2. Target Files
* `data.py`: トラップタイルの定数追加、マップ生成ロジック (`Map.generate_random`) の更新。
* `main.py`: ダンジョン更新ロジック (`_upd_dungeon`) へのトラップ判定追加、トラップ発動時のメッセージ処理。
* `docs/2. 仕様詳細.md`: 「12.1 トラップタイル仕様」の更新。
* `docs/4. 開発タスク.md`: Phase 5 「トラップと環境ギミックの実装」の更新。

# 3. Step-by-Step Instructions

## 3.1 タイル定数の追加 (`data.py`)
1.  以下の定数を定義する。
    - `TILE_TRAP_SPIKE = 4`
    - `TILE_TRAP_POISON = 5`

## 3.2 マップ生成ロジックの更新 (`data.py`)
1.  `Map.generate_random` メソッド内、通路の接続が終わった後にトラップを配置する。
2.  各部屋 (`rooms`) に対して、ランダムな数（例: 0〜2個）のトラップを配置する。
3.  **制約:** 階段 (`TILE_STAIRS`)、宝箱 (`TILE_CHEST`)、およびスタート地点（最初の部屋の中心）には配置しないこと。
4.  タイルが `TILE_FLOOR` である場所のみを書き換える。

## 3.3 トラップ発動ロジックの実装 (`main.py`)
1.  `_upd_dungeon` メソッドにて、プレイヤーが移動 (`moved = True`) した後、移動先のタイルを確認する。
2.  **Spike Trap (`TILE_TRAP_SPIKE`):**
    - プレイヤーに `5〜10` のランダムダメージを与える（HPは最小0）。
    - `town_sub_lines` に "Ouch! A spike trap!" とダメージ量を設定。
    - タイルを `TILE_FLOOR` に書き換える（`_dungeon_map.set_tile` を使用）。
    - `_dialog_return_state` を `STATE_DUNGEON` にし、`STATE_TOWN_SUB` に遷移。
3.  **Poison Trap (`TILE_TRAP_POISON`):**
    - プレイヤーの `status_effects["poison"]` を `3` に設定。
    - `town_sub_lines` に "Poison needles! You are poisoned." を設定。
    - タイルを `TILE_FLOOR` に書き換える。
    - 同様に `STATE_TOWN_SUB` に遷移。

## 3.4 ドキュメントの更新
1.  **`2. 仕様詳細.md`**: 「12.1 トラップタイル仕様」を「将来」から「実装済み」に更新。
2.  **`4. 開発タスク.md`**: Phase 5 の「トラップと環境ギミックの実装」を完了に更新。

# 4. Constraints
* **ASCII:** メッセージはすべて半角英数字と記号のみを使用すること。
* **UI:** トラップの通知には既存の `STATE_TOWN_SUB` (Windowフレームワーク) を流用する。
* **Minimap:** `draw_minimap` はトラップを通常の床（`COL_DARK_GRAY`）として描画し、踏むまで隠蔽すること。

# 5. Success Criteria
1. ダンジョンを歩いていると、一定確率でメッセージが表示され、ダメージや毒を受ける。
2. トラップを踏んだタイルが、ミニマップや内部データ上で通常の床に変化している。
3. スタート地点の目の前にトラップが配置されない。
4. `docs/` 内の仕様書と開発タスクが、トラップ実装完了の状態に更新されている。
5. トラップ発動時に `STATE_TOWN_SUB` のダイアログが表示され、Z/Xキーで探索に戻れる。