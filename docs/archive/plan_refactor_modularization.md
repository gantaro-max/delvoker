# Implementation Plan: Structural Refactoring & Modularization

## 1. Task Overview
肥大化した `main.py` および `data.py` を機能ごとに分割し、メンテナンス性と拡張性を向上させます。
「定数」「データモデル」「マップ生成」「描画ロジック」「永続化」を別モジュールに切り出し、`main.py` をゲーム全体の司令塔としてスリム化します。

## 2. Target Files
### New Files:
- `/workspaces/games/constants.py`: 状態、色、タイル等の定数定義。
- `/workspaces/games/logic/map_generator.py`: `Map` クラスおよびダンジョン生成ロジック。
- `/workspaces/games/ui/renderer_3d.py`: 3Dビューの描画処理 (`draw_3d_view`)。
- `/workspaces/games/systems/persistence.py`: セーブ/ロードおよびシリアライズ処理。

### Existing Files (Refactor):
- `/workspaces/games/data.py`: データカタログの読み込みと基本クラス定義に限定。
- `/workspaces/games/main.py`: インポートの整理と、UI/システムの呼び出しに専念。

## 3. Step-by-Step Instructions

### 3.1 定数の分離 (`constants.py`)
- `main.py` および `data.py` に点在する以下の定数を `constants.py` へ移動。
  - `STATE_*`, `COL_*`, `TILE_*`, `DIR_*`, `VIEW_H`, `MAX_FLOOR`, `INV_MAX` 等。
  - `TOWN_MENU`, `SHOP_KEYS` 等のリスト定数。

### 3.2 マップ生成ロジックの抽出 (`logic/map_generator.py`)
- `data.py` から `Map` クラスと `generate_random` メソッドを `logic/map_generator.py` に移動。
- 依存関係を整理し、`constants.py` から `TILE_*` をインポートするように修正。

### 3.3 永続化システムの抽出 (`systems/persistence.py`)
- `main.py` にある `save_data`, `load_data` および `_serialize_item`, `_deserialize_item` を `systems/persistence.py` に移動。
- `App` クラスに依存しないよう、データを受け取って辞書またはJSONを返す独立した関数として再定義。

### 3.4 3Dレンダラーの分離 (`ui/renderer_3d.py`)
- `main.py` の `draw_3d_view` 関数を `ui/renderer_3d.py` に移動。
- `App` インスタンス（または必要な座標情報）を引数として受け取る形式に変更。

### 3.5 `main.py` のクリーンアップ
- 分割した各モジュールをインポート。
- `App` クラス内の巨大なメソッドを、分割後の各クラス・関数の呼び出しに置き換え。
- 不要になったヘルパー関数を削除。

## 4. Document Updates
- `docs/4. 開発タスク.md`: 「リファクタリングとモジュール分割」という新しいフェーズ（Phase 11）を追加。
- `docs/3. データ構造.md`: ファイル構成の変更に合わせて、クラスがどのファイルに存在するかを更新。

## 5. Constraints
- **循環参照に注意**: `constants.py` をハブにすることで、モジュール間での相互インポートを避けること。
- **ASCII制約**: ファイル名、ディレクトリ名、コード内のコメント、ログはすべて ASCII 文字を使用すること。
- **動作の維持**: リファクタリング前後でゲームの内容（仕様）が変化しないようにすること。

## 6. Success Criteria
1. ゲームが正常に起動し、タイトル画面、街、ダンジョンの遷移がリファクタリング前と同様に動作する。
2. `main.py` の行数が 1300行から大幅に（目標: 800行以下）削減される。
3. 新しく作成した各ファイルが、適切な責務（データ、描画、ロジック）を保持している。
4. セーブ/ロードが正常に行われ、既存のセーブデータが破損しない。