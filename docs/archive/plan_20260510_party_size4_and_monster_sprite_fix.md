# Implementation Plan: Phase 22 - Party Size 4 & Monster Sprite Fix

## 1. Task Overview
パーティ最大人数を「Player + NPC2」の3名から「Player + NPC3」の4名へ拡張します。あわせて、戦闘画面でモンスター画像が表示されない問題を段階的に切り分け、`assets.pyxres` ロード、`sprite_u` / `sprite_v`、透過色、パレットスワップ、フォールバック描画のどこで失敗しても原因を追える状態にします。

主目的:
- パーティ運用を最大4名へ拡張し、HUD・対象選択・敵AIターゲットが全員を扱えるようにする。
- 4枚カードHUDでも文字が重ならないよう、表示情報を短縮・安定配置する。
- `assets.pyxres` がロードできる環境では敵スプライトを確実に表示する。
- ロード失敗や座標不整合時は警告とフォールバック表示で原因を把握できるようにする。

## 2. Target Files
- `/workspaces/games/data.py`: `Party.MAX_SIZE` を 4 に変更し、追加NPCを受け入れ可能にする。
- `/workspaces/games/main.py`: 4人HUD、アイテム対象選択、敵AIターゲット、敵スプライト描画、アセットロード警告を更新する。
- `/workspaces/games/data/enemies.json`: 全敵の `sprite_u` / `sprite_v` 定義を確認し、必要なら実アセット座標へ修正する。
- `/workspaces/games/constants.py`: 必要ならHUD表示幅やデバッグフラグなどの定数を追加する。
- `/workspaces/games/docs/3. 仕様詳細.md`: パーティ構成、`Party.MAX_SIZE`、4カードHUD、敵スプライト診断仕様を更新する。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 22 のタスクと完了チェックを追加する。

## 3. Sub-Phases & Instructions

### Phase 22.1: パーティ最大人数の4名化
1. **`Party.MAX_SIZE` 更新**:
   - `data.py` の `Party.MAX_SIZE = 3` を `4` に変更する。
   - `Party.add()` の上限判定は `MAX_SIZE` 参照のまま維持する。
2. **募集・雇用フロー確認**:
   - Guild / Hire などで `party.add(npc)` を使っている箇所を確認する。
   - 画面上の「満員」判定やメッセージが固定値 `3` を参照していないか検索し、`Party.MAX_SIZE` または `len(self.party.members)` 基準へ統一する。
3. **パーティメンバー参照の安全化**:
   - `self.party.members[0..2]` のような固定インデックス参照があれば、ループまたは `enumerate(self.party.members)` に変更する。
   - 空スロット表示は `for i in range(self.party.MAX_SIZE)` を基準にする。

### Phase 22.2: 4カードHUDレイアウト
1. **`draw_status` のカード数変更**:
   - 現在の `card_w = SCREEN_W // 3` を `SCREEN_W // 4` 基準へ変更する。
   - `for i in range(4)` または `range(self.party.MAX_SIZE)` で4枚分のカードを描画する。
2. **カード描画ヘルパーの調整**:
   - `_draw_party_card(member, x, y, w, h, role, border_col)` がある場合は、4人幅に合わせて短縮ロジックを見直す。
   - ヘルパーがない場合は追加し、`draw_status` の肥大化を避ける。
3. **表示優先度**:
   - 必須: 名前、`[REAR]` / `[FRONT]`、HPバー + 数値、MPバー + 数値、状態異常タグ。
   - 装備表示は幅に応じて短縮する。例: `W:Dag` / `A:Lth` のように 3〜5文字程度へ圧縮する。
   - 文字が重なる場合は、装備名をさらに短縮し、アクセサリー表示は省略してよい。
4. **安定寸法**:
   - バー幅、カード高さ、テキスト行間を固定し、HP/MPの桁数増加でレイアウトが崩れないようにする。
   - 4人未満の場合、空カードは `-- Empty --` または `Empty` を灰色で表示する。
5. **ポップアップ座標**:
   - `_party_card_popup_pos(target)` がある場合は、4カード配置に合わせて index 0〜3 の座標を返す。
   - 対象が見つからない場合は画面中央またはプレイヤーカード座標へフォールバックする。

