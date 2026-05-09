# Implementation Plan: Phase 18 - Porter Refinement

## 1. Task Overview
ゲームのコンセプトを「自身は戦わない荷物持ち（ポーター）」として完成させるため、以下の調整を行います。
- 初期解放ジョブを `warrior` から `porter` に変更。
- 戦闘メインコマンドを `Fight` から `Aid（援護）` に変更。
- ポーター専用の支援スキル `Encourage（鼓舞）` の実装。
- プレイヤー（ポーター）の初期ステータスを非戦闘員向けに下方修正（STR/DEF）し、支援能力（AGI/LUK/MP）を上方修正。
- 攻撃メッセージを「敵を牽制・妨害する」内容に刷新。

**※重要: 実装前に、Claude Code は各フェーズの「詳細なサブタスク（修正関数リスト等）」を自身で作成し、提示してください。**

## 2. Target Files
- `/workspaces/games/constants.py`: コマンド名の変更。
- `/workspaces/games/data.py`: ポーター用初期ステータス、スキルの定義。
- `/workspaces/games/main.py`: 初期ジョブ設定、攻撃メッセージ、スキル効果の実装。
- `/workspaces/games/docs/1. 機能要件.md`: コンセプトの更新。
- `/workspaces/games/docs/3. 仕様詳細.md`: スキル計算式等の追記。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 18 の追加と完了管理。

## 3. Sub-Phases & Instructions

### Phase 18.1: ポーター職の基礎定義
1. **ジョブ定義拡張**: `data/jobs.json` に `porter` を追加し、成長率（AGI/LUK高め、STR/DEF低め）を設定。
2. **定数更新**: `constants.py` の `COMMANDS` から `"Fight"` を除去し `"Aid"` を追加。
3. **初期スキル定義**: `data.py` の `JOB_SKILLS` に `porter` 用の `Encourage` を定義（`effect_type="encourage"`）。

### Phase 18.2: 戦闘演出とロジックの変更
1. **初期状態の固定**: `main.py` の `App.__init__` で `unlocked_jobs` を `["porter"]` に変更。
2. **攻撃メッセージ刷新**: `_player_attack` を修正し、ポーターの場合は「牽制」や「気を引く」表現に変更。
3. **支援スキル実装**: `_execute_active_skill` に `encourage` タイプを実装。生存メンバー全員を `power + LUK // 2` 回復。

### Phase 18.3: ドキュメント同期
1. **要件定義修正**: `1. 機能要件.md` にてポーターの役割を再定義。
2. **仕様詳細更新**: `3. 仕様詳細.md` に `Encourage` スキルの計算式を追記。
3. **タスク管理**: `4. 開発タスク.md` に Phase 18 を追加。

## 4. Constraints
- **ASCII制約**: ゲーム内表示文字列は全て半角英数字。
- **後方互換性**: 既存のセーブデータ読み込み時にエラーが出ないよう配慮。

## 5. Success Criteria
1. ゲーム開始時のデフォルトジョブが `Porter` になっている。
2. 戦闘コマンドが `Aid` に変更され、ログ演出がポーターらしい表現になっている。
3. `Encourage` スキルでパーティ全員が回復する。
4. ドキュメントが最新のゲームコンセプトと一致している。

---
※ Claude Code への指示：
まずは **Phase 18.1** の詳細なタスク分解案を提示してください。