# Implementation Plan: Phase 27 - Content Variety Expansion Tasks

## 1. Task Overview

モンスター、武器、防具のバリエーションを増やし、階層別エンカウント・階層別ドロップ・属性相性・部位破壊・エンチャントの既存システムをより活かすための開発タスクを `docs/4. 開発タスク.md` に追記する。

今回の指示書はタスク分解とロードマップ追記のためのものであり、この段階では `data/enemies.json`、`data/items.json`、`main.py` などの実装ファイルは変更しない。

主目的:
- B1F-B3F / B4F-B6F / B7F-B10F の各ティアに、役割の異なる通常モンスターを追加する。
- 武器・防具の基礎装備を増やし、エンチャント抽選時のハクスラ感を高める。
- 通常敵にも一部だけ部位破壊・特殊ドロップを導入し、狙って倒す楽しさを増やす。
- 追加データを階層別エンカウント、ドロップ、ショップ在庫、Bestiary、スプライト座標契約へ自然に接続する。

## 2. Target Files

- `/workspaces/games/docs/4. 開発タスク.md`: Phase 27 のタスクを未着手状態で追記する。
- `/workspaces/games/docs/3. 仕様詳細.md`: 実装フェーズ完了後に、追加モンスター・追加装備・部位破壊・ティア配分を同期する。
- `/workspaces/games/data/enemies.json`: 実装フェーズで追加モンスター定義を入れる対象。
- `/workspaces/games/data/items.json`: 実装フェーズで追加武器・防具・特殊ドロップを入れる対象。
- `/workspaces/games/data/enchants.json`: 必要に応じてエンチャント候補の拡張を検討する対象。
- `/workspaces/games/main.py`: 実装フェーズで `_encounter_pool(floor)`、`_drop_pools(floor)`、ショップ在庫候補、特殊ドロップ処理を調整する対象。
- `/workspaces/games/assets.pyxres`: 新規モンスターに専用スプライトを割り当てる場合の最終リソース。
- `/workspaces/games/assets/source/image2/monsters/`: 新規モンスター原画の受け入れ候補。

## 3. Roadmap Entry Instructions

`docs/4. 開発タスク.md` の Phase 26 の後、Future Issues の前に `Phase 27: Content Variety Expansion（未着手）` を追加する。

各チェック項目は未着手の `[ ]` とし、実装開始時にそのまま作業チェックリストとして使える粒度にする。

## 4. Proposed Phase 27 Task Breakdown

### Phase 27.1: 追加コンテンツ設計（未着手）

1. 既存の `data/enemies.json`、`data/items.json`、`data/enchants.json` を確認し、現行のHP、DEF、武器ダイス、報酬、価格レンジを整理する。
2. 追加モンスターは各ティア2体、合計6体を基本単位とする。
3. 追加武器は各ティア2種、合計6種を基本単位とする。
4. 追加防具は各ティア2種、合計6種を基本単位とする。
5. 追加コンテンツは既存の属性 `fire` / `ice` / `poison` / `holy` とAIタイプ `normal` / `ranged` / `support` を優先して使い、新システム追加を最小限にする。
6. ゲーム内表示名はASCIIのみとし、長すぎる名前はUI短縮表示でも判別できる長さに抑える。

### Phase 27.2: 低階層モンスター追加（B1F-B3F）（未着手）

1. `kobold` を追加候補とする。
   - 役割: Goblinより速い軽量敵。
   - AI: `ranged` または `normal`。
   - 狙い: AGI型・軽装備の価値を序盤から見せる。
2. `ooze` を追加候補とする。
   - 役割: 低攻撃、高HP、poison耐性の耐久敵。
   - AI: `normal`。
   - 狙い: 毒属性だけに頼る戦い方への軽い対策。
3. B1F-B3Fの `_encounter_pool(floor)` に、既存 Slime / Bat / Goblin / Skeleton との出現比率を崩さない形で追加する。
4. 低階層のEXP/Goldは既存敵の `8-20 EXP`、`3-15 Gold` を基準に調整する。

### Phase 27.3: 中階層モンスター追加（B4F-B6F）（未着手）

1. `cultist` を追加候補とする。
   - 役割: support AIでHPが低い味方を狙う人型敵。
   - 弱点: `holy`。
   - 狙い: 複数戦でのターゲット優先度を作る。
2. `ice_hound` を追加候補とする。
   - 役割: fire弱点、ice耐性の属性チュートリアル強化敵。
   - AI: `ranged`。
   - 狙い: fire武器・fireスキルの価値を中盤で上げる。
3. B4F-B6Fの `_encounter_pool(floor)` に追加し、Wraith / Golem / Mimic / Wyvern との難度差を調整する。
4. 中階層のEXP/Goldは既存敵の `30-70 EXP`、`20-50 Gold` を基準に調整する。

### Phase 27.4: 高階層モンスター追加（B7F-B10F）（未着手）

1. `dark_knight` を追加候補とする。
   - 役割: 高DEF、holy弱点、stun付与の重装敵。
   - AI: `normal` または `support`。
   - 狙い: holy攻撃と高火力武器の価値を上げる。
2. `lich` を追加候補とする。
   - 役割: holy弱点、fire/ice耐性、telegraph持ちの魔術師敵。
   - AI: `support`。
   - 狙い: 終盤の準ボス級通常敵として緊張感を作る。
3. B7F-B10Fの `_encounter_pool(floor)` に追加し、Archdemon前の終盤プールを厚くする。
4. 高階層のEXP/Goldは既存敵とボスの間に収め、通常戦の報酬過多を避ける。

### Phase 27.5: 武器バリエーション追加（未着手）

