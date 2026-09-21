# Implementation Plan: Phase 40 - Public Release Preparation

## 1. Task Overview
リポジトリを GitHub で Public 公開するための整備を行います。外部レビューで指摘された10項目を対象とし、「初見の閲覧者がREADMEだけでゲーム内容を理解し、手元で起動できる」状態をゴールとします。

主目的:
- リポジトリ名・README・スクリーンショットで、プロジェクトの第一印象を成立させる。
- `__pycache__` などの生成物を追跡対象から外し、`.gitignore` で再混入を防ぐ。
- ドキュメントとコードの乖離（パーティ人数）を解消する。
- 最低限の自動テストと CI を用意し、外部から見て「壊れていないことが確認できる」状態にする。
- `main.py` の肥大化を隠さず「今後の改善」として明記する。

注意: ゲームロジックの仕様変更は本フェーズの対象外です。既存の挙動は変えません。

## 2. Target Files
- `/workspaces/games/.gitignore`: 新規作成。生成物・キャッシュ・セーブデータを除外する。
- `/workspaces/games/README.md`: 新規作成。公開時の入口となるドキュメント。
- `/workspaces/games/requirements.txt` / `requirements-dev.txt`: 新規作成。依存関係を明示する。
- `/workspaces/games/pytest.ini`: 新規作成。テストパスの設定。
- `/workspaces/games/tests/`: 新規作成。`conftest.py` と各テストモジュール。
- `/workspaces/games/tools/capture_screenshots.py`: 新規作成。READMEスクリーンショットの無人再生成スクリプト。
- `/workspaces/games/docs/screenshots/`: 新規作成。README用スクリーンショット4枚の置き場。
- `/workspaces/games/.github/workflows/ci.yml`: 新規作成。テストと起動スモークの CI。
- `/workspaces/games/docs/1. 機能要件.md`: L35 のパーティ人数を実装（4名）に同期する。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 40 のタスクと完了チェックを追加する。

## 3. Sub-Phases & Instructions

### Phase 40.1: リポジトリ改名（games → delvoker）
1. **GitHub側の改名**:
   - GitHub の Settings > General > Repository name で `games` → `delvoker` に変更する。GitHubは旧URLからのリダイレクトを維持するため、既存クローンは即座には壊れない。
   - 改名後、ローカルで `git remote set-url origin https://github.com/gantaro-max/delvoker.git` を実行する。
2. **ローカルパスの影響確認**:
   - 調査済み: `/workspaces/games` をハードコードしているのは `docs/archive/` 配下の26ファイルのみで、すべて過去の作業記録である。**これらは書き換えない**（当時の記録として保持する）。
   - `.devcontainer/devcontainer.json` と `Dockerfile` に絶対パスの記述はないため、ディレクトリ名変更による修正は不要。
3. **作業ディレクトリ名**:
   - ローカルの `/workspaces/games` ディレクトリ名変更は devcontainer の再作成を伴うため、本フェーズでは**必須としない**。GitHub側のリポジトリ名が `delvoker` になっていれば公開要件は満たす。

### Phase 40.2: .gitignore 作成と生成物の追跡解除
1. **`.gitignore` 新規作成**:
   - 以下のカテゴリを含める。
     - Python: `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`
     - テスト・ツール: `.pytest_cache/`, `.coverage`
     - Pyxel実行時生成物: `delvoker_save.json`, `pyxel-*.png`, `pyxel-*.gif`, `*.pyxapp`
     - エディタ・OS: `.vscode/`, `.idea/`, `.DS_Store`
   - セーブファイル名は `constants.py` の `SAVE_FILE = "delvoker_save.json"` に一致させること。`savedata.json` ではない。
2. **追跡済み生成物の解除**:
   - 現在16個の `.pyc` が追跡されている。内訳は ルート直下9 / `logic/` 2 / `systems/` 2 / `tools/` 1 / `ui/` 2。
   - `git rm -r --cached __pycache__ logic/__pycache__ systems/__pycache__ tools/__pycache__ ui/__pycache__` で追跡解除する。
   - ルート直下の `pyxel-20260515-100354.png`（Pyxelのスクリーンショット機能が吐いた残骸）も `git rm --cached` で追跡解除し、実ファイルを削除する。