### Phase 22.3: 4人対応の戦闘・対象選択
1. **敵AIターゲット確認**:
   - `_get_enemy_target` または同等処理で `self.party.alive` / `self.party.members` を使っているか確認する。
   - 固定で Player / NPC2名のみを候補にしている場合は、4人全員の生存メンバーを候補にする。
   - `normal` AI は生存メンバーからランダム、`ranged` はAGI最大、`support` はHP最少など、既存仕様を4人にも適用する。
2. **アイテム使用対象選択**:
   - `STATE_INV_TARGET_SELECT` の対象リストが `self.party.members` から生成されることを確認する。
   - `inv_target_idx` の上下移動・clamp・決定処理を `len(targets)` 基準にし、4人目を選択できるようにする。
   - UI描画も4行分を収め、無効対象の色分けを維持する。
3. **NPCコマンド・装備管理**:
   - 固有NPCコマンド選択、NPC装備管理、Revive、宿屋回復など、NPC一覧を出す画面が2人固定になっていないか確認する。
   - 可能な限り `self.party.npcs` または `self.party.members[1:]` のループへ統一する。

### Phase 22.4: モンスターアセットロード診断
1. **ロード処理確認**:
   - `App.__init__` で `pyxel.load("assets.pyxres")` が実行され、成功時に `self.assets_loaded = True` になることを確認する。
   - ファイルパスは実行ディレクトリ基準で問題ないか確認する。必要なら `os.path.exists("assets.pyxres")` 等で事前確認を入れる。
2. **失敗時警告**:
   - `except Exception as e:` で握りつぶすだけにせず、`print(f"[WARN] assets.pyxres load failed: {e}")` のようなコンソール警告を出す。
   - ゲーム内表示文字列ではないため、警告文は開発者向けでよい。ただしASCIIに保つ。
3. **デバッグフラグ**:
   - 必要なら `self.debug_sprite_log_once = set()` のような一度だけ出すログ管理を追加する。
   - 毎フレーム大量にprintしない。

### Phase 22.5: スプライト座標・透過色の検証
1. **`enemies.json` の座標確認**:
   - 全敵に `sprite_u` / `sprite_v` が定義されているか確認する。
   - 値は Image Bank 0 内の32x32スプライト左上座標として扱う。
   - `sprite_u` / `sprite_v` が未定義または範囲外の場合はフォールバック描画へ切り替え、警告を1回だけ出す。
2. **`pyxel.blt` 透過色確認**:
   - 現在の第8引数 `0` がスプライトの背景色であることを確認する。
   - 主要色まで透明化されている疑いがある場合は、透過色を変更するか、該当スプライト側の背景色を0に統一する。
   - コード側では定数化して `SPRITE_TRANSPARENT_COLOR = 0` のように意味を明確にしてもよい。
3. **座標ログ**:
   - 表示されない敵について `enemy.enemy_key`, `sprite_u`, `sprite_v`, `x`, `y`, `assets_loaded` を一度だけprintする。
   - ログは開発時診断用とし、常時大量出力しない。

### Phase 22.6: パレットスワップ競合排除
1. **色番号範囲の確認**:
   - `_enemy_palette_swaps(enemy)` が返す `orig` / `new` は0〜15のみとする。
   - `new` が背景色 `COL_BLACK` に偏り、敵が黒背景へ溶け込まないようにする。
2. **透明色との競合回避**:
   - 透過色 `0` に置換するパレットスワップは避ける。
   - どうしても黒系を使う場合は、輪郭や明部色を残して視認性を担保する。
3. **リセット保証**:
   - `_draw_enemy_sprite` 内で `try/finally` を使い、`pyxel.blt` の成否に関わらず最後に `pyxel.pal()` を呼ぶ。
   - フォールバック描画時もパレット状態が残らないようにする。

### Phase 22.7: フォールバック描画の保証
1. **戻り値の整理**:
   - `_draw_enemy_sprite(enemy, x, y)` は「スプライト描画できたか」を返すか、「必ず何かを描画する」責務に統一する。
   - 推奨: この関数内で `assets_loaded == False` や座標不正時も `pyxel.rect` フォールバックを描き、呼び出し元は追加描画しない。
