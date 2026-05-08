# Implementation Plan: Home Upgrades & Warehouse

## 1. Task Overview
プレイヤーの拠点（Home）を強化するシステムを導入します。溜めたゴールドを使い、持ちきれないアイテムを保管する「倉庫（Warehouse）」の利用・拡張、およびプレイヤーの基礎能力を底上げする「永続強化」を可能にします。

## 2. Target Files
- `/workspaces/games/main.py`: `STATE_HOME` の追加、倉庫UIの実装、拠点メニューのロジック。
- `/workspaces/games/data.py`: `Player` クラスへの永続強化フラグや倉庫データの保持。

## 3. Step-by-Step Instructions

### 3.1 データの拡張 (`data.py`)
- `Player` クラスに以下を追加：
    - `self.warehouse = []`: アイテム保管用リスト。
    - `self.warehouse_max = 10`: 倉庫の初期最大容量。
    - `self.perm_stats = {"str": 0, "def": 0, "mag": 0}`: 投資による永続上昇値の記録。

### 3.2 拠点状態の追加 (`main.py`)
- `STATE_HOME = 15` を定義。
- `TOWN_MENU` に `"Home"` を追加。
- `_upd_town` 内の分岐に `Home` を選択した際の `_set_state(STATE_HOME)` を追加。

### 3.3 拠点メニューと倉庫UIの実装 (`main.py`)
- `_upd_home` / `_draw_home` を作成し、以下のサブメニューを提供：
    - **Warehouse**: プレイヤーの `inventory` と `warehouse` の間でアイテムを移動するUI。
    - **Renovate**: ゴールドを消費して `warehouse_max` を増加させる（例: 5段階、1段階ごとに+5枠、費用増加）。
    - **Training**: ゴールドを消費して `perm_stats` を上昇させる（高額に設定：1000G, 2000G...）。
- 倉庫UIは、`Window` クラスを再利用し、左右に「手持ち」と「倉庫」を並べて表示、または切り替えて操作する形式とする。

### 3.4 永続強化の反映 (`main.py`)
- `Player` の攻撃力や防御力の計算ロジックに `self.perm_stats` を加算するように修正。

## 4. Document Updates
- `docs/1. 機能要件.md`: 「拠点（マイホーム）の永続強化」を実装済みに更新。
- `docs/2. 仕様詳細.md`: 倉庫の仕様、投資による強化率、倉庫拡張費用などのテーブルを追記。
- `docs/4. 開発タスク.md`: 該当タスクにチェックを入れる。

## 5. Constraints
- 全てのテキストは ASCII 文字のみを使用すること。
- 倉庫からのアイテム移動時に、受け取り側の最大容量を必ずチェックすること。
- UIのレイアウトは Pyxel の 256x256 画面内に収まるように調整すること（既存の Window クラスを活用）。

## 6. Success Criteria
1. 町のメニューから「Home」を選択し、拠点画面に遷移できること。
2. 倉庫にアイテムを預け、次回の探索後に取り出せること。
3. ゴールドを消費して倉庫の最大容量（`warehouse_max`）が増えること。
4. ステータス強化後、戦闘時やステータス画面でその効果が反映されていること。