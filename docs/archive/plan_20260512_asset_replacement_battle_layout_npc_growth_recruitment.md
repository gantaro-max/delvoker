# Implementation Plan: Phase 26 - Asset Replacement, Battle Centering, NPC Growth and Recruitment

## 1. Task Overview

再作成済みモンスター画像を `assets.pyxres` へ差し替え、戦闘画面で単体モンスターが右寄りに見える問題を修正する。あわせて、NPCに経験値が入らずレベルアップしない問題を修正し、探索NPCを戦闘だけでなく仲間化できる機能として完成させる。

今回の指示書は実装前の設計・タスク分解用であり、この段階ではコード変更を行わない。

主目的:
- 暗く輪郭が読みにくい、または縦に間延びしたモンスター素材を、再作成済み画像で差し替える。
- 32x32化後も輪郭・顔・特徴パーツが黒背景で読めるように変換条件を固定する。
- 1体だけの戦闘では、モンスター名・スプライト・HPバーを画面中央へ安定配置する。
- 戦闘勝利時のEXPを生存NPCにも配布し、NPCが `Status.gain_exp()` でレベルアップするようにする。
- 探索NPC接触時に即戦闘だけでなく、条件に応じてパーティ加入を選べる仲間化導線を実装する。

## 2. Target Files

- `/workspaces/games/assets/source/image2/monsters/`: 再作成済みモンスターPNGの受け入れ先。
- `/workspaces/games/assets.pyxres`: 最終的なPyxelリソース。
- `/workspaces/games/tools/convert_image2_assets.py`: モンスター差し替え変換の調整。
- `/workspaces/games/main.py`: 戦闘描画中央寄せ、EXP配布、探索NPC接触、仲間化UI/ロジック。
- `/workspaces/games/npc.py`: 必要に応じて探索NPCの種別・仲間化可否・描画名を拡張。
- `/workspaces/games/data.py`: 必要に応じて `NPCMember` 生成ヘルパー、経験値仕様、加入情報を追加。
- `/workspaces/games/constants.py`: 新規ステートや表示定数を追加する場合に更新。
- `/workspaces/games/systems/persistence.py`: 仲間化NPCを保存対象に含める場合に更新。
- `/workspaces/games/docs/3. 仕様詳細.md`: 実装後に仕様同期する。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 26 タスクを記録する。

## 3. Sub-Phases & Instructions

### Phase 26.1: 再作成モンスター画像の差し替え

1. 再作成済みPNGを `assets/source/image2/monsters/` へ配置する。
2. ファイル名は既存 `data/enemies.json` の `sprite_u` / `sprite_v` と対応する既存名を維持する。
3. 差し替え対象の例:
   - 暗く輪郭が不明瞭なモンスター。
   - 32x32変換後に縦長へ間延びして見えるモンスター。
   - 既存原本より体型比率が崩れたモンスター。
4. `tools/convert_image2_assets.py` を確認し、差し替え対象だけをBank 0の既存座標へ上書きできることを確認する。
5. 既存の壁テクスチャ、タイトル背景、エンディング背景、差し替え対象外モンスターを不用意に再生成・上書きしない。

### Phase 26.2: モンスター変換品質の補正

1. モンスター変換時、背景の `#00ff00` または透明ピクセルはPyxel色 index 0 に変換する。
2. モンスター本体の重要輪郭・顔・武器・翼・角は index 0 に沈みすぎないよう、最近色変換後に 5 / 6 / 7 / 10 / 13 など可視色が残ることを確認する。
3. 縦に間延びして見える素材は、32x32へ単純フィットするだけでなく、元画像の内容領域を検出して正方形キャンバスへセンタリングしてから縮小する。
4. 変換スクリプトに必要なら以下の前処理を追加する。
   - クロマキー背景を除外したバウンディングボックス抽出。
   - 抽出した本体領域を少し余白付きで正方形キャンバスへ配置。
   - 32x32縮小後に本体が上下左右へ偏らないよう中央揃え。
   - 暗すぎる輪郭に対する最小限の明部補正、または再作成画像側の再確認。
