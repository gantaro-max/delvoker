# Implementation Plan: Phase 4 Attribute Affinities and Armor Enchantment

1. **Task Overview:**
   属性システムの拡張（三すくみの導入）と、防具への属性付与およびエンチャント機能を実装します。プレイヤーと敵の双方が属性の相性の影響を受けるようにし、装備の選択肢を広げます。

2. **Target Files:**
   - `data.py`: `EnchantedArmor` クラスの追加、`Status` クラスの耐性計算ロジック改善、属性相性定数の定義。
   - `main.py`: `_calc_dmg` の相性判定拡張、防具ドロップへのエンチャント適用。
   - `docs/1. 機能要件.md`: 属性相性表の追記。
   - `docs/2. 仕様詳細.md`: 防具エンチャントと耐性の仕様追記。
   - `docs/4. 開発タスク.md`: Phase 4 の更新。

3. **Step-by-Step Instructions:**

   **Step 1: 属性相性の定義 (`data.py`)**
   - `ATTR_AFFINITY = {"fire": "ice", "ice": "poison", "poison": "fire"}` を定義。
   - `holy` は特殊属性とし、全属性（`holy` 以外）に対して 1.2x のボーナス、耐性持ちには 0.5x。

   **Step 2: 防具エンチャントの実装 (`data.py`)**
   - `EnchantedArmor(ArmorItem)` クラスを作成。接頭辞で `def_bonus`、接尾辞で `attribute`（耐性）を付与。
   - `make_enchanted_armor(base_key)` 関数を実装し、防具ドロップ時に抽選を行う。

   **Step 3: 耐性計算の動態化 (`data.py`)**
   - `Status.resistances` プロパティを変更し、`self.armor` が持つ `attribute` を自動的に耐性リストに含めるようにする。

   **Step 4: ダメージロジックの更新 (`main.py`)**
   - `_calc_dmg` において、`ATTR_AFFINITY` を用いた相性判定（1.5x / 0.5x）を追加。
   - 弱点を突いた場合、ログに `It's effective!` 等のメッセージを表示する仕組みを検討。

4. **Document Updates:**
   - `1. 機能要件.md`: 「3. 戦闘システム」に属性相性（Fire > Ice > Poison > Fire）を追加。
   - `2. 仕様詳細.md`: 防具の接頭辞（Sturdy, Light）と接尾辞（of Heat, of Cold）の定義を追記。

5. **Constraints:**
   - すべてのエンチャント名、ログメッセージは ASCII文字のみを使用。
   - 防具の `def_bonus` は最低 0 を保証。

6. **Success Criteria:**
   - `Fire` 属性の武器で `Ice` 耐性のない敵を攻撃するとダメージが 1.5倍になる。
   - `Fire` 属性を持つ防具を装備すると、敵からの `Fire` 攻撃ダメージが 0.5倍になる。
   - インベントリで防具に「Sturdy Cloth Armor +Fire」のようなラベルが表示される。