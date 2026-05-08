# Implementation Plan: Final Objective & Teleport Skill

## 1. Task Overview
ゲームの終着点を実装します。B5F を最深部とし、そこで待ち構える「Dungeon Master」を撃破することで「Dungeon Core」を獲得し、ゲームクリア（エンディング）となる流れを構築します。また、利便性向上のため、街へ即座に帰還できる「Teleport」スキルを導入します。

## 2. Target Files
- `/workspaces/games/main.py`: `STATE_ENDING` の追加、最深部判定ロジック、テレポートスキルの実装。
- `/workspaces/games/data.py`: `Skill` クラスの拡張（戦闘外使用フラグ）、マップ生成の最終階層対応。
- `/workspaces/games/data/enemies.json`: 最終ボス「Dungeon Master」の定義。
- `/workspaces/games/data/items.json`: テレポートスキルを習得できる「Grimoire of Return」の追加。

## 3. Step-by-Step Instructions

### 3.1 最終階層とボスバトルの設定 (`main.py`, `data.py`)
- `MAX_DEPTH = 5` に更新（現在は 4）。
- `main.py` の `_next_floor` 修正：
    - `self.dungeon_floor` が `MAX_DEPTH` に達した場合、階段の代わりに「Dungeon Core」オブジェクト（または特殊タイル）を配置するか、階段を昇る際にボス戦を開始する判定を追加。

### 3.2 最終ボス「Dungeon Master」の追加 (`enemies.json`)
- `dungeon_master` を定義：
    - 高HP（150程度）、全属性耐性、強力な全体攻撃（予兆メッセージ付き）。
    - 撃破時の `gold_reward` を 0 とし、代わりにクリアフラグを立てる。

### 3.3 テレポートスキルの実装 (`main.py`, `data.py`)
- `Skill` クラスに `is_utility` フラグを追加（デフォルト False）。
- ダンジョン画面で `S` キーを押すことで習得済みのスキル一覧を表示し、使用できる仕組みを検討。
- `Teleport` スキル（消費MP: 10）を使用した場合、ダンジョンから即座に `STATE_TOWN` へ遷移する。
- `items.json` に `grimoire_return` を追加。

### 3.4 エンディング画面の実装 (`main.py`)
- `STATE_ENDING = 16` を定義。
- ボス撃破後のメッセージ（`_handle_victory`）から `_set_state(STATE_ENDING)` へ遷移。
- `_draw_ending`: 「CONGRATULATIONS!」のテキスト、最終的なスタッツを表示。

## 4. Document Updates
- `docs/1. 機能要件.md`: 「10. クリア目標」を実装済みに更新。
- `docs/2. 仕様詳細.md`: ボス階層とエンディングの仕様を追記。
- `docs/4. 開発タスク.md`: 該当タスクにチェックを入れる。

## 5. Constraints
- すべてのテキストは ASCII 文字のみを使用すること。
- テレポートは戦闘中には使用できないようにすること。
- ボス戦では「逃げる」を選択不可にするか、失敗確率を100%にする。

## 6. Success Criteria
1. B5F に到達し、「Dungeon Master」との戦闘が始まること。
2. ボス撃破後、エンディング画面が表示されること。
3. 「Teleport」スキルを習得し、ダンジョン内で使用することで街に帰還できること。