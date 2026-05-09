# Implementation Plan: Phase 15 - Rebalance & UI Fix

## 1. Task Overview
UIの表示不具合（はみ出し・重なり）の解消、およびゲームバランス（エンカウント・トラップ・鍵扉生成ロジック）の抜本的な再調整を行います。

## 2. Target Files
- `/workspaces/games/main.py`: UI配置修正、エンカウント歩数管理の実装。
- `/workspaces/games/logic/map_generator.py`: 階層に応じた生成ロジック（トラップ・扉・鍵）の再設計。
- `/workspaces/games/docs/3. 仕様詳細.md`: 調整後の計算式・アルゴリズムの更新。
- `/workspaces/games/docs/4. 開発タスク.md`: フェーズ進捗の更新。

## 3. Sub-Phases & Instructions

### Phase 15.1: UIレイアウトの精密修正
1. **ACTIONメニュー修正**: `main.py` の `self.inv_action_win` の幅を `100` -> `120` に拡大。
2. **SHOP画面修正**: `main.py` の `_draw_shop` および `_draw_dungeon_shop` にて、商品名の文字数制限を `[:18]` に適用し、価格との重なりを防止。
3. **価格表示位置の調整**: 価格の描画X座標を調整して視認性を向上。

### Phase 15.2: エンカウント・ロジックの適正化
1. **歩数カウンター導入**: `App.__init__` に `self.steps_since_encounter = 0` を追加。
2. **確率制御**: `_upd_dungeon` にて、戦闘直後（3歩以内）はエンカウント率を 0 にし、その後徐々に上昇させるロジックを実装。戦闘開始時にカウンターをリセット。

### Phase 15.3: 階層に応じたトラップ・扉の再配置
1. **トラップ制限**: `logic/map_generator.py` の `generate_random` を修正。1-2Fではトラップ数を 0 にし、中層までは 1 個、深層で最大 2 個とする。
2. **鍵扉の段階的導入**: 1-2Fでは扉を生成しない。3-5Fでは最大1枚、それ以降で最大2枚とする。
3. **鍵の入手保証**: 扉がある場合は必ず鍵チェストを配置するロジックを強化。

### Phase 15.4: ドキュメント同期
1. **仕様詳細更新**: `docs/3. 仕様詳細.md` に新しいエンカウント式と階層別生成ルールを追記。
2. **タスク更新**: `docs/4. 開発タスク.md` に Phase 15 を追加。

## 4. Constraints
- **ASCII制約**: 全ての表示文字列はASCIIのみ。
- **互換性**: セーブデータ構造は変更しない。

## 5. Success Criteria
1. 各メニュー（Action/Shop）でテキストが枠を突き抜けない。
2. 戦闘終了後、少なくとも数歩は確実に探索できる。
3. 低階層において「鍵がないのに扉がある」「トラップだらけ」という理不尽な状況が発生しない。