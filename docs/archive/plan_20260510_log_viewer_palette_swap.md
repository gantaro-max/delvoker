# Implementation Plan: Phase 19 - Battle Log Viewer & Monster Palette Variants

## 1. Task Overview
戦闘状況をあとから確認できるログビューアを追加し、同時に限られた `.pyxres` モンスターアセットから階層差・強敵感を出すためのパレットスワップと左右反転描画を導入します。

主目的:
- プレイヤーが直近の戦闘ログを見返せるようにする。
- `assets.pyxres` の単一スプライト群を、色替え・反転で効率よくバリエーション化する。
- ログビューア中は戦闘進行を完全停止し、毒ダメージや敵ターンなどのバックグラウンド処理を走らせない。

## 2. Target Files
- `/workspaces/games/constants.py`: `STATE_LOG_VIEW` 定数、必要なら BGM ゾーン定義を追加。
- `/workspaces/games/main.py`: ログ履歴管理、ログビューアの update/draw、戦闘中入力導線、敵描画のパレットスワップ・左右反転対応。
- `/workspaces/games/data.py`: `EnemyDef` / `Enemy` の sprite・palette・flip 用フィールド拡張が必要な場合に更新。
- `/workspaces/games/data/enemies.json`: 全敵の `sprite_u` / `sprite_v` 定義維持、必要なら `palette_tier` や `palette_swaps` を追加。
- `/workspaces/games/docs/3. 仕様詳細.md`: ログビューア、パレットスワップ、アセットフォールバック仕様を追記。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 19 のタスクと完了チェックを追加。

## 3. Sub-Phases & Instructions

### Phase 19.1: ログ履歴基盤
1. **状態定数追加**: `constants.py` に `STATE_LOG_VIEW = 23` を追加する。既存 `STATE_BATTLE_SKILL = 22` の次番号を使い、重複を避ける。
2. **BGMゾーン登録**: `BGM_ZONES` に `STATE_LOG_VIEW` を追加する。戦闘中から開く想定のため、ゾーンは Battle BGM (`2`) とする。
3. **履歴フィールド追加**: `App.__init__` に `self.message_history = []` を追加する。最大保持数は `LOG_HISTORY_MAX = 100` などの定数で管理する。
4. **履歴追加ヘルパー**: `main.py` に `_append_message_history(messages)` を追加する。
   - `messages` は list[str] を受け取る。
   - 空文字は保存しない。
   - ゲーム内表示文字列は ASCII のみを維持する。
   - 追加後、古い行から削除して最大100行に収める。
5. **既存メッセージとの接続**: `_show_msgs(messages, next_state, colors=None)` の冒頭または末尾で `_append_message_history(messages)` を呼ぶ。
   - `_show_msgs` を通らない直接ログ追加箇所があれば、同じヘルパーを使って履歴に流す。
   - `self.messages` への代入・`self.message_colors` の既存挙動は壊さない。

### Phase 19.2: `STATE_LOG_VIEW` の入力・描画
1. **復帰先管理**: `App.__init__` に `self.log_return_state = STATE_BATTLE_CMD` と `self.log_scroll = 0` を追加する。
2. **ログビュー起動導線**: 戦闘関連ステートで L キーなどを押したら `STATE_LOG_VIEW` に遷移する。
   - 対象候補: `STATE_BATTLE_CMD`, `STATE_BATTLE_NPC_CMD`, `STATE_BATTLE_TARGET`, `STATE_BATTLE_TARGET_PART`, `STATE_BATTLE_SKILL`, `STATE_BATTLE_MSG`, `STATE_BATTLE_END`
   - 起動前に現在ステートを `self.log_return_state` に保存する。
   - `STATE_BATTLE_MSG` から開く場合は `msg_idx` を保持したまま戻せるようにする。
3. **ポーズ保証**: `STATE_LOG_VIEW` の update では、敵ターン・毒ダメージ・ポップアップ更新・戦闘タイマー進行を実行しない。
   - `update()` のステート分岐に専用 `_upd_log_view()` を追加し、他の戦闘 update にフォールスルーしない。
   - `draw()` は背景として通常の戦闘画面を描いてからログウィンドウを重ねてもよいが、状態進行処理は一切行わない。
4. **スクロール操作**: `_upd_log_view()` を実装する。
   - Up/Down: 1行スクロール。
   - PageUp/PageDown 相当が必要なら Left/Right で複数行スクロール。
   - X または L: `self.log_return_state` に戻る。
   - 履歴が空なら `"No logs."` を表示する。
5. **描画実装**: `_draw_log_view()` を追加する。
   - 画面上部または中央に Window を表示し、最新ログから遡れる構成にする。
   - 1画面に表示する行数は Pyxel の解像度に合わせて 8〜12 行程度。
   - 色付き履歴を保持しない場合は白(7)でよい。将来的に色を保存するなら `(text, color)` の構造に拡張する。