3. **確認**:
   - `git ls-files | grep -c pycache` が `0` になること。

### Phase 40.3: 機能要件のパーティ人数同期
1. **修正箇所**:
   - `docs/1. 機能要件.md` L35 の「プレイヤー1名 + 臨時NPC最大2名、合計最大3名」を「プレイヤー1名 + 臨時NPC最大3名、合計最大4名（`Party.MAX_SIZE = 4`）」に変更する。
2. **他ドキュメントの確認（調査済み、修正不要）**:
   - `docs/3. 仕様詳細.md` は L16「パーティ合計 4」/ L27「`MAX_SIZE` = 4」で既に同期済み。
   - `docs/4. 開発タスク.md` L451 の「3名分」は Phase 22 以前の作業ログであり、当時の記録として**書き換えない**。
   - 実装の正は `data.py` の `Party.MAX_SIZE = 4`。

### Phase 40.4: スクリーンショット生成スクリプト
`docs/archive/*_preview.png` は3Dビュー単体のレンダリング確認用であり、HUDもUIも写っていないためREADMEには使えません。ゲーム画面を無人で取得するスクリプトを新規に作成します。

1. **`tools/capture_screenshots.py` 新規作成**:
   - 起動方法は `Xvfb :99 -screen 0 640x480x24 &` の後に `DISPLAY=:99 python tools/capture_screenshots.py`。devcontainerには `xvfb` が導入済み。
   - `xvfb-run` はこの環境に `xauth` が無いため使えない。`Xvfb` を直接起動して `DISPLAY` を渡すこと。
2. **メインループを回さずに描画する手法**:
   - `import main` の**前に** `pyxel.run = lambda update, draw: _loop.update(update=update, draw=draw)` で差し替える。これで `App()` がゲーム状態を完全に構築しつつ、ブロッキングするメインループに入らない。
   - シーンの切り替えは `app._set_state(STATE_XXX)` を使う。`self.state` への直接代入では**ウィンドウの open 処理が走らず画面が真っ黒になる**（`_set_state` 内で `town_win.open()` 等を呼んでいるため）。
   - `Window` は `_ANIM_STEP = 0.15` の開閉アニメを持ち、`ready` になるまで中身を描画しない。`draw()` を呼ぶ前に、`town_win` / `status_win` / `sub_win` / `battle_win` / `inv_win` / `inv_action_win` / `shop_win` の `update()` を10フレーム分回してアニメを完了させること。
   - `random.seed(7)` を先頭で固定し、毎回同じダンジョン配置・同じ敵が出るようにする。
3. **PNG出力**:
   - Pyxelにはフレームバッファを任意パスへ保存するAPIが無い。また本プロジェクトは Pillow / numpy に依存していないため、**標準ライブラリの `zlib` + `struct` でPNGを自前エンコードする**。
   - 手順: `pyxel.screen.pget(x, y)` で色番号(0-15)を取得 → `pyxel.colors[i]` で24bit RGBへ変換 → 各行の先頭にフィルタバイト `0x00` を付けて連結 → `zlib.compress` → IHDR / IDAT / IEND チャンクを組み立てる。
   - 画面は256x256と小さいため、横方向は画素を2回、縦方向は行を2回繰り返してスケール2倍で出力する。
4. **撮影する4シーン**（`docs/screenshots/` へ出力）:
   - `01_title.png`: `STATE_TITLE`
   - `02_town.png`: `STATE_TOWN`（`app.player.gold` に適当な値を入れて所持金欄を空に見せない）
   - `03_dungeon.png`: `app._enter_dungeon_fresh()` の後に `STATE_DUNGEON`（4枚のパーティカードHUDが写る）
   - `04_battle.png`: `app._start_battle()` の後に `STATE_BATTLE_CMD`（敵スプライトとコマンドウィンドウが写る）
   - インベントリ画面は初期状態が空で情報量が無いため採用しない。