5. `assets.pyxres` 保存後、Bank 0 の差し替え座標だけを読み戻して、透過色と可視色数を確認する。

### Phase 26.3: 戦闘画面の単体モンスター中央寄せ

1. `_draw_battle()` の敵配置計算を確認する。
   - 現状は `slot_w = SCREEN_W // n`、`cx = slot_w // 2 + i * slot_w`、`sprite_x = cx - 16`。
   - `n == 1` のときは `cx = SCREEN_W // 2` を明示し、名前・スプライト・HPバーが同じ中心線に揃うようにする。
2. 複数体表示では既存の均等スロット配置を維持する。
3. `enemy.flip_x` による `pyxel.blt(x + 32, ..., -32, ...)` が描画位置の見た目をずらしていないか確認する。
4. スプライト本体が32x32内で左右に偏っている場合は、コードで無理に補正せず、Phase 26.2 のアセット変換で中央配置する。
5. 名前表示、HPバー、ターゲットカーソル、ダメージポップアップが単体/複数体の両方で敵中心に対応することを確認する。

### Phase 26.4: NPC経験値配布とレベルアップ修正

1. `_handle_victory(msgs, enemy)` では現在 `self.player.gain_exp(exp)` のみ実行されているため、パーティ内NPCにもEXPを配布する。
2. 配布対象は原則として `self.party.alive` の生存メンバーとする。
   - プレイヤーが生存している場合は従来通りプレイヤーにもEXPを入れる。
   - HP 0 の戦闘不能NPCにはEXPを入れない。
3. `Status.gain_exp()` は `NPCMember` でも継承済みなので、NPCごとに同じ関数を呼び出す。
4. メッセージはASCIIのみで、長くなりすぎないよう要約する。
   - 例: `Gard Level Up! Lv1 -> Lv2`
   - 複数NPCが同時に上がる場合もログが画面から溢れないよう、必要なら詳細表示を圧縮する。
5. `self.level_up_gains` が現在プレイヤー表示用に使われているため、NPCレベルアップ情報とは混同しない。
   - 推奨: `self.level_up_gains` はプレイヤー用のまま維持。
   - NPC用には `npc_level_up_msgs` または同等のローカルメッセージだけを使う。
6. 勝利画面のEXP表示はプレイヤー中心を維持してよいが、NPCレベルアップログは `msgs` に追加して確認できるようにする。

### Phase 26.5: 探索NPCの仲間化導線

1. 現在、探索NPC接触時は `self.npcs.remove(npc)` の後に必ず `_start_battle(npc.enemy_key)` している。この分岐に仲間化判定を追加する。
2. 仲間化対象と敵対対象を区別する。
   - 最初は既存 `NPC_TYPES` の一部を仲間化可能にするか、`recruitable` フラグを追加する。
   - 例: `goblin`, `skeleton` などを敵対、`porter`/`mercenary` 相当の新規タイプを仲間候補にする、など実装しやすい形を選ぶ。
3. 接触時、仲間化可能NPCなら新規ステートまたは既存ダイアログで選択肢を出す。
   - 表示文字列はASCIIのみ。
   - 例: `Recruit {name}?`, `Join`, `Fight`, `Leave`
4. パーティが満員の場合は加入できないことを表示し、戦闘するか立ち去るかの挙動を明確にする。
5. 加入成功時は `NPCMember(job_key, name, personality)` を生成して `self.party.add(member)` する。
6. 加入NPCの初期レベルは現在階層に応じて調整する。
   - 推奨: `level = max(1, min(10, self.dungeon_floor))` を基準に、必要EXPまたは直接レベルアップで同期する。
   - HP/MPは加入時に最大まで回復してよい。