### Phase 19.3: モンスター描画バリエーション
1. **アセットロード継続**: `App.__init__` の `pyxel.load("assets.pyxres")` try-except と `self.assets_loaded` フラグを維持する。
   - `assets.pyxres` が無い場合は従来通り `pyxel.rect` フォールバックで描画する。
   - フォールバック中もクラッシュさせない。
2. **sprite座標の徹底**: `data/enemies.json` の全敵に `sprite_u` / `sprite_v` が定義されていることを確認する。
   - 既存の `EnemyDef.sprite_u` / `sprite_v` 読み込みを維持する。
   - 新規敵追加時も必須項目として扱う。
3. **階層別パレットロジック**: `_draw_battle` 内、または小さなヘルパー `_enemy_palette_swaps(enemy, floor)` を追加して階層に応じた色変換を返す。
   - 例: B1-3F は通常色、B4-6F は寒色寄り、B7-10F は赤・紫寄り、ボスは専用配色。
   - `pyxel.pal(orig, new)` は色番号 0〜15 の範囲のみ使う。
   - ゲーム全体のUI色を壊さないよう、敵スプライト描画直後に必ず引数なしの `pyxel.pal()` でリセットする。
4. **左右反転のランダム化**: 戦闘開始時に敵ごとの反転フラグを決め、描画中に毎フレーム変わらないようにする。
   - 推奨: `Enemy.__init__` で `self.flip_x = random.random() < 0.5` を設定する。
   - または `_start_battle` で生成後に付与する。
   - `_draw_battle` の `pyxel.blt` では、`flip_x` が True の場合 `w = -32` とし、描画開始 `x` を調整する。
   - 反転時も当たり判定・UI座標・HPバー位置は変えない。
5. **描画ヘルパー化**: `_draw_battle` が肥大化する場合は `_draw_enemy_sprite(enemy, x, y, floor)` に分離する。
   - Refactor Agent 条件に該当するため、描画処理を小さく保つ。
   - パレット適用・`pyxel.blt`・`pyxel.pal()` リセットを同じヘルパー内に閉じ込める。

### Phase 19.4: ドキュメント同期
1. **仕様詳細更新**: `docs/3. 仕様詳細.md` に以下を追記する。
   - `STATE_LOG_VIEW` の目的、起動キー、戻り先、ポーズ仕様。
   - `message_history` 最大100行、保存タイミング。
   - `pyxel.pal()` 使用時のリセット義務。
   - `assets_loaded = False` 時のフォールバック描画継続。
2. **開発タスク更新**: `docs/4. 開発タスク.md` に Phase 19 を追加し、各サブタスクのチェックボックスを作成する。
3. **実装指示書の完了処理**: 実装・確認が完了したら、このファイルを `docs/archive/` に移動する。移動時は同名衝突を避ける。

## 4. Constraints
- **ASCII制約**: ゲーム内ログ、UIテキスト、敵名表示はすべて ASCII 文字にする。
- **Pyxel色制約**: `pyxel.pal(orig, new)` の `orig` / `new` は 0〜15 の範囲に限定する。
- **パレットリセット必須**: 敵スプライト描画後は必ず `pyxel.pal()` を呼び、UI・テキスト・メニューの色化けを防ぐ。
- **ポーズ仕様厳守**: `STATE_LOG_VIEW` 中は敵行動、毒ダメージ、ターン経過、勝敗判定を進めない。
- **フォールバック維持**: `assets.pyxres` が存在しない環境でも起動・戦闘描画できる状態を保つ。
- **表示安定性**: 左右反転は戦闘開始時に固定し、描画フレームごとにランダム再抽選しない。

## 5. Success Criteria
1. 戦闘中にログビューアを開き、直近最大100行のメッセージ履歴をスクロール確認できる。
2. ログビューアを開いている間、敵ターンや毒ダメージなどのバックグラウンド処理が進行しない。
3. `assets.pyxres` がロード済みの場合、敵スプライトが階層に応じてパレット変更される。
4. 敵ごとに左右反転がランダムに適用され、同一戦闘中は向きが固定される。
5. 敵描画後の `pyxel.pal()` リセットにより、UIやテキストの色が崩れない。
6. `assets.pyxres` が無い場合でも `assets_loaded = False` のフォールバック描画でクラッシュしない。
7. `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装内容と一致している。

---
※ 実装担当者への指示:
まず **Phase 19.1** の詳細タスク分解を作成し、`_show_msgs` 以外に履歴へ追加すべきメッセージ経路がないか `main.py` を確認してください。その後、Phase 19.2 でログビューアのポーズ仕様を優先して実装してください。
