# Implementation Plan: Phase 3 NPC Promotion, Wipe-out Penalty, and Skill System

1. **Task Overview:**
   Phase 3の残存タスクである「NPCの昇格」「全滅時のアイテムロスト演出」「魔導書によるスキル習得」を一括で実装し、コアループに緊張感と深みを与えます。

2. **Target Files:**
   - `data.py`: `Status`クラスへのスキルリスト追加、`NPCMember`の昇格フラグ、`Skill`クラスの定義。
   - `main.py`: ギルドでの昇格処理、戦闘終了時のロスト判定演出、アイテム使用（魔導書）ロジックの実装。
   - `docs/1. 機能要件.md`: ギルド・ペナルティ・スキルの詳細追記。
   - `docs/2. 仕様詳細.md`: 昇格コスト、ロスト確率、スキル枠制限の仕様追記。
   - `docs/4. 開発タスク.md`: Phase 3 のタスクを完了に更新。

3. **Step-by-Step Instructions:**

   **Step 1: スキルと昇格のデータ基盤 (`data.py`)**
   - `Skill` クラスを追加（name, mp_cost, effect_type, power）。
   - `Status` に `skills = []` を追加（最大4枠）。
   - `NPCMember` に `is_unique = False` フラグを追加。これが `True` のNPCは戦闘中にコマンド操作を可能にする。

   **Step 2: ギルド機能の拡張 (`main.py`)**
   - `STATE_TOWN_SUB` (Guild) において、パーティにいる `NPCMember` を 1000 Gold で `is_unique` に昇格させる選択肢を実装。
   - 昇格したNPCは、戦闘時にプレイヤー同様のコマンド選択フローに組み込む。

   **Step 3: 全滅ペナルティとロスト演出 (`main.py`)**
   - `_upd_battle_end` にて、敗北時に `player.inventory` または装備中のアイテムからランダムに1つを抽出し、ロストさせる処理を追加。
   - ロスト時は専用のメッセージ `ITEM LOST: [Item Name]...` を表示し、SEの代わりに画面フラッシュ等の演出（簡易的で可）を行う。

   **Step 4: 魔導書システムの実装 (`main.py`)**
   - `_do_use` 関数を拡張。アイテム名に "Grimoire" が含まれる場合、対応するスキルを `Status.skills` に追加する。
   - スキル枠がいっぱいの場合は、上書きの確認を行う（今回は簡易的に一番古いスキルを消す、またはランダム上書きで可）。

4. **Document Updates:**
   - `1. 機能要件.md`: ギルドでの「固有NPC昇格」と「全滅時のロスト」の記述を具体化。
   - `2. 仕様詳細.md`: 昇格費用（1000G）、スキル最大数（4）を明記。

5. **Constraints:**
   - 全てのメッセージ、スキル名は ASCII文字のみを使用すること。
   - ロスト対象には装備中の武器・防具も含めること（ハクスラの緊張感維持）。

6. **Success Criteria:**
   - ギルドで金を払い、NPCを「固有メンバー」に昇格させ、戦闘で手動操作できる。
   - 全滅時、所持品が1つ消去され、ログで確認できる。
   - 魔導書（Grimoire）を使用してスキルを覚え、戦闘のコマンドに表示される（表示のみで実行ロジックはPhase 4でも可とするが、枠への追加は必須）。

7. **Archive Task:**
   - 作業完了後、本ファイルを `docs/archive/` に移動する。