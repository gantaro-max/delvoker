# Implementation Plan: Dungeon NPC Sprites, Name Input, and Rich Backgrounds

## 1. Consistency Review

GEMINI案は方向性として妥当です。ただし、現行コードに合わせて以下を補正して実装します。

- `draw_3d_view` の引数漏れは現行 `main.py` では既に修正済み。`_draw_3d_view(self.wall_at, self.assets_loaded, self.dungeon_floor)` を維持する。
- `npc.py` の `NPC.draw()` は現状 `assets_loaded` を受け取らないため、`main.py::draw_npcs()` から渡すようにシグネチャを変更する。
- `NPC.draw()` から `ENEMY_CATALOG` を参照する案は妥当。`NPC_TYPES[npc_type_key]["enemy_key"]` と `data/enemies.json` の `sprite_u` / `sprite_v` は既存仕様と整合している。
- Pyxel `blt` はスケーリング非対応なので、単純に常時32x32で描くと遠距離NPCが大きすぎる。初期実装では手動の最近傍スケール描画ヘルパーを追加し、既存の矩形サイズ `nw` / `nh` に近い寸法でスプライトを表示する。
- New Game のフローは `STATE_NAME_INPUT` へ遷移し、Continue は保存済みデータをロードして `STATE_TOWN` へ遷移する。Continue を `STATE_JOB_SELECT` や名前入力へ送らない。
- 職業選択画面は New Game ではスキップし、`porter` 固定で開始する。ただし既存の `STATE_JOB_SELECT` は互換・将来のジョブ解放UI用に残す。
- 背景画像は Bank 1 = Title、Bank 2 = Ending とし、Bank 0 のモンスター・壁テクスチャと分離する。

## 2. Task Overview

ダンジョン探索画面のNPC表示を単色矩形からモンスタースプライト表示へ変更し、New Game 時に名前入力を挟んで Porter 固定で開始するフローへ刷新します。あわせてタイトル・エンディング背景を `assets.pyxres` の別Bankへ導入できるよう、制作・変換・描画仕様を定義します。

主目的:
- 探索中の徘徊NPCを戦闘用モンスタースプライトで表示し、遭遇前に敵種を判別可能にする。
- `assets.pyxres` 未ロード時は従来の単色矩形フォールバックを維持する。
- New Game → 名前入力 → Porter固定開始 → Town のフローに変更する。
- タイトル・エンディング画面に全画面背景画像を敷けるようにする。

## 3. Target Files

- `/workspaces/games/constants.py`: `STATE_NAME_INPUT` とBGMゾーンを追加する。
- `/workspaces/games/main.py`: タイトル遷移、名前入力更新・描画、Porter固定開始、背景描画、NPC描画呼び出しを更新する。
- `/workspaces/games/npc.py`: `NPC.draw()` をスプライト対応にする。
- `/workspaces/games/systems/persistence.py`: 必要なら `player_name` を保存・読込対象に追加する。
- `/workspaces/games/assets.pyxres`: Bank 1 / Bank 2 に背景画像を追加する。
- `/workspaces/games/docs/3. 仕様詳細.md`: 画面遷移、探索NPC描画、背景アセット仕様を更新する。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 24 のタスクと完了チェックを追加する。

## 4. Phase 24.1: Dungeon NPC Sprite Rendering

1. **`NPC.draw()` シグネチャ変更**
   - 変更前: `draw(self, px, py, player_dir, is_wall_fn)`
   - 変更後: `draw(self, px, py, player_dir, is_wall_fn, assets_loaded=False)`
   - 既存呼び出し互換のため `assets_loaded=False` をデフォルトにする。

2. **`ENEMY_CATALOG` 参照**
   - `npc.py` で `from data import NPC_TYPES, ENEMY_CATALOG` に変更する。
   - `self.enemy_key` から `edef = ENEMY_CATALOG.get(self.enemy_key)` を取得する。
   - `edef.sprite_u` / `edef.sprite_v` がない、または `assets_loaded == False` の場合は従来の `pyxel.rect(nx, ny, nw, nh, self.color)` にフォールバックする。

