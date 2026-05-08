# Implementation Plan: Grave Recovery System

## 1. Task Overview
プレイヤーが全滅した際、ロストしたアイテムをその場に「遺品（Grave）」として残します。次回の探索でその場所に到達し、守護者（Revenant）との戦闘に勝利することでアイテムを回収できる仕組みを構築します。

## 2. Target Files
- `/workspaces/games/data.py`: 定数定義、`Grave`クラスの追加、マップ生成ロジックの拡張。
- `/workspaces/games/main.py`: 全滅時のデータ退避、遺品タイルの判定、回収バトルの制御。
- `/workspaces/games/data/enemies.json`: 守護者「Revenant」のデータ定義。

## 3. Step-by-Step Instructions

### 3.1 データ構造の整備 (`data.py`)
- `TILE_GRAVE = 6` を追加。
- `Grave` クラスを定義。属性として `floor`, `x`, `y`, `item` (Itemオブジェクト) を持つ。
- `Map.generate_random` メソッドを修正。引数に `grave=None`, `current_floor=1` を追加し、条件が一致する場合に指定座標のタイルを `TILE_GRAVE` に書き換える処理を末尾に追加。

### 3.2 状態保持と初期化 (`main.py`)
- `App.__init__` で `self.grave = None` および回収バトル中かを示す `self.is_grave_battle = False` を初期化。
- `_enter_dungeon_fresh` および `_next_floor` で `Map.generate_random` を呼ぶ際、現在の遺品データとフロア数を渡すように修正。

### 3.3 全滅時の処理変更 (`main.py`)
- `_calc_item_loss()` を修正し、名前だけでなくロストした **Itemオブジェクト自体** を返すように変更。
- `_enemy_turn` 内の全滅判定時、`_calc_item_loss` から受け取ったオブジェクトを `self.grave` に保存する（既存の `lost_item_name` 表示ロジックと併存させる）。

### 3.4 遺品タイルの接触イベント (`main.py`)
- `_upd_dungeon` で移動後のタイルが `TILE_GRAVE` だった場合の処理を追加。
    - メッセージ「You found your previous remains. A vengeful spirit appears!」を表示。
    - `self.is_grave_battle = True` を設定。
    - `self._start_battle("revenant")` を実行。

### 3.5 戦闘勝利とアイテム復元 (`main.py`)
- `_handle_victory` を修正。
    - `self.is_grave_battle` が True の場合、`self.grave.item` をインベントリに戻す。
    - インベントリが満杯の場合は、ドロップしたメッセージを表示するか、足元に置く処理を検討（今回は簡易的に「戻した」と表示し、ロジックを優先）。
    - 勝利後、`self.grave = None`, `self.is_grave_battle = False` とし、マップ上のタイルを `TILE_FLOOR` に戻す。

### 3.6 守護者データ (`data/enemies.json`)
- `revenant` を追加。
    - HP: 40程度, DEF: 2, 弱点: `holy`, AI: `normal`。

## 4. Document Updates
以下の仕様書を実装内容に合わせて Claude Code に更新させてください。
- `docs/1. 機能要件.md`: 「9. ロスト品回収」のステータスを更新。
- `docs/2. 仕様詳細.md`: 12.2節「Grave System」として仕様を追記。
- `docs/3. データ構造.md`: `Grave` クラスの定義を追記。
- `docs/4. 開発タスク.md`: 「遺品回収イベントの実装」の各項目を完了（x）にする。

## 5. Constraints
- メッセージはすべて ASCII 文字（半角英数字・記号）を使用すること。
- ミニマップ上での遺品タイルは `COL_PINK (14)` で描画すること。

## 6. Success Criteria
1. アイテムを所持した状態で全滅し、`self.grave` に正しい座標とアイテムが保持される。
2. 次の探索で同じ階層・座標に移動した際、ミニマップにピンクの点が表示され、移動すると戦闘が開始される。
3. 戦闘に勝利すると、ロストしたはずのアイテムがインベントリに復元される。
4. アイテム回収後、墓石タイルがマップから消去される。