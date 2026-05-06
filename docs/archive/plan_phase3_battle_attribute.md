---
Target Plan File: docs/plan_phase3_battle_attribute.md
---

1. **Task Overview:**
   エンカウント率の調整と、戦闘に「属性（Attribute）」システムを導入します。
   武器に属性を付与し、敵に弱点（Weakness）と耐性（Resistance）を設定することで、戦略的な戦闘を可能にします。

2. **Target Files:**
   - `/workspaces/games/main.py`: エンカウント率の定数変更、ダメージ計算ロジックの更新。
   - `/workspaces/games/data.py`: `WeaponItem`, `EnemyDef`, `Status` クラスへの属性フィールド追加とデータロードの修正。

3. **Step-by-Step Instructions:**
   - **エンカウント率の調整 (`main.py`):**
     - `ENCOUNTER_RATE` を `0.3` から `0.15` に引き下げ、探索のストレスを軽減します。
   
   - **属性システムの基盤実装 (`data.py`):**
     - `WeaponItem` クラスに `attribute` フィールド（文字列、初期値 `None`）を追加します。
     - `EnemyDef` クラスに `weaknesses` と `resistances`（ともに文字列リスト）を追加します。
     - `EnchantedWeapon` クラスで属性を引き継げるよう修正します。
     - `Status` クラス（プレイヤー）に将来的な拡張のため `weaknesses`, `resistances` プロパティを追加します。
     - JSONからの読み込み関数 (`_build_item`, `_build_enemies`) で属性関連の値を辞書から取得するように更新します。

   - **ダメージ計算の更新 (`main.py`):**
     - `_calc_dmg` メソッドを修正し、以下の倍率を適用します。
       - 攻撃属性が対象の **Weakness** に含まれる場合: ダメージ **1.5倍**
       - 攻撃属性が対象の **Resistance** に含まれる場合: ダメージ **0.5倍**
     - 浮動小数点計算後の結果は `int()` で整数化し、最低ダメージ `1` を保証します。

   - **聖属性（holy）への対応:**
     - システム上 `holy` 属性を扱えるようにし、希少属性としての基礎を構築します。

4. **Constraints:**
   - 属性名などの内部文字列は ASCII のみを使用してください（例: "fire", "ice", "holy"）。
   - 既存の武器・敵データの構造を壊さないよう、属性データは `.get()` を用いてデフォルト値（空リストなど）を設定してください。

5. **Success Criteria:**
   - エンカウント頻度が体感で減少していること。
   - 武器に属性（例: "holy"）を設定した際、特定の敵（弱点設定済み）へのダメージが増加すること。
   - 耐性を持つ敵へのダメージが減少すること。
   - 属性がない武器では、従来通りのダメージ計算が行われること。