3. **距離別スプライトサイズ**
   - 既存の `nw` / `nh` をスプライト表示サイズとして利用する。
   - `draw_scaled_sprite(src_u, src_v, src_w, src_h, dst_x, dst_y, dst_w, dst_h, transparent=0)` のような小ヘルパーを `npc.py` に追加する。
   - 最近傍で `pyxel.images[0].pget()` し、透明色0以外を `pyxel.pset()` または小矩形で描画する。
   - 表示サイズは最小 `8x8` 程度を確保し、遠距離でも敵が潰れすぎないようにする。

4. **描画座標**
   - 既存の中心座標 `cx`, `cy` を維持する。
   - `dst_x = cx - sprite_w // 2`
   - `dst_y = cy - sprite_h // 2 + fh // 10`
   - ラベルは従来通り `self.name[:6]` を表示し、スプライト上部に重なりすぎる場合は `dst_y - 8` を基準にする。

5. **呼び出し元更新**
   - `main.py::draw_npcs()` を `npc.draw(self.px, self.py, self.dir, is_wall, self.assets_loaded)` に変更する。

## 5. Phase 24.2: Name Input and Porter Start Flow

1. **ステート追加**
   - `constants.py` に `STATE_NAME_INPUT = 25` を追加する。
   - `_BGM_ZONES` に `STATE_NAME_INPUT: 0` を追加する。
   - `main.py` の constants import に `STATE_NAME_INPUT` を追加する。

2. **初期フィールド**
   - `App.__init__` に以下を追加する。
   - `self.player_name = "HERO"`
   - `self.name_input_text = "HERO"`
   - `self.name_input_cursor = 0`（画面上文字盤を採用する場合）
   - `self.unlocked_jobs = ["porter"]` は維持する。

3. **タイトル更新**
   - `_upd_title()` の New Game 分岐:
     - `self.player_name = "HERO"`
     - `self.name_input_text = "HERO"`
     - `self.unlocked_jobs = ["porter"]`
     - `self.game_cleared = False`
     - `self._set_state(STATE_NAME_INPUT)`
   - Continue 分岐:
     - `self.player = Player("porter")` など最低限のプレイヤーを作る。
     - `self.load_data()`
     - `self.party = Party(self.player)`
     - 必要なら初期NPC `Gard` を追加する。
     - `self._set_state(STATE_TOWN)`
   - New Game で `STATE_JOB_SELECT` へ遷移しない。

4. **開始処理の集約**
   - `_start_new_game(self)` を追加または整備する。
   - `self.player = Player("porter", self.player_name)` または作成後 `self.player.name = self.player_name` とする。
   - `_grant_job_skill("porter")` を呼び、Porter開始スキルを保証する。
   - `self.party = Party(self.player)`
   - 既存通り `NPCMember("warrior", "Gard", "reckless")` を加入させる。
   - `self._set_state(STATE_TOWN)`

5. **名前入力仕様**
   - ゲーム内表示文字列はASCIIのみ。
   - デフォルト名は `HERO`。
   - 入力可能文字は `A-Z`, `0-9`, `-`, `_` 程度に制限する。
   - 最大長は8文字、空欄決定時は `HERO`。
   - キーボード入力が安定して使える場合は `pyxel.input_keys` を利用する。
   - `pyxel.input_keys` が環境・バージョン差で扱いづらい場合は、画面上文字盤方式を採用する。
   - 決定: `Z` / `Space`
   - 削除: `Backspace` または `X`
   - キャンセル: 名前を `HERO` に戻してタイトルへ戻る、または `X` 長押し等の誤爆しにくい操作にする。

6. **描画**
   - `_draw_name_input()` を追加する。
   - タイトル、現在名、入力ガイド、文字盤またはキーボード入力状態を表示する。
   - 画面内テキストはすべてASCIIにする。

## 6. Phase 24.3: Rich Title and Ending Backgrounds

1. **Bank割り当て**
   - Bank 0: 既存のモンスター・壁テクスチャ。
   - Bank 1: タイトル背景 256x256。
   - Bank 2: エンディング背景 256x256。

2. **画像制作・変換**
   - AI生成画像を使う場合は、256x256で作成する。
   - Pyxel標準16色へ減色してから `assets.pyxres` に取り込む。
   - 変換はスクリプト化し、元画像PNGを `assets/source/` 等へ置く場合はドキュメント化する。
   - Bank 0 を上書きしないこと。

