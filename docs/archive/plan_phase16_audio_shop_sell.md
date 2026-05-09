# Implementation Plan: Phase 16 - Audio Mute & Shop Sell Feature

## 1. Task Overview
BGMを一時的に無効化し、ゲームプレイ中の聴覚的フィードバックを効果音に集中させます。また、ショップでプレイヤーがアイテムを売却できる機能を追加し、経済システムを強化します。

## 2. Target Files
- `/workspaces/games/main.py`
- `/workspaces/games/constants.py`
- `/workspaces/games/docs/3. 仕様詳細.md`
- `/workspaces/games/docs/4. 開発タスク.md`
- `/workspaces/games/systems/persistence.py` (セーブデータ互換性のため)

## 3. Sub-Phases & Instructions

### Phase 16.1: BGMの一時停止とIssue追記
1. **BGMコメントアウト**: `main.py` の `_init_audio` メソッド内で、`pyxel.musics[0].set([3], [], [], [])` などの `pyxel.musics` の呼び出し行をすべてコメントアウトします。これにより、効果音は鳴りつつBGMは再生されなくなります。
2. **Issue追記**: `docs/4. 開発タスク.md` の "Future Issues" セクションに、"Issue #03: BGMの差し替えと最終調整" を追記します。

### Phase 16.2: ショップ売却機能の実装
1. **コマンド追加**: `constants.py` に `SHOP_COMMANDS = ["Buy", "Sell"]` を新規定義します。
2. **ショップモード管理**: `main.py` の `App.__init__` に `self.shop_mode = "buy"` を追加。`_upd_shop` で `pyxel.KEY_LEFT` / `pyxel.KEY_RIGHT` を押した際に `self.shop_mode` を `"buy"` と `"sell"` で切り替えるロジックを実装します。
3. **売却UIの実装**: `main.py` の `_draw_shop` を修正し、`self.shop_mode == "sell"` の場合に以下のUIを表示します。
   - プレイヤーのインベントリ (`self.player.inventory`) を表示します。
   - 選択中のアイテムにカーソル (`>`) を表示します。
   - アイテム名と売却価格 (`int(item.value * 0.3)`) を表示します。
   - 装備中のアイテム (`item is self.player.weapon or item is self.player.armor`) は売却不可とし、灰色で表示します。
   - 売却可能なアイテムがない場合は「-- Empty --」と表示します。
4. **売却ロジックの実装**: `main.py` の `_upd_shop` を修正し、`self.shop_mode == "sell"` かつ `pyxel.KEY_Z` が押された際に以下の処理を行います。
   - 選択中のアイテムが装備中でないか、インベントリに存在するかを確認します。
   - 売却価格 (`int(item.value * 0.3)`) をプレイヤーのゴールドに加算します。
   - インベントリからアイテムを削除します。
   - `self.shop_idx` を調整し、リストの範囲外にならないようにします。
5. **ドキュメント更新**: `docs/3. 仕様詳細.md` のショップセクションに、アイテム売却機能の仕様（売却価格、操作方法、UIなど）を追記します。

### Phase 16.3: ドキュメント同期
1. **タスク更新**: `docs/4. 開発タスク.md` の Phase 15 を完了とし、Phase 16 を「進行中」に更新します。

## 4. Constraints
- **ASCII制約**: 表示文字列は引き続きASCIIのみ。
- **経済バランス**: 売却価格はアイテムの `value` の **3割** (`int(item.value * 0.3)`) とします。
- **セーブデータ互換性**: `systems/persistence.py` の `save_game` / `load_game` は変更不要です。

## 5. Success Criteria
1. ゲーム起動中、効果音は再生されるがBGMは再生されない。
2. ショップ画面で `pyxel.KEY_LEFT` / `pyxel.KEY_RIGHT` を押すことで「Buy」と「Sell」モードを切り替えられる。
3. 「Sell」モードでインベントリのアイテムを選択し、売却（ゴールド獲得、アイテム消滅）できる。
4. 装備中のアイテムは売却できない。
5. `docs/4. 開発タスク.md` にBGM差し替えに関するIssueが追記されている。

---
※ Claude Code への追加指示：
まずは Phase 16.1 の BGM コメントアウトから着手してください。

### Phase 16.3: ドキュメント同期
1. `docs/3. 仕様詳細.md` に売却機能の仕様を追記します。
2. `docs/4. 開発タスク.md` の進捗を更新します。