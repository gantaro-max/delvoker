# Implementation Plan: Dungeon Gimmicks & Exploration (Phase 8)

## 1. Task Overview
ダンジョン探索に「謎解き」と「利便性」の要素を追加します。鍵付きの扉とそれに対応するキーアイテム、およびフロア全体を可視化するアイテムを実装し、探索のモチベーションを高めます。

## 2. Target Files
- `/workspaces/games/data.py`: `TILE_LOCKED_DOOR = 7` の定義、`Map.generate_random` の修正。
- `/workspaces/games/main.py`: 扉とのインタラクション、地図の巻物の使用効果の実装。
- `/workspaces/games/data/items.json`: `dungeon_key`, `scroll_mapping` の追加。

## 3. Step-by-Step Instructions

### 3.1 タイルとデータの追加 (`data.py`)
- `TILE_LOCKED_DOOR = 7` を追加。
- `Map.generate_random`: 
    - 部屋をつなぐ通路の入り口に一定確率で `TILE_LOCKED_DOOR` を配置。
    - その階層のどこかの部屋（または宝箱）に `dungeon_key` が必ず配置されるように調整。

### 3.2 鍵付き扉の判定ロジック (`main.py`)
- `_upd_dungeon` 内で、移動先が `TILE_LOCKED_DOOR` の場合の処理を追加。
    - インベントリ内に `dungeon_key` があるかチェック。
    - あれば「Used Dungeon Key.」と表示し、扉を `TILE_FLOOR` に変更、キーを消費。
    - なければ「It's locked. Need a Dungeon Key.」と表示し、進行を阻害。

### 3.3 地図の巻物 (Scroll of Mapping) の実装 (`main.py`)
- `_do_use` において、アイテムが `scroll_mapping` だった場合の処理を追加。
    - `_dungeon_map.visited` の全要素を `True` に書き換える。
    - メッセージ「The entire floor map is revealed!」を表示。

### 3.4 隠し通路の導入 (Optional)
- 壁タイルの一部に、通行可能なフラグを持つ特殊な壁をランダムで配置する。

## 4. Document Updates
- `docs/2. 仕様詳細.md`: ダンジョンギミック（扉、地図）の項目を追加。
- `docs/4. 開発タスク.md`: Phase 8 を追加し、進捗を管理。

## 5. Constraints
- 鍵付き扉はミニマップ上で `COL_INDIGO (13)` 等で表示し、視認性を確保すること。
- テキストはすべて ASCII 文字を使用すること。

## 6. Success Criteria
1. ダンジョン内に鍵のかかった扉が出現し、鍵アイテムを持っていないと通れないこと。
2. 鍵を使用すると扉が消え、通行可能になること。
3. 「Scroll of Mapping」を使用すると、ミニマップの未訪問部分がすべて表示されること。