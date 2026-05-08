# Implementation Plan: Persistence & Meta-Progression (Phase 10)

## 1. Task Overview
ゲームの進行状況（ゴールド、倉庫、永続強化、クリアフラグ）をファイルに保存するセーブシステムを実装します。また、一度ゲームをクリア、あるいは特定の階層に到達することで新しいジョブ（Thief, Mage等）が選択可能になる「メタプログレッション」を導入します。

## 2. Target Files
- `/workspaces/games/main.py`: セーブ・ロード処理の実装、タイトル画面でのジョブ選択UIの構築。
- `/workspaces/games/data.py`: `Player` データのシリアライズ対応、ジョブ定義の追加。

## 3. Step-by-Step Instructions

### 3.1 セーブデータの構造定義 (`main.py`)
- `save_data()` / `load_data()` メソッドを `App` クラスに追加。
- 保存対象：`player.gold`, `player.warehouse`, `player.warehouse_max`, `player.perm_stats`, `unlocked_jobs` (list), `game_cleared` (bool)。
- Python の `json` モジュールを使用して `delvoker_save.json` に保存。

### 3.2 セーブ・ロードのタイミング (`main.py`)
- **セーブ**: 街に戻ったタイミング、または拠点での強化直後に実行。
- **ロード**: `App.__init__` 時にファイルが存在すれば自動で読み込む。

### 3.3 ジョブ選択システムと新規ジョブ (`data.py`, `main.py`)
- `JOBS` に新しいジョブを追加：
    - `thief`: HP低め、AGI特化。
    - `mage`: HP/DEF低め、MP/MAG特化。
- タイトル画面（または `Enter Dungeon` の前）でジョブを選択できる `STATE_JOB_SELECT` を実装。
- 初期状態では `warrior` のみ、B5F到達で `thief` 解放、B10Fクリアで `mage` 解放などのフラグ管理を行う。

### 3.4 タイトル画面の刷新 (`main.py`)
- ゲーム起動時に「New Game」か「Continue」を選択できるように変更（セーブデータがある場合）。

## 4. Document Updates
- `docs/1. 機能要件.md`: 「11. 永続化と解放要素」を追加。
- `docs/4. 開発タスク.md`: Phase 10 を追加し、進捗を管理。

## 5. Constraints
- セーブデータは ASCII 形式の JSON とする。
- 倉庫内の「エンチャント武器」のデータ（prefix/suffix）がセーブ・ロードで復元できるよう、シリアライズ処理に注意すること。
- 日本語は使用せず、すべて ASCII 文字で完結させること。

## 6. Success Criteria
1. ゲームを終了して再起動した後も、所持金や倉庫の中身、Training の強化値が維持されていること。
2. ダンジョンマスターを撃破した後、新しいジョブが選択可能になっていること。
3. セーブデータファイルがない場合でも、正常に初期状態で起動すること。