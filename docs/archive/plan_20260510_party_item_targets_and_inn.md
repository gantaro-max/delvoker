# Implementation Plan: Phase 21 - Party Item Targeting & Inn Party Recovery

## 1. Task Overview
消費アイテムの使用対象をプレイヤー固定からパーティメンバー選択式へ拡張します。あわせて、宿屋の回復処理をプレイヤー単体からパーティ全体へ変更し、Porter + NPC パーティ運用に合う回復導線へ整えます。

主目的:
- Potion / Ether / Antidote 等を NPC にも使用できるようにする。
- 使用対象選択UIを追加し、満タン・戦闘不能・状態異常なし等の無効対象を判定する。
- 宿屋は生存メンバー全員の HP/MP を回復し、Revive の役割を維持する。
- 回復SE / ポップアップを対象メンバーに対応させる。

## 2. Target Files
- `/workspaces/games/constants.py`: `STATE_INV_TARGET_SELECT` 定数の追加。
- `/workspaces/games/main.py`: 宿屋処理、インベントリ使用フロー、対象選択 update/draw、`_do_use(item, target)` への変更。
- `/workspaces/games/docs/3. 仕様詳細.md`: アイテム対象選択と宿屋仕様を追記。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 21 のタスクと完了チェックを追加。

## 3. Sub-Phases & Instructions

### Phase 21.1: 宿屋のパーティ回復化
1. **推奨仕様採用**: 宿屋は `self.party.members` のうち `hp > 0` の生存メンバーだけを回復する。
   - HP=0 の戦闘不能メンバーは回復しない。
   - 戦闘不能メンバーは既存 `Revive` メニューで蘇生する役割分担を維持する。
2. **`_upd_town` 修正**: `sel == "Inn"` の処理を以下に変更する。
   - `for member in self.party.members:`
   - `if member.hp > 0: member.hp = member.max_hp; member.mp = member.max_mp`
3. **メッセージ更新**:
   - 例: `"The party's HP and MP are fully restored."`
   - 戦闘不能者がいる場合は追加で `"Fallen members need Revive."` を表示してもよい。
4. **状態異常の扱い**:
   - 今回はHP/MP回復のみ。毒/スタンを宿屋で治療するかは追加仕様扱い。
   - 現状の硬派寄りバランスを維持するなら状態異常は消さない。

### Phase 21.2: インベントリ対象選択ステート追加
1. **状態定数追加**: `constants.py` に `STATE_INV_TARGET_SELECT = 24` を追加する。
   - 既存 `STATE_LOG_VIEW = 23` の次番号。
2. **import / 分岐追加**: `main.py` の constants import、`update()`、`draw()`、`_set_state()` に新ステートを追加する。
3. **Appフィールド追加**:
   - `self.inv_target_idx = 0`
   - `self.pending_use_item = None`
4. **対象候補ヘルパー**:
   - `_item_targets(item)` を追加し、`self.party.members` を返す。
   - 基本は Player / NPC1 / NPC2 の現在パーティメンバー全員。
5. **使用可否ヘルパー**:
   - `_can_use_item_on(item, target)` を追加する。
   - HP回復: `target.hp > 0 and target.hp < target.max_hp`
   - MP回復: `target.hp > 0 and target.mp < target.max_mp`
   - 状態治療: `target.hp > 0 and target.status_effects[cure_status] > 0`
   - 複数効果アイテムは、どれか1つでも有効なら使用可。
   - 戦闘不能 (`hp <= 0`) には通常消費アイテムを使用不可。蘇生アイテムを将来追加する場合は別判定にする。
6. **対象不要アイテムの整理**:
   - `Scroll: Mapping` は従来通り対象選択なしで即使用。
   - `GrimoireItem` はプレイヤーがスキルを覚えるアイテムなので対象選択なしで即使用。
   - Potion / Ether / Antidote / Elixir 等は対象選択へ遷移する。

### Phase 21.3: 使用フロー変更
1. **`_upd_inv_action` 修正**:
   - `sel == "Use"` のとき、対象不要アイテムなら `_do_use(item, self.player)` を呼ぶ。
   - 対象選択が必要な消費アイテムなら:
     - `self.pending_use_item = item`
     - `self.inv_target_idx = 0`
     - `_set_state(STATE_INV_TARGET_SELECT)`
     - return
2. **`_upd_inv_target_select` 追加**:
   - X: `STATE_INV_ACTION` に戻る。
   - Up/Down: 対象カーソル移動。
   - Z/Space: `_can_use_item_on(item, target)` が True なら `_do_use(item, target)` を実行し、`STATE_INVENTORY` へ戻る。
   - 無効対象なら何もしないか、短いダイアログ `"No effect."` を表示する。
