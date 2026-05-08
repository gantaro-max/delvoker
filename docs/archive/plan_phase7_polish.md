# Implementation Plan: Polish (Audio & Juice)

## 1. Task Overview
ゲームの「手触り」を向上させるため、サウンドエディタを使用した効果音（SE）とBGMの実装、および視覚的なフィードバック（画面揺れ等）を追加します。

## 2. Target Files
- `/workspaces/games/main.py`: サウンド初期化、再生ロジック、画面揺れ演出の追加。

## 3. Step-by-Step Instructions

### 3.1 サウンドリソースの定義 (`main.py`)
- `_init_audio()` メソッドを作成し、`App.__init__` で呼び出す。
- `pyxel.sound` と `pyxel.music` を使用して、以下の簡易的な音色をコードで定義する。
    - **Sound 0 (Attack)**: 鋭いノイズ音。
    - **Sound 1 (Hit)**: 短い爆発音。
    - **Sound 2 (Heal)**: 上昇するアルペジオ音。
    - **Music 0 (Town)**: 穏やかなループ。
    - **Music 1 (Dungeon)**: 不気味なベースライン。
    - **Music 2 (Battle)**: アップテンポなリズム。

### 3.2 SEのトリガー設定 (`main.py`)
- `_player_attack`, `_enemy_turn`: 攻撃時に `pyxel.play(0, 0)`、ヒット時に `pyxel.play(1, 1)`。
- `_do_use` (回復アイテム): `pyxel.play(2, 2)`。
- `_set_state`: 状態遷移に合わせて `pyxel.music.play` を切り替える。

### 3.3 画面揺れ (Screen Shake) の実装 (`main.py`)
- `App` クラスに `self.shake_timer = 0` を追加。
- `_enemy_turn` でプレイヤーがダメージを受けた際、`self.shake_timer = 5` を設定。
- `draw()` の冒頭で、`shake_timer` が 0 より大きい場合、`pyxel.camera(random.randint(-2, 2), random.randint(-2, 2))` を実行。描画の最後で `pyxel.camera()` をリセットする。

### 3.4 ログのカラーリング拡張
- `_show_msgs` にメッセージ種別（警告、アイテム獲得など）を渡せるようにし、描画時の色を動的に変更する。

## 4. Document Updates
- `docs/4. 開発タスク.md`: Phase 6 の完了をマークし、Phase 7 (Polish) を追加。

## 5. Constraints
- すべてのサウンド定義は Python コード内（`pyxel.sound().set`）で行い、外部アセットファイル（.pyxres）に依存しない形式にすること（配布・管理の容易さのため）。
- ASCII制約を継続し、日本語文字は使用しないこと。

## 6. Success Criteria
1. 街、ダンジョン、戦闘でそれぞれ異なるBGMがループ再生されること。
2. 攻撃時やアイテム使用時に適切な効果音が鳴ること。
3. 被ダメージ時に画面が揺れ、視覚的なインパクトがあること。