2. **フォールバック形状**:
   - `pyxel.rect(x, y, 32, 32, color)` に加え、枠線や敵名の頭文字などを入れると、背景との区別がしやすい。
   - 色はPyxel 0〜15の範囲で、背景に溶けない色を選ぶ。
3. **座標計算検証**:
   - `_draw_battle` の敵スロット計算 (`slot_w`, `sprite_x`, `sprite_y`) が1体〜複数体で画面内に収まるか確認する。
   - フォールバックすら見えない場合は、描画座標を一度だけprintして原因を切り分ける。

### Phase 22.8: ドキュメント同期
1. **仕様詳細更新**:
   - `docs/3. 仕様詳細.md` の「1.1 パーティ構成」を `Player + NPC最大3名 = 最大4名` に変更する。
   - 「1.2 Party クラス仕様」の `MAX_SIZE` を `4` に変更する。
   - Party Card HUD を4枚カード仕様へ更新する。
   - モンスター描画診断として、アセットロード警告、座標検証、透過色、パレットリセット、フォールバック表示を追記する。
2. **開発タスク更新**:
   - `docs/4. 開発タスク.md` に Phase 22 を追加し、各サブフェーズの完了チェック欄を作成する。
3. **完了処理**:
   - 実装と確認が完了したら、この指示書を `docs/archive/` に移動する。

## 4. Constraints
- **ASCII制約**: ゲーム内表示文字列はすべてASCIIにする。HUDタグは `[REAR]`, `[FRONT]`, `Empty` などを使う。
- **Pyxel色制約**: 色番号は0〜15のみ使用する。
- **固定値排除**: パーティ人数に関わる `3` の直書きを避け、`Party.MAX_SIZE` / `len(self.party.members)` / `len(targets)` を使う。
- **UI安定性**: 4カード化で横幅が狭くなるため、名前・装備名・数値は必ず短縮し、隣カードと重ねない。
- **ログ過多防止**: スプライト診断ログは敵キー単位・原因単位で一度だけ出す。
- **パレットリセット必須**: `pyxel.pal()` のリセット漏れでUI全体の色が壊れないようにする。
- **フォールバック維持**: `assets.pyxres` が存在しない環境でも、敵の矩形フォールバックが見える状態を保つ。

## 5. Success Criteria
1. パーティに Player + NPC3 の最大4名を編成できる。
2. 探索HUDに4枚のパーティカードが表示され、HP/MP、役割タグ、状態異常、短縮装備名が枠内に収まる。
3. 敵AIのターゲット選択が4人全員の生存メンバーを候補に含める。
4. `STATE_INV_TARGET_SELECT` で4人目を選択し、消費アイテムを使用できる。
5. NPC装備管理、宿屋、Revive、固有NPCコマンドなどのNPC一覧が4人構成でも破綻しない。
6. `assets.pyxres` ロード成功時、敵スプライトが `sprite_u` / `sprite_v` に基づいて表示される。
7. アセットロード失敗・座標不正・描画不能時は警告または一度だけの診断ログが出て、フォールバック矩形が表示される。
8. パレットスワップ後に必ず `pyxel.pal()` がリセットされ、UIやテキストの色が崩れない。
9. `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装内容と一致している。

## 6. Recommended Verification
1. `python -B main.py` で起動し、assetsロード警告の有無を確認する。
2. GuildでNPCを3名まで加入できることを確認する。
3. 探索画面で4カードHUDが重ならないことを確認する。
4. 戦闘で敵スプライトまたはフォールバック矩形が表示されることを確認する。
5. Potion / Ether / Antidote の対象選択で4人目までカーソル移動できることを確認する。
6. `rg -n "MAX_SIZE = 3|SCREEN_W // 3|range\\(3\\)|NPC2|Player \\+ NPC2" .` で、4人化すべき固定値が残っていないか確認する。

---
※ 実装担当者への指示:
まず **Phase 22.1** で `Party.MAX_SIZE` と人数固定値の洗い出しを行い、次に **Phase 22.2** の4カードHUDへ進んでください。モンスター画像問題は **Phase 22.4〜22.7** の順に、ロード、座標、透過色、パレット、フォールバックを一段ずつ切り分けてください。
