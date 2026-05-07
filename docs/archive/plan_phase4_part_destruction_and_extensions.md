---
Target Plan File: `docs/plan_phase4_part_destruction_and_extensions.md`
---

# 1. Task Overview
本プランでは、Phase 4の最後の主要機能である「部位破壊システム」を実装します。あわせて、将来の拡張要素（NPCの個別装備、高度AI、ダンジョンギミック、遺品回収）をプロジェクトの正式なロードマップとして各仕様書（1.md, 2.md, 4.md）に定義・追記し、Phase 5への基盤を整えます。

# 2. Target Files
* `data.py`: `EnemyDef`, `Enemy` クラスへの部位データ構造の追加。
* `main.py`: 戦闘メニュー（部位ターゲット選択）の拡張、破壊判定ロジックの実装。
* `docs/1. 機能要件.md`: 拡張機能（NPC装備、ギミック、遺品回収）の要件追記。
* `docs/2. 仕様詳細.md`: 部位破壊の詳細ルール、トラップの種類、NPC AIパターンの追記。
* `docs/4. 開発タスク.md`: 部位破壊の完了チェックとPhase 5タスクの具体化。

# 3. Step-by-Step Instructions

## 3.1 部位破壊システムの実装
1.  **データ構造拡張 (`data.py`):**
    *   `EnemyDef` に `parts` リストを追加。例: `[{"name": "Tail", "hp_ratio": 0.3, "weakness": "ice", "drop_flag": "rare_scale"}]`
    *   `Enemy` クラスに `part_hps` (dict) と `broken_parts` (set) を追加し、生成時にHP計算（最大HP × ratio）して初期化する。
2.  **ターゲット選択の拡張 (`main.py`):**
    *   `STATE_BATTLE_TARGET_PART` 状態を新設。敵を選択した後、部位がある場合は部位リストを表示し、選択可能にする（「Body（本体）」も選択肢に含める）。
3.  **破壊判定と効果:**
    *   部位へのダメージ適用時、部位HPが0になったら破壊成功とし、ログ `[PART BROKEN: {Name}]` を表示。
    *   破壊された部位はターゲットリストから除外する。
    *   ドロップ処理 (`_handle_victory`) を修正し、破壊済み部位の `drop_flag` に対応するレアドロップ抽選（20%程度）を本体ドロップとは別枠で行う。

## 3.2 拡張機能のドキュメント化とタスク化（Claudeへの重要指示）
Claudeはコード実装と並行して、以下の内容を各ドキュメントに**必ず記述・追加**してください。

1.  **NPCの深化仕様:**
    *   `1. 機能要件.md`: 「NPC個別装備システム（プレイヤーから渡して装備可能）」および「ジョブ/性格に応じたスキル使用AI」の項を追記。
2.  **ダンジョンギミック & 遺品回収:**
    *   `2. 仕様詳細.md`: トラップタイル（Spike: ダメージ, Poison: 毒付与）の仕様と、全滅地点に生成される「遺品（Grave）」の回収フロー（戦闘発生、勝利でロスト品復元）を追記。
3.  **ロードマップの更新:**
    *   `4. 開発タスク.md`: 
        - 「部位破壊システム」を完了済みに更新。
        - Phase 5 のタスクとして「NPC個別装備と高度AIの実装」「トラップと環境ギミックの実装」「遺品回収イベントの実装」を明確なタスクとして追加。

# 4. Constraints
* **ASCII文字限定:** UI表示（`PART BROKEN`等）やドキュメント追記内容はすべて半角英数字。
* **UIの一貫性:** 部位選択は既存の `Window` クラスとカーソル選択スタイルを維持。

# 5. Success Criteria
1. 戦闘中、敵の部位（例: Orc Chiefの腕など）をターゲットにして攻撃できる。
2. 部位HPを0にすると破壊ログが表示され、戦闘終了時に追加のドロップ判定が行われる。
3. `docs/` 内の各ドキュメントに、指示された将来の拡張機能（NPC強化、トラップ、遺品回収）が具体的な仕様として記述されている。

# 6. (Optional) Example Data for Testing
`enemies.json` の `orc_chief` に以下のような部位データを追加してテストすること。
```json
"parts": [
  {"name": "Right Arm", "hp_ratio": 0.4, "weakness": "fire", "drop_flag": "chief_gauntlet"}
]
```