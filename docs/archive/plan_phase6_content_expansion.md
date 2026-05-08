# Implementation Plan: Content Expansion (Phase 6)

## 1. Task Overview
現在の5階層・数種類のモンスターという構成を大幅に拡張し、ハクスラとしてのプレイサイクルを長期化させます。具体的には、最大階層を10階に引き上げ、中盤・終盤に向けた敵とアイテムのバリエーションを追加し、階層に応じたドロップロジックを実装します。

## 2. Target Files
- `/workspaces/games/main.py`: `MAX_FLOOR` の更新、階層別ドロップテーブルの導入、B10Fボス判定の追加。
- `/workspaces/games/data/enemies.json`: 新規モンスター（Wraith, Golem, Mimic, Wyvern, Final Boss）の追加。
- `/workspaces/games/data/items.json`: 上位装備（Steel/Mithril）、新規魔導書（Ice/Poison）、消費アイテム（Antidote）の追加。

## 3. Step-by-Step Instructions

### 3.1 階層設定の変更 (`main.py`)
- `MAX_FLOOR = 10` に更新。
- `_upd_dungeon` 内の階段判定で、`dungeon_floor == 5` の場合は `dungeon_master`（中ボス）との戦闘、`dungeon_floor == 10` の場合は新ボスの戦闘を開始するように変更。

### 3.2 モンスターデータの拡充 (`enemies.json`)
- **Wraith**: HP35, `holy` 弱点, `fire/ice` 耐性。
- **Golem**: HP80, DEF 5, AGI 1。
- **Mimic**: 宝箱に擬態（`TILE_CHEST` 接触時に一定確率で出現するよう `main.py` を調整）。
- **Wyvern**: AGI 8, 高火力の物理攻撃。
- **Archdemon** (B10F Boss): HP 300, 全属性耐性、強力な全体攻撃。

### 3.3 アイテム・ティアの実装 (`items.json`)
- 既存の `WEAPON_DROP_POOL` を廃止し、階層別プールを定義。
  - Tier 1 (B1-B3): `old_dagger`, `short_sword`, `leather_armor`
  - Tier 2 (B4-B6): `long_sword`, `chain_mail`, `grimoire_ice`
  - Tier 3 (B7-B10): `mithril_sword`, `steel_plate`, `grimoire_poison`
- `antidote` (毒解除) アイテムを追加。

### 3.4 階層別ドロップロジックの実装 (`main.py`)
- `_open_chest` 関数内で、現在の `self.dungeon_floor` に基づいて抽選するアイテムリストを動的に選択するロジックを実装。

### 3.5 状態異常治療の実装 (`main.py`)
- `_do_use` 関数において、`antidote` 使用時に `player.status_effects["poison"] = 0` とする処理を追加。

## 4. Document Updates
- `docs/1. 機能要件.md`: 「10. クリア目標」の内容をB10Fへ更新。
- `docs/2. 仕様詳細.md`: 階層ごとの出現モンスター・アイテム一覧を追記。
- `docs/4. 開発タスク.md`: Phase 6 として本タスクの内容を追記し、管理。

## 5. Constraints
- テキストはすべて ASCII 文字（半角英数字・記号）を使用すること。
- インフレが激しくなりすぎないよう、B10Fクリア時の推奨攻撃力を算出し、敵HPを設定すること（目安：1ターン30〜40ダメージ × 8〜10ターンで倒せる程度）。

## 6. Success Criteria
1. B5F で `dungeon_master` が出現し、撃破後に B6F へ進めること。
2. B10F に到達した際、新ボスとの最終決戦が発生し、勝利後にエンディングが表示されること。
3. 階層が進むにつれて、チェストからより強力な（Tierの高い）装備がドロップすること。
4. 毒状態が `antidote` で正常に解除されること。