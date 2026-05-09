# Implementation Plan: Phase 17 - Porter System Overhaul & UI Polish

## 1. Task Overview
ゲームのコンセプトを「自身は戦わない荷物持ち（ポーター）」へと刷新し、それに伴う新ステータス（LUK）、装備枠（Accessory）、職種別装備制限を導入します。
あわせて、報告されたUIの不具合（Actionメニューのはみ出し等）と、多対多戦闘のバランス調整を完遂します。

**※重要: Claude Code は各フェーズの実装に着手する前に、必ず「詳細なタスク分解案（修正対象の関数名、JSON構造、UI座標の計算結果など）」を自身で作成・提示し、ユーザーの承認を得てください。**

## 2. Target Files
- `/workspaces/games/main.py`: UI、戦闘ロジック、インベントリ拡張。
- `/workspaces/games/data.py`: `Status`, `Job`, `Item` クラスのデータ構造拡張。
- `/workspaces/games/constants.py`: 定数追加、UIサイズの微調整。
- `/workspaces/games/systems/persistence.py`: セーブデータ互換性（LUK等のデフォルト値）処理。
- `/workspaces/games/docs/`: 全ドキュメントの同期。

## 3. Sub-Phases & Instructions

### Phase 17.1: 不具合修正 & 戦闘ロジック適正化
1. **UI修正**: `inv_action_win` の高さを `72` に拡大。ステータス表示（街/ダンジョン）に防具(`A:`)およびアクセサリー(`Acc:`)の行を追加。
2. **出現数調整**: `_start_battle` のランダム出現数を B3F+: 2体(30%)、B6F+: 2体(30%)/3体(10%) に設定。
3. **ターゲット分散**: `"normal"` AI のターゲットを `random.choice(alive)` に変更し、NPCも攻撃を受けるようにする。

### Phase 17.2: ポーターシステム基盤 (Stat & Accessory)
1. **LUK（幸運）の実装**: `Status` への追加、`Job` 成長率への統合。クリティカル判定（`LUK%`でダメージ2倍）および逃走成功率へのボーナス加算。
2. **Accessory（装飾品）枠**: `Status` へのスロット追加。`ITEM_CATALOG` に LUK や MP を補正する装飾品（Lucky Ring 等）を定義。
3. **セーブ互換性**: `persistence.py` にて、既存データに `luk` や `accessory` がない場合のデフォルト値補完を実装。

### Phase 17.3: 役割の差別化と装備制限
1. **ポーターの制約**: アイテムに `weight_class` ("light"/"heavy") を導入。プレイヤー（Porter）は "heavy" 武具の装備を試みた際に拒否されるバリデーションを `_do_equip` に追加。
2. **ポーターの利点**: プレイヤーのみ、初期インベントリ最大数を 8 から **12** へ拡張。ポーター用のスキルや装備アイテム（戦闘補助や簡易なステータス回復など）を導入
3. **NPC装備管理の高度化**: 「Give to NPC」を「Manage NPC Gear」へ拡張。NPCの全装備（W, A, Acc）を一覧・変更でき、旧装備を確実にプレイヤーのバッグへ回収する統合フローの実装。

### Phase 17.4: ドキュメント刷新
1. `docs/1. 機能要件.md`: プレイヤーがポーターである世界観への修正。
2. `docs/3. 仕様詳細.md`: LUK 計算式、装備制限テーブル、新出現率の詳述。
3. `docs/4. 開発タスク.md`: Phase 17 完了の記録。

## 4. Constraints
- **ASCII制約**: ゲーム内表示、ログ、コメントはすべて半角英数字（ASCII）のみ。
- **1ファイルずつの修正**: 大規模変更のため、一度に全てのファイルを書き換えず、サブタスク単位で確実にコードを確定させること。

## 5. Success Criteria
1. インベントリの Action メニューが Cancel まで正常に表示される。
2. 複数敵が出現し、NPCも攻撃対象になる。
3. プレイヤー（ポーター）が重装備を拒否され、インベントリ枠が12に増えている。
4. アクセサリーを装備でき、LUK によるクリティカル演出が動作する。
5. NPCの装備を統合管理できるUI/フローが機能している。

---
※ Claude Code への指示：
**Phase 17.1 (不具合修正 & 戦闘調整)** のタスク分解から開始してください。
まず、「どの関数のどの座標を修正するか」「出現確率をどう分岐させるか」のリストを提示してください。