3. **描画実装**
   - `_draw_title()` 冒頭:
     - `if self.assets_loaded: pyxel.blt(0, 0, 1, 0, 0, 256, 256)`
     - 未ロード時は従来通り `pyxel.cls(COL_BLACK)`。
   - `_draw_ending()` 冒頭:
     - `if self.assets_loaded: pyxel.blt(0, 0, 2, 0, 0, 256, 256)`
     - 未ロード時は従来通り `pyxel.cls(COL_BLACK)`。
   - 背景上の文字は可読性確保のため、必要に応じて黒の影文字または半透明風の単色帯を使う。ただしUIカード過多にはしない。

4. **段階導入**
   - 背景画像のAI生成・取り込みが未完了でも、Bank 1/2 が空なら黒背景と同等に見えるだけでクラッシュしないこと。
   - 先にコード側の描画対応を入れ、背景制作は別コミット・別作業でもよい。

## 7. Phase 24.4: Persistence and Compatibility

1. **Player名保存**
   - 現行 `systems/persistence.py` は `player.name` を保存していない。
   - 名前入力を永続化するなら `save_game()` に `"player_name": player.name` を追加する。
   - `load_data()` で `self.player.name = data.get("player_name", "HERO")` を復元する。

2. **ジョブ保存方針**
   - 現行セーブはジョブ自体を保存していないため、Continue時は `Player("porter")` を基準に復元する。
   - 将来ジョブ選択を復活させる場合は `"player_job"` 保存を追加する。
   - 今回は New Game が Porter固定なので、最小実装は `porter` 固定でよい。

3. **既存セーブ互換**
   - `player_name` がない旧セーブは `"HERO"` で復元する。
   - `unlocked_jobs` が旧値の場合でも、New Game は必ず `["porter"]` に戻す。

## 8. Phase 24.5: Documentation Sync

1. `docs/3. 仕様詳細.md`
   - 画面遷移フローを `New Game -> STATE_NAME_INPUT -> STATE_TOWN` に更新する。
   - `Continue -> STATE_TOWN` に更新する。
   - `STATE_JOB_SELECT` は互換・将来用ステートとして残ることを明記する。
   - 探索NPCスプライト描画仕様を追加する。
   - Bank 1 / Bank 2 背景画像仕様を追加する。

2. `docs/4. 開発タスク.md`
   - Phase 24 として各サブフェーズの完了チェックを追加する。

3. 完了後
   - 本指示書を `docs/archive/` に移動する。

## 9. Constraints

- ゲーム内表示テキストはASCIIのみ。
- Pyxel色番号は0-15のみ。
- Bank 0 の既存モンスター・壁テクスチャを壊さない。
- `assets.pyxres` 未ロード時でも探索・タイトル・エンディングが描画できる。
- 既存の `STATE_JOB_SELECT` は削除しない。New Gameからは使わないだけにする。
- ユーザー作業中の差分がある場合は、該当ファイルを編集する前に差分を確認し、無関係な変更を戻さない。

## 10. Success Criteria

1. ダンジョン探索中のNPCが、`assets_loaded=True` かつ `ENEMY_CATALOG` 座標ありの場合にモンスタースプライトで表示される。
2. 距離に応じてスプライト表示サイズが変わり、遠距離でも過大表示にならない。
3. `assets.pyxres` 未ロード時や座標不備時は従来の単色矩形表示にフォールバックする。
4. New Game 選択後に名前入力画面へ遷移する。
5. 名前決定後、プレイヤー名が反映された Porter として Town から開始する。
6. Continue は名前入力・職業選択を挟まず、保存データを復元して Town へ遷移する。
7. タイトル画面で Bank 1 背景、エンディング画面で Bank 2 背景を描画できる。
8. 旧セーブデータでもクラッシュせず、名前未保存時は `HERO` にフォールバックする。
9. `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装内容と一致している。

## 11. Recommended Verification

1. `python -B -m py_compile main.py npc.py constants.py systems/persistence.py ui/renderer_3d.py`
2. `python -B main.py` で起動し、New Game → 名前入力 → Town の遷移を確認する。
3. 名前を変更して開始し、HUD・戦闘ログ・エンディング表示に反映されることを確認する。
4. Continue が直接 Town へ遷移し、旧セーブでもクラッシュしないことを確認する。
5. ダンジョンでNPCを視界正面に置き、距離別のスプライト表示を確認する。
6. `assets.pyxres` を一時的に読み込めない状態にして、NPCが矩形フォールバックで表示されることを確認する。
7. タイトル・エンディングで背景描画後も文字が読めることを確認する。

