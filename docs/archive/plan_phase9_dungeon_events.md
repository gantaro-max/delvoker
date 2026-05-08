# Implementation Plan: Dungeon Interaction & Dynamic Events (Phase 9)

## 1. Task Overview
ダンジョン探索中にランダムで遭遇するインタラクティブなオブジェクト（癒しの泉）とNPC（放浪の商人）を実装します。これにより、探索継続の判断やリソース管理に深みを持たせます。

## 2. Target Files
- `/workspaces/games/data.py`: `TILE_FOUNTAIN = 8`, `TILE_MERCHANT = 9` の定義、`Map.generate_random` への配置ロジック追加。
- `/workspaces/games/main.py`: 泉のインタラクション（確率による効果分岐）、ダンジョン内ショップUIの構築。
- `/workspaces/games/data/items.json`: ダンジョン内商人が限定販売する新アイテム（例：全回復薬、一時強化薬）の追加。

## 3. Step-by-Step Instructions

### 3.1 タイルと生成ロジックの追加 (`data.py`)
- `TILE_FOUNTAIN = 8` (ミニマップ: COL_BLUE)
- `TILE_MERCHANT = 9` (ミニマップ: COL_GREEN)
- `Map.generate_random` にて、以下のルールで配置：
    - `TILE_FOUNTAIN`: 各階層のランダムな部屋に 50% の確率で 1 つ配置。
    - `TILE_MERCHANT`: B3F 以降、20% の確率で 1 つ配置。

### 3.2 癒しの泉のインタラクション (`main.py`)
- `_interact_fountain(nx, ny)` ヘルパーを作成：
    - **70% 成功**: HP/MPを最大値の30%回復。「Blessed water restores your strength.」
    - **20% 失敗**: 何も起きない。「The fountain is dry...」
    - **10% 罠**: 毒状態になる。「The water was tainted! You are poisoned.」
    - 使用後は `TILE_FLOOR` に変更。

### 3.3 放浪の商人の実装 (`main.py`)
- `_interact_merchant()` ヘルパーを作成：
    - `STATE_SHOP` をベースにしたダンジョン内専用のショップ画面を表示。
    - **重要**: 販売価格は通常の 1.5 倍に設定。
    - `items.json` に追加する「Elixir」や「Holy Scroll」など、街では手に入りにくいレア品をラインナップに含める。

### 3.4 入力処理の拡張 (`main.py`)
- `_upd_dungeon` において、`TILE_FOUNTAIN` または `TILE_MERCHANT` への移動（体当たり）を検出し、それぞれのインタラクション関数を呼び出す。

## 4. Document Updates
- `docs/2. 仕様詳細.md`: 14章「Dungeon Events」として泉と商人の詳細仕様を追記。
- `docs/4. 開発タスク.md`: Phase 9 を追加し、各項目にチェックを入れる。

## 5. Constraints
- テキストはすべて ASCII 文字（半角英数字・記号）を使用すること。
- ミニマップの色：泉 = `COL_BLUE (12)`、商人 = `COL_GREEN (11)`。
- 商人との取引中もダンジョンのステータス表示を維持し、没入感を削がないようにすること。

## 6. Success Criteria
1. ダンジョンを生成した際、稀に青い点（泉）や緑の点（商人）がミニマップに出現すること。
2. 泉を調べたとき、回復・不発・毒のいずれかが発生し、タイルが床に変わること。
3. 商人に話しかけた際、専用のラインナップと割増価格で買い物が可能であること。
4. 毒状態が泉で発生した場合、ステータス画面に反映され、継続ダメージが発生すること。