1. 低階層武器を追加する。
   - `hand_axe`: Hand Axe。最大値寄りの序盤武器。
   - `spear`: Spear。軽量で扱いやすい序盤武器。
2. 中階層武器を追加する。
   - `war_hammer`: War Hammer。高DEF敵に刺さる固定値寄り武器。
   - `rune_staff`: Rune Staff。Mage向けの雰囲気を持つ軽量武器。
3. 高階層武器を追加する。
   - `dragon_slayer`: Dragon Slayer。高価格・高火力の終盤重武器。
   - `shadow_blade`: Shadow Blade。軽量高額の終盤レア武器。
4. 追加武器はすべて `make_enchanted_weapon()` の既存抽選に乗る基礎武器として定義する。
5. ダイス性能は既存武器の段階を壊さないよう、Old Dagger < Short Sword < Long Sword < Steel Sword < Mithril Sword の延長線上で調整する。

### Phase 27.6: 防具バリエーション追加（未着手）

1. 低階層防具を追加する。
   - `padded_armor`: Padded Armor。安価なDEF+1装備。
   - `hunter_cloak`: Hunter Cloak。軽量でThief/NPC向けのDEF+2装備。
2. 中階層防具を追加する。
   - `scale_mail`: Scale Mail。Chain MailとSteel Plateの中間装備。
   - `mage_robe`: Mage Robe。低DEFだが軽量・魔法職向けの装備候補。
3. 高階層防具を追加する。
   - `dragon_mail`: Dragon Mail。高DEFかつfire耐性候補。
   - `aegis_plate`: Aegis Plate。高価格・高DEFの終盤重防具。
4. 追加防具はすべて `make_enchanted_armor()` の既存抽選に乗る基礎防具として定義する。
5. 防具の `weight_class` は既存の装備制限・表示仕様と矛盾しないように設定する。

### Phase 27.7: 部位破壊と特殊ドロップ追加（未着手）

1. 通常敵のうち2-3体にだけ部位破壊を追加し、通常戦のテンポを壊さない範囲に留める。
2. 候補:
   - `wyvern`: Wing破壊で `wing_boots` などの軽量防具またはアクセサリー候補。
   - `golem`: Core破壊で `stone_core` などの高DEF素材装備候補。
   - `dark_knight`: Shield破壊で `black_shield` などの防具候補。
3. 既存の部位破壊ドロップ率20%を基本として流用する。
4. 特殊ドロップ用アイテムは `data/items.json` に追加し、通常ドロッププールには入れすぎない。
5. 部位名、ログ、アイテム名はASCIIのみとする。

### Phase 27.8: ドロップ・ショップ・経済バランス調整（未着手）

1. `_drop_pools(floor)` に追加武器・防具を階層別に配分する。
2. ショップ在庫候補にも低-中階層装備を中心に追加し、高階層装備はドロップ・宝箱寄りにする。
3. 価格は既存装備の価値レンジに合わせる。
   - 低階層: 20-120G程度。
   - 中階層: 150-400G程度。
   - 高階層: 500G以上。
4. レアリティ抽選、Genesis抽選、売却価格30%の既存仕様を壊さない。
5. 宝箱・敵ドロップ・ショップのどれで入手できるかを装備ごとに整理する。

### Phase 27.9: スプライト・Bestiary・表示連携（未着手）

1. 新規モンスターに `sprite_u` / `sprite_v` を割り当てる。
2. 既存Bank 0の32x32モンスターグリッドと衝突しない座標を使う。
3. 新規スプライトがまだない場合は矩形フォールバックでも判別できるよう、名前と頭文字表示を確認する。
4. Bestiaryに追加モンスターが撃破後に表示されることを確認する。
5. 敵名・装備名が戦闘画面、インベントリ、ショップ、ログでUIからはみ出さないよう確認する。

### Phase 27.10: ドキュメント同期と検証（未着手）

1. `docs/3. 仕様詳細.md` に追加モンスター、追加装備、部位破壊ドロップ、階層別プールの仕様を追記する。
2. `docs/4. 開発タスク.md` のPhase 27チェックリストを実装結果に合わせて更新する。
3. 実装・検証完了後、この指示書を `docs/archive/` へ移動する。

## 5. Constraints

- ゲーム内表示文字列はASCIIのみ。
- Pyxel色番号は0-15のみ。
- 既存JSONの読み込み互換性を壊さない。
- 追加コンテンツは既存システムを優先して使い、新しい戦闘システム追加はこのPhaseでは原則行わない。
- 高階層装備を序盤で入手しすぎないよう、ドロップ・ショップ・宝箱の配分を調整する。
- 通常敵の部位破壊は増やしすぎず、戦闘テンポを維持する。
- Phase 26 が未完了の場合でも、Phase 27のタスク追記は独立して行えるようにする。

## 6. Acceptance Criteria

- `docs/4. 開発タスク.md` に Phase 27 が未着手タスクとして追加されている。
- Phase 27 はモンスター追加、武器追加、防具追加、部位破壊、ドロップ/ショップ、表示連携、ドキュメント同期に分解されている。
- 追加候補名、役割、対象階層、実装対象ファイルが明記されている。
- 実装担当者がこの指示書と開発タスクだけを見て、次の実装フェーズを開始できる。
- この指示書自体は実装完了まで `docs/instructions/` に残す。

## 7. Recommended Verification

1. `docs/4. 開発タスク.md` に Future Issues より前の位置で Phase 27 が追加されていることを確認する。
2. チェックボックスがすべて `[ ]` の未着手状態であることを確認する。
3. ゲーム内に出る予定の名称がASCIIのみであることを確認する。
4. 既存Phase 26のタスク内容を上書き・削除していないことを確認する。