5. **スモークテストとしての価値**:
   - このスクリプトは `main.py` の import と `App.__init__` を実際に通すため、CI から実行すれば起動時クラッシュの検出器になる。Phase 40.8 で利用する。

### Phase 40.5: pytest によるテスト追加
1. **テスト対象の選定（調査済み）**:
   - `data.py` / `constants.py` / `logic/map_generator.py` / `systems/persistence.py` は **pyxel を import していない**ため、ディスプレイ無しで素直にテストできる。ここを対象にする。
   - `main.py` と `ui/renderer_3d.py` は pyxel 依存。ユニットテストの対象外とし、Phase 40.8 の起動スモークでカバーする。
2. **`tests/conftest.py`**:
   - プロジェクトルートを `sys.path` に挿入するだけ。パッケージ化はしない。
3. **`tests/test_data.py`**:
   - JSONカタログ（`JOBS` / `ITEM_CATALOG` / `ENEMY_CATALOG`）が空でないこと。
   - **全アイテム名・全敵名が ASCII であること**。AGENTS.md のASCII制約をテストで担保する価値が高い。
   - 全ジョブで `Status` が構築でき、`hp == max_hp` で始まること。
   - 敵の `weaknesses` / `resistances` に未知の属性が混入していないこと（許容は `fire` / `ice` / `poison` / `holy`）。
   - `ATTR_AFFINITY` が3すくみの閉じた循環であること。
   - `gain_exp()` のレベルアップ：`bonus_points` が +3 されること、HP全回復すること、経験値超過時に多段レベルアップすること。
   - `total_def` に防具の `def_bonus` が乗ること。`resistances` が装備防具の属性を含むこと。
   - `Party.add()` が `MAX_SIZE` で打ち止めになること、`is_wiped_out` が全員HP0のときだけ真になること。
   - `NPCMember` が未知の personality を `normal` にフォールバックすること。
   - エンチャント生成物の `label()` が ASCII であること（seedを変えて複数回）。
4. **`tests/test_map_generator.py`**:
   - seed を 0〜19 で振り、以下の不変条件を検証する。
     - 外周がすべて `TILE_WALL` であること。
     - `start_x` / `start_y` が壁でないこと、階段がちょうど1つ存在すること。
     - **階段が開始地点から到達可能であること**（flood fill）。到達不能フロアはソフトロックになるため最重要。
     - B1F（`current_floor=1`）に `TILE_LOCKED_DOOR` と `TILE_MERCHANT` が出現しないこと。
     - 鍵扉が置かれたフロアでは `key_chest_pos` が設定され、その座標が `TILE_CHEST` かつ到達可能であること。
   - flood fill では `TILE_WALL` のみを障害物として扱う。鍵扉は鍵で開けられるため通過可能とみなす（`Map.is_wall()` とは判定基準が異なる点に注意。`is_wall()` は泉・商人も壁扱いにしている）。
5. **`tests/test_persistence.py`**:
   - セーブ破損は直接プレイヤーの損失になるため、**全アイテムサブクラスを個別にラウンドトリップ**する: `WeaponItem` / `ArmorItem` / `ConsumableItem` / `AccessoryItem` / `GrimoireItem` / `EnchantedWeapon` / `EnchantedArmor`。
   - エンチャント品は prefix / suffix から再構築されるため、`label()` の一致で検証するのが最も取りこぼしが少ない。
   - `kind` を持たないペイロードが consumable として読めること（旧セーブ互換）。
   - `NPCMember` のラウンドトリップ：レベル・最大HP・`is_unique`・装備・スキルが保たれること。
   - `hp` が `max_hp` を超える値で保存されていても、ロード時に clamp されること。
   - `save_game()` → `load_game()` の全項目一致。プレイヤーは `main.py` の `Player` クラス（pyxel依存）を使わず、`types.SimpleNamespace` で `name` / `gold` / `warehouse` / `warehouse_max` / `perm_stats` を持つスタブを組む。
   - セーブファイルが ASCII のみであること（`save_game` は `encoding="ascii"` で書き出すため、非ASCIIが混ざると保存時に落ちる）。
   - ファイル不在・JSON破損時に `load_game()` が空dictを返すこと。
   - 一時ファイルは pytest の `tmp_path` フィクスチャを使い、リポジトリを汚さないこと。