7. 加入済みNPCは `self.npcs` から除去し、同じ探索NPCが戦闘として再発火しないようにする。
8. 加入を断った場合の挙動を固定する。
   - 推奨: `Leave` はそのNPCを消す。
   - `Fight` は従来通り `_start_battle(npc.enemy_key)`。

### Phase 26.6: 仲間化NPCの保存・既存機能連携

1. セーブ/ロード後に仲間化NPCが保持されるか確認する。
2. 現行の保存対象がプレイヤーメタ中心でパーティNPCを保存していない場合、`systems/persistence.py` にNPC保存を追加する。
3. 保存対象:
   - name, job key or job name mapping, personality, level, exp
   - hp, mp, max_hp, max_mp
   - str_, def_, agi, luk, mag, bonus_points
   - weapon, armor, accessory
   - skills, status_effects, is_unique
4. ロード時、旧セーブでは既存の `Gard` 初期加入フォールバックを維持する。
5. Guild昇格、NPC装備管理、Revive、宿屋、アイテム対象選択、戦闘AIが仲間化NPCにもそのまま効くことを確認する。

### Phase 26.7: Documentation Sync

1. `docs/3. 仕様詳細.md` に以下を追記・更新する。
   - モンスター画像差し替え時の変換品質ルール。
   - 戦闘画面の単体/複数体配置仕様。
   - NPCへのEXP配布とレベルアップ仕様。
   - 探索NPCの仲間化仕様。
   - 仲間化NPCの保存仕様。
2. `docs/4. 開発タスク.md` の Phase 26 を完了状態へ更新する。
3. 実装と確認が完了したら、この指示書を `docs/archive/` へ移動する。

## 4. Constraints

- ゲーム内表示文字列はASCIIのみ。
- Pyxel色番号は0〜15のみ。
- `assets.pyxres` のBank 0座標契約を壊さない。
- 差し替え対象外の素材を不用意に上書きしない。
- 戦闘画面は単体敵で中央、複数敵で均等配置を維持する。
- NPC EXP配布は死亡メンバーに入れない。
- 仲間化UIは既存の入力体系（Z/Space決定、Xキャンセル、Up/Down選択）に合わせる。

## 5. Acceptance Criteria

- 再作成済みモンスター画像が既存座標のまま `assets.pyxres` に差し替わっている。
- 32x32表示でモンスターの輪郭が黒背景上でも判別できる。
- 縦に間延びしたモンスターが、32x32内で自然な比率と中央配置になっている。
- 敵が1体だけの戦闘で、スプライト・名前・HPバーが中央に揃う。
- 複数敵戦闘の横並びレイアウトは壊れていない。
- 戦闘勝利時、生存NPCにもEXPが入り、必要EXP到達でレベルアップする。
- NPCレベルアップ時のログが表示される。
- 探索NPCのうち仲間化可能な個体は、接触時に加入選択ができる。
- パーティ満員時は加入できず、分かりやすいASCIIメッセージが出る。
- 仲間化したNPCが戦闘AI、装備管理、Revive、宿屋、アイテム対象選択で既存NPCと同様に扱われる。
- セーブ/ロード後も仲間化NPCが維持される、または旧セーブ互換のフォールバックが機能する。

## 6. Recommended Verification

1. `python -B -m py_compile main.py npc.py data.py constants.py systems/persistence.py ui/renderer_3d.py`
2. 変換スクリプトを実行し、Bank 0の差し替え対象座標を読み戻す。
3. `assets.pyxres` ロードありで各差し替えモンスターを戦闘表示する。
4. 単体敵、2体敵、3体敵の戦闘画面を確認する。
5. NPCを連れた状態で勝利し、NPCのEXP/Levelが増えることを確認する。
6. 仲間化可能NPCに接触し、Join / Fight / Leave の各分岐を確認する。
7. パーティ満員時の加入失敗を確認する。
8. セーブ/ロード後に仲間化NPCの状態が維持されることを確認する。

