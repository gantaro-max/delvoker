# Implementation Plan: Phase 17 - Combat & UI Polish (Full)

## 1. Task Overview
UIのレイアウト不備（アクションメニューのはみ出し、装備表示の不足）を修正し、多対多戦闘の発生率と敵AIのターゲット分散ロジックを適正化します。

## 2. Target Files
- `/workspaces/games/main.py`
- `/workspaces/games/constants.py` (必要に応じてUI関連定数調整)
- `/workspaces/games/docs/3. 仕様詳細.md`
- `/workspaces/games/docs/4. 開発タスク.md`

## 3. Sub-Phases & Instructions

### Phase 17.1: UIレイアウトの修正
1. **ACTIONメニューの高さ調整:** `main.py` の `self.inv_action_win` の高さを現在の `56` から `72` へ拡大します。これにより、武具選択時に表示される 4 つのメニュー項目（Equip, Give to NPC, Drop, Cancel）とタイトルが枠内に収まるようにします。
2. **街のステータス画面に防具表示を追加:** `main.py` の `_draw_town` 内の `_status_content` 関数を修正し、武器 (`p.weapon.label()`) の表示の下に、防具 (`p.armor.label()` または "None") の情報を表示する行を追加します。
3. **ダンジョンのステータスバーに防具表示を追加:** `main.py` の `draw_status` 関数を修正し、武器名表示の横（または適切な位置）に装備中の防具名を表示する項目を追加します。
4. **インベントリ内での装備中防具の表示確認:** `main.py` の `_draw_inventory` 内で、`item is self.player.armor` が正しく判定され、装備中の防具も緑色（`COL_GREEN`）で表示されることを確認・修正します。

### Phase 17.2: 戦闘バランスの適正化
1. **多対多戦闘の発生ロジックの強化:** `main.py` の `_start_battle` 関数を修正します。
   - `enemy_key` が指定されていない場合（ランダムエンカウント時）に、以下のロジックで敵の出現数を決定します。
     - `self.dungeon_floor` が 1-2F の場合: 常に 1 体。
     - `self.dungeon_floor` が 3-5F の場合: 70% の確率で 1 体、30% の確率で 2 体。
     - `self.dungeon_floor` が 6F 以降の場合: 60% の確率で 1 体、30% の確率で 2 体、10% の確率で 3 体。
   - `_encounter_pool(self.dungeon_floor)` から敵をランダムに選択し、指定された数だけ `self.enemies` リストに追加します。
2. **敵 AI のターゲット分散:** `main.py` の `_get_enemy_target` 関数を修正します。
   - `ai_type == "normal"` の場合、現在の `alive[0]`（プレイヤー優先）ではなく、**`self.party.alive` リストからランダムにターゲットを選択**するように変更します。
   - これにより、敵の攻撃がプレイヤーだけでなく NPC メンバーにも分散されるようになります。

### Phase 17.3: ドキュメント同期
1. **仕様詳細の更新:** `docs/3. 仕様詳細.md` の以下のセクションを更新します。
   - 2.3 多対多戦闘フロー: 「敵の出現数決定ロジック」を追記し、階層に応じた出現確率を明記します。
   - 2.4 敵 AI 行動タイプ: `"normal"` AI のターゲットロジックを「生存しているパーティメンバーの中からランダムに選択」に更新します。
2. **タスクリストの更新:** `docs/4. 開発タスク.md` の Phase 16 を完了とし、Phase 17 を「進行中」として追加します。

## 4. Constraints
- **ASCII制約**: 全ての表示文字列はASCIIのみ。
- **Window枠の遵守**: テキストがウィンドウ枠からはみ出さないよう座標計算を行う。
- **ゲームバランス**: 敵のターゲット分散により、NPCの生存戦略が重要になるため、必要に応じてNPCのHPや防御力、回復アイテムのドロップ率などを微調整する可能性を考慮します。

## 5. Success Criteria
1. インベントリのアクションメニューが全て表示される。
2. 装備中の防具名がステータス画面で確認できる。
3. 複数敵との遭遇が発生し、敵がNPCを攻撃する。
4. `docs/4. 開発タスク.md` の Phase 17 が追加され、タスクが適切に記述されている。