6. **設定ファイル**:
   - `pytest.ini` に `testpaths = tests` を設定する。
   - `requirements.txt` に `pyxel>=2.9`（現行環境は 2.9.9）、`requirements-dev.txt` に `-r requirements.txt` と `pytest>=8.0` を記述する。

### Phase 40.6: README.md 作成
公開リポジトリの入口です。以下の構成で作成します。日本語で記述してよい（ゲーム内文字列ではないためASCII制約の対象外）。

1. **タイトルと1〜2行の要約**:
   - 「Pyxel製のレトロスタイル・ダンジョン探索RPG」であることと、「プレイヤーは戦えないポーター（荷物持ち）で、NPCを管理・支援して迷宮を攻略する」というコンセプトの独自性を冒頭に置く。
2. **スクリーンショット**:
   - Phase 40.4 の4枚を `docs/screenshots/` から参照する。2x2のテーブルに並べるとREADMEが縦に伸びず読みやすい。
   - 各画像に「タイトル」「街（Solace Town）」「ダンジョン探索」「戦闘」のキャプションを付ける。
3. **特徴**:
   - ポーター視点の戦闘（Aid / Encourage 中心の非戦闘員）、性格AIを持つ臨時NPC、ハクスラ的なランダムエンチャント（normal〜genesis）、部位破壊、手続き的マップ生成、全滅時のロストと遺品回収。
   - 箇条書き6項目程度に抑え、詳細は `docs/` へのリンクで逃がす。
4. **起動方法**:
   ```
   git clone https://github.com/gantaro-max/delvoker.git
   cd delvoker
   pip install -r requirements.txt
   python main.py
   ```
   - 動作環境として Python 3.11 以上 / Pyxel 2.9 以上を明記する。
   - Linux では SDL2 系のパッケージが必要な場合がある旨を1行添える（`.devcontainer/Dockerfile` の `libsdl2-2.0-0` / `libsdl2-image-2.0-0` / `libgl1` / `libegl1` が参考になる）。
   - VS Code Dev Container が同梱されている旨も記載する。
5. **操作方法**:
   - 矢印キー: 移動 / 選択、`Z` または `Space`: 決定、`X`: キャンセル、`T`: 街へ、`I`: アイテム、`S`: スキル、`Q`: 終了。
   - ゲーム内のフッター表示と食い違わないよう、実装を確認してから書くこと。
6. **開発の進め方（AIとの役割分担）**:
   - 本プロジェクトが AI エージェント併用で開発されている点を明記する。誠実さの担保であると同時に、このリポジトリ自体の面白さになる部分。
   - Codex（メインエージェント）: 要件定義からの指示書作成、実装、ドキュメント同期・アーカイブ。
   - Claude（レビュアー）: 実装済みコードのレビュー、リファクタリング、難易度の高いバグの原因究明。
   - 人間: 要件出し、仕様の意思決定、最終的な受け入れ判断。
   - ドキュメント駆動（`docs/` がSSOT、`docs/instructions/` に指示書を作り完了後 `docs/archive/` へ移動）というワークフローと、`AGENTS.md` / `CLAUDE.md` へのリンクを添える。
7. **テストの実行方法**:
   - `pip install -r requirements-dev.txt` と `pytest` の2行。
8. **プロジェクト構成**:
   - `main.py` / `data.py` / `constants.py` / `logic/` / `systems/` / `ui/` / `data/` / `assets/` / `docs/` / `tests/` / `tools/` を1行ずつ説明する。
9. **今後の改善（Known Issues / Roadmap）**:
   - **`main.py` が3,251行に肥大化しており、状態ごとの `update` / `draw` がすべて集中している**点を正直に記載する。`logic/` `systems/` `ui/` への分割を進行中であること、状態ハンドラのモジュール分割が次の課題であることを書く。
   - BGMが `main.py` 内で定義のみでミュートされている（`pyxel.musics[...]` がコメントアウト）点も、既知の未完了事項として挙げてよい。
   - 隠すより明示するほうが、レビュワーからの印象は良い。