3. **インデックス安全性**:
   - 使用後にアイテムが消えるため、`inv_idx` は現在のバッグ長に合わせて clamp する。
   - `pending_use_item` は使用完了またはキャンセル後に `None` へ戻す。

### Phase 21.4: `_do_use(item, target)` への抽象化
1. **シグネチャ変更**: `_do_use(self, item)` を `_do_use(self, item, target=None)` に変更する。
   - `target is None` の場合は後方互換として `self.player` を使う。
2. **適用対象変更**:
   - HP/MP回復、状態異常治療は `target` に対して行う。
   - グリモア習得は引き続き `self.player` に対して行う。
   - Mapping Scroll はダンジョンマップに対して行うため target 不要。
3. **消費判定**:
   - `_can_use_item_on` で無効対象を弾くため、`_do_use` 側では有効効果を適用してからアイテムを削除する。
   - 万一効果ゼロならアイテムを消費しない設計でもよい。
4. **SE / ポップアップ**:
   - HP回復または状態治療が発生したら `pyxel.play(2, 2)`。
   - ポップアップ座標は `_party_card_popup_pos(target)` のようなヘルパーで対象カード位置に合わせる。
   - 例: プレイヤー index 0 → 左カード、NPC1 index 1 → 中央カード、NPC2 index 2 → 右カード。
   - 町/インベントリ画面中はHUDカードが見えない場合があるため、最低限カード想定座標または対象名付きダイアログでも可。

### Phase 21.5: ターゲット選択UI
1. **描画追加**: `_draw_inventory()` 内に `if self.state == STATE_INV_TARGET_SELECT:` ブロックを追加する。
2. **表示内容**:
   - タイトル: `Use Item`
   - アイテム名: `Potion` など
   - 対象リスト: `> Hero HP:10/20 MP:4/8`
   - NPCも同様に表示。
   - 無効対象は `COL_DARK_GRAY`、有効対象は通常色、カーソル対象は `COL_YELLOW`。
3. **操作ガイド**:
   - `"Z:Use  X:Cancel"`
4. **ウィンドウ**:
   - 既存 `sub_win` を流用してよい。
   - `_set_state(STATE_INV_TARGET_SELECT)` で `sub_win.open()`、戻るときは適切に閉じる。

### Phase 21.6: ドキュメント同期
1. **仕様詳細更新**: `docs/3. 仕様詳細.md` に以下を追記する。
   - `STATE_INV_TARGET_SELECT`
   - 消費アイテム対象選択フロー
   - `_can_use_item_on` の判定表
   - 宿屋は生存メンバーのみ回復し、戦闘不能は Revive 管轄
2. **開発タスク更新**: `docs/4. 開発タスク.md` に Phase 21 を追加する。
3. **完了処理**: 実装と確認が完了したら、この指示書を `docs/archive/` に移動する。

## 4. Constraints
- **ASCII制約**: ゲーム内表示文字列はすべてASCIIにする。
- **Reviveの役割維持**: 宿屋と通常消費アイテムで HP=0 を復活させない。
- **対象不要アイテム維持**: Mapping Scroll と Grimoire は無駄に対象選択を挟まない。
- **無効使用防止**: HP/MP満タン、治療対象なし、戦闘不能など、効果がない対象にはアイテムを消費しない。
- **既存UIとの整合**: `STATE_INV_ACTION` / `STATE_INV_GIVE_NPC` の既存フローを壊さない。
- **ポップアップ安全性**: 対象カード座標が取れない場合でもクラッシュしない。

## 5. Success Criteria
1. 宿屋利用時、生存中の Player / NPC 全員の HP/MP が最大まで回復する。
2. HP=0 のメンバーは宿屋では復活せず、Revive が必要なままになる。
3. Potion / Ether / Antidote 等で Use を選ぶと対象選択UIへ遷移する。
4. Player / NPC1 / NPC2 から対象を選んでアイテム効果を適用できる。
5. HP/MP満タンや治療対象なしなどの無効対象ではアイテムが消費されない。
6. Mapping Scroll と Grimoire は従来通り対象選択なしで使用できる。
7. 回復SEとポップアップが選択対象に応じて発生する。
8. `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装内容と一致している。

---
※ 実装担当者への指示:
まず **Phase 21.1: 宿屋のパーティ回復化** から着手してください。次に `STATE_INV_TARGET_SELECT` を追加し、消費アイテムの対象選択フローを実装してください。