10. **ライセンス**:
    - ライセンスの方針はユーザーの判断事項。未定の場合はこの節を作らず、確認してから追記する。アセットの出自にも注意すること。

### Phase 40.7: main.py 分割の扱い
1. **本フェーズでは分割しない**:
   - 公開作業と大規模リファクタを同時に行うと、退行時の切り分けが困難になる。README の「今後の改善」への明記（Phase 40.6-9）をもって本フェーズの対応とする。
2. **将来の分割方針だけ記録する**:
   - `docs/4. 開発タスク.md` に、次フェーズ候補として以下を記載する。
     - 状態ごとの `update_*` / `draw_*` を `states/` 配下のモジュールへ移す。
     - 戦闘進行（ダメージ計算、行動順、AI）を `logic/battle.py` として切り出す。
     - ショップ / ギルド / マイホームの各メニューを `ui/` 配下へ移す。
   - 着手は公開後、CIが動く状態になってから行う。テストが無い状態での大規模分割は避ける。

### Phase 40.8: GitHub Actions 追加
1. **`.github/workflows/ci.yml` 新規作成**:
   - トリガーは `push` と `pull_request`。
2. **test ジョブ**:
   - `runs-on: ubuntu-latest`、`strategy.matrix.python-version: ["3.11", "3.12"]`。
   - `pip install -r requirements-dev.txt` → `pytest`。
   - Phase 40.5 のテストは pyxel を import しないため、ディスプレイ関連のセットアップは不要。
3. **smoke ジョブ**:
   - `main.py` の起動を検証する。Pyxelの実行には SDL2 と仮想ディスプレイが必要。
   - `sudo apt-get install -y libsdl2-2.0-0 libsdl2-image-2.0-0 libgl1 libegl1 xvfb` を入れる。
   - `Xvfb :99 -screen 0 640x480x24 &` を起動し `DISPLAY=:99` を設定したうえで `python tools/capture_screenshots.py` を実行する。これが成功すれば import / `App.__init__` / 各シーンの `draw()` がすべて通ったことになる。
   - 音声デバイスが無いため `Failed to initialize audio device` が stderr に出るが、Pyxelはこれで異常終了しない。エラー扱いにしないこと。
   - 生成されたスクリーンショットを `actions/upload-artifact` で成果物として上げておくと、描画の退行を目視確認できる。
4. **README バッジ**:
   - CI の status badge を README 冒頭に追加する。

### Phase 40.9: ドキュメント同期とアーカイブ
1. **開発タスク更新**:
   - `docs/4. 開発タスク.md` に `## Phase 40: Public Release Preparation` を追加し、40.1〜40.8 の完了チェック欄を作る。
   - Phase 40.7 の将来分割方針も、次フェーズ候補としてここに記録する。
2. **完了処理**:
   - 実装と確認が完了したら、本指示書を `docs/archive/plan_20260921_public_release_prep.md` へ移動する。

## 4. Constraints
- **挙動を変えない**: 本フェーズはゲームロジックを一切変更しない。テストは現在の実装を正として書き、テストが落ちた場合は原因を報告してから対処方針を判断する（テストに合わせて実装を書き換えない）。
- **ASCII制約の適用範囲**: ゲーム内表示文字列はASCIIのみ。README・指示書・テストのdocstringは日本語可。
- **Pyxel色制約**: 色番号は0〜15のみ（本フェーズで新規描画コードは書かないが、スクリーンショットスクリプトでパレット変換する際も0〜15前提とする）。
- **依存を増やさない**: Pillow / numpy を追加しない。PNG生成は標準ライブラリで完結させる。テストの追加依存は pytest のみ。
- **リポジトリを汚さない**: テストが生成するファイルは必ず `tmp_path` 配下へ出す。セーブファイルをリポジトリルートに作らない。
- **archive を書き換えない**: `docs/archive/` 配下の過去記録（`/workspaces/games` 表記や「3名」表記を含む）は歴史的記録として保持する。
- **CIを緑に保つ**: 追加したワークフローが最初から失敗する状態でマージしない。

## 5. Success Criteria
1. GitHub上のリポジトリ名が `delvoker` になり、ローカルの `origin` がそれを指している。
2. `git ls-files | grep -c pycache` が 0 で、`.gitignore` により再追加されない。ルート直下の `pyxel-*.png` も追跡されていない。
3. `docs/1. 機能要件.md` のパーティ人数が `Party.MAX_SIZE = 4` と一致している。
4. `docs/screenshots/` にタイトル・街・ダンジョン・戦闘の4枚があり、`tools/capture_screenshots.py` で再生成できる。
5. README に 概要 / スクリーンショット / 特徴 / 起動方法 / 操作方法 / AIとの役割分担 / テスト実行方法 / プロジェクト構成 / 今後の改善 が揃っている。
6. `main.py` の肥大化が「今後の改善」として README に明記されている。
7. `pip install -r requirements-dev.txt && pytest` がクリーンな環境で全件成功する。
8. GitHub Actions の test / smoke 両ジョブが緑になり、READMEにバッジが出ている。
9. `docs/4. 開発タスク.md` に Phase 40 が記録され、本指示書が `docs/archive/` へ移動している。

## 6. Recommended Verification
1. `git clean -xdn` で、追跡外のゴミが `.gitignore` で拾えているか確認する。
2. `git ls-files | grep -iE "pycache|\.pyc$|pyxel-.*\.png"` が空であることを確認する。
3. `pytest` をリポジトリルートで実行し、全件成功かつリポジトリに新規ファイルが残っていないこと（`git status` がクリーン）を確認する。
4. `Xvfb :99 -screen 0 640x480x24 & DISPLAY=:99 python tools/capture_screenshots.py` で4枚が再生成され、いずれも真っ黒でないことを目視確認する。
5. `python main.py` を実際に起動し、READMEに書いた操作キーが実装と一致していることを確認する。
6. READMEをGitHub上のプレビュー（またはVS Codeのマークダウンプレビュー）で開き、画像の相対パスが切れていないことを確認する。
7. `rg -n "最大3名|最大2名" docs/[0-9]*.md` で、マスター仕様書側に古い人数表記が残っていないことを確認する。

## 7. 補足: 調査中に判明した既存の不具合（本フェーズ対象外）
本フェーズでは修正しません。別タスクとして起票してください。

1. **`systems/persistence.py:88` — 破損セーブでクラッシュする**:
   - `deserialize_item()` は未知の `kind` を受け取ると全分岐を素通りして末尾の consumable 生成に落ち、`d["name"]` で `KeyError` を送出する。
   - `load_game()` の `except (FileNotFoundError, json.JSONDecodeError, KeyError)` はJSONのパース時にしか効かず、`deserialize_item()` は後から `main.py` 側で呼ばれるため捕捉されない。
   - 対処案: 未知の `kind` は `None` を返し、呼び出し側でスキップする。
2. **`data.py:551` — `NPCMember.inventory` が死んだ状態**:
   - `NPCMember.__init__` で `self.inventory = []` を定義しているが、`main.py` の `STATE_INV_GIVE_NPC` は装備スロット（weapon / armor / accessory）しか書き換えず、この属性に何も入れない。`serialize_member()` にも含まれていない。
   - 対処案: NPCに消費アイテムを持たせる仕様が無いなら属性ごと削除する。将来使う予定があるなら `serialize_member()` / `deserialize_npc_member()` に追加する。

---
※ 実装担当者への指示:
**Phase 40.2（.gitignore）→ 40.3（要件同期）** の機械的な作業から着手してください。次に **Phase 40.4（スクリーンショット）→ 40.5（テスト）** を進め、成果物が揃ってから **Phase 40.6（README）** を書くと、手戻りなくスクリーンショットとテスト実行方法を記載できます。**Phase 40.8（CI）** は `requirements-dev.txt` と `tools/capture_screenshots.py` の完成後に着手してください。**Phase 40.1（改名）** はGitHub側の操作を伴うため、ユーザーに実施を依頼してください。
