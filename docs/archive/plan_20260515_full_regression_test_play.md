# Implementation Plan: Phase 30 - Full Regression Test Play and Bug Fix

## 1. Purpose

Phase 29までの主要機能と新規3Dビュー面素材を含め、ゲーム全体を通しで検証する。

目的は新機能追加ではなく、以下を発見・修正すること。

- クラッシュ
- 進行不能
- セーブ互換不具合
- 主要フローの回帰
- UIはみ出し
- 3Dビュー面素材の視認性問題

本フェーズは `docs/4. 開発タスク.md` の Phase 30 に対応する。

## 2. Source of Truth

検証時は以下の仕様を正とする。

- `docs/1. 機能要件.md`
- `docs/3. 仕様詳細.md`
- `docs/4. 開発タスク.md`

ゲーム内テキストはASCIIのみを維持する。
Pyxel色番号は0-15の範囲を維持する。

## 3. Scope

### In Scope

- 起動、New Game、Continue、セーブ/ロード
- Town / Home / Guild / Shop / Dungeon / Battle / Log View の主要遷移
- ダンジョン探索、3Dビュー、階層別surface表示
- 戦闘、スキル、対象選択、逃走、勝利、敗北
- アイテム使用、装備、NPCへの受け渡し
- Shop購入/売却/Restock
- 宿屋、Revive、レベルアップ、ステータス割り振り
- 部位破壊、特殊ドロップ、Bestiary
- Ending到達までの進行確認
- UIはみ出し、可読性、深層視認性

### Out of Scope

- 新規コンテンツ追加
- BGM差し替え
- 日本語フォント導入
- ダンジョンバイオーム新ギミック追加

ただし、検証中に重大な不具合を見つけた場合は、本フェーズ内で修正する。

## 4. Test Environment

基本コマンド:

```text
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B main.py
```

構文チェック:

```text
python -B -c "paths=('main.py','tools/convert_image2_assets.py','ui/renderer_3d.py'); [compile(open(p, encoding='utf-8').read(), p, 'exec') for p in paths]; print('compile ok')"
```

surface取り込み確認:

```text
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B tools/convert_image2_assets.py --surfaces
```

3Dビュー簡易描画確認:

```text
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B -c "import pyxel; from ui.renderer_3d import draw_3d_view; pyxel.init(256,256,display_scale=1); pyxel.load('assets.pyxres'); draw_3d_view(lambda d,s: (d==2 and s==0) or (s in (-1,1) and d < 3), True, 5); print('render ok', flush=True)"
```

## 5. Verification Checklist

### 5.1 Startup and Save Compatibility

- New Gameから名前入力へ進める。
- 名前入力後、Townへ到達する。
- Continueが既存セーブでクラッシュしない。
- セーブデータが無い場合、Continueが不正表示されない。
- `assets.pyxres` 読み込み成功時に画像描画される。
- `assets.pyxres` が無い場合でもフォールバック描画でクラッシュしない。

### 5.2 Main State Transitions

- Title -> New Game -> Town
- Title -> Continue -> Town
- Town -> Home -> Warehouse / Renovate / Training
- Town -> Guild
- Town -> Shop -> Buy / Sell
- Town -> Dungeon
- Dungeon -> Battle -> Dungeon
- Dungeon -> Log View -> Dungeon
- Dungeon -> Teleport -> Town
- Battle defeat -> wipe penalty / Grave flow
- Archdemon defeat -> Ending

### 5.3 Dungeon and 3D View

- B1F-B2Fのsurfaceセットが表示される。
- B3F-B4Fのsurfaceセットが表示される。
- B5F-B10Fのsurfaceセットが表示される。
- ceiling / side wall / front wall / floor / far が別面として読める。
- 正面壁は斜めに流れず、突き当たり壁として見える。
- 左右横壁は奥へ流れ、左壁は不自然な向きにならない。
- Far Endは正面壁の遠距離版ではなく、最奥背景面として見える。
- 深層B5F以降で黒潰れにより進行方向や壁が読めなくならない。
- NPC、階段、宝箱、罠、鍵扉、泉、商人が探索画面で破綻しない。

### 5.4 Battle Flow

- 通常戦闘が開始し、ターンが止まらない。
- Aidが実行できる。
- Provoke / Quick Strike / Mana Bolt が実行できる。
- 複数敵で対象選択が破綻しない。
- 複数味方で対象選択が破綻しない。
- 部位持ち敵でBody/部位選択ができる。
- 部位破壊ログと特殊ドロップ抽選が動く。
- 逃走可能敵から逃走できる。
- Dungeon Master / Archdemonから逃走できない。
- 勝利後、EXP/Gold/Dropが処理される。
- 敗北後、全滅ペナルティとGrave flowが処理される。

### 5.5 Items, Shop, Growth

- InventoryでUse / Equip / Give to NPCが破綻しない。
- 回復アイテム対象選択が機能する。
- Grimoireでスキル習得できる。
- Mapping Scrollが探索中に機能する。
- ShopでBuy / Sellが機能する。
- Restockが歩数または階層移動で発生する。
- 宿屋で生存メンバーのみ回復する。
- Reviveで戦闘不能メンバーを蘇生できる。
- レベルアップ時にステータス割り振りへ進める。
- Genesis品、呪い、耐性、追加装備の表示と保存が破綻しない。

### 5.6 UI and Readability

- Party HUDで4人表示が崩れない。
- Battle HUDで複数敵/複数味方でも文字がはみ出さない。
- Inventory / Shop / Guild / Bestiary / Log Viewで長い名前がはみ出さない。
- Damage popupが対象位置に出る。
- 状態異常表示 `[P]` / `[S]` が読める。
- 3Dビュー更新後、NPCやHUDと視覚的に干渉しない。
- ゲーム内表示テキストがASCII範囲に収まる。

## 6. Bug Report Format

不具合を見つけたら、指示書または作業メモに以下の形式で記録する。

```text
### BUG-XX: short_ascii_title

Severity: Critical / High / Medium / Low
Area: Startup / Save / Dungeon / Battle / UI / Asset / Other
Build State: current branch + relevant files

Steps:
1. ...
2. ...
3. ...

Expected:
- ...

Actual:
- ...

Suspected Cause:
- ...

Fix Plan:
- ...

Verification:
- [ ] Reproduced before fix
- [ ] Fixed
- [ ] Regression checked
```

Severity基準:

- Critical: クラッシュ、セーブ破壊、進行不能
- High: 主要フローが成立しない、戦闘/探索が止まる
- Medium: UI崩れ、表示誤り、バランス上の明確な問題
- Low: 軽微な見た目、文言、ログの問題

## 7. Implementation Instructions

1. Phase 30.1として本指示書を作成済みにする。
2. まず構文チェックとsurface取り込み確認を実行する。
3. 自動化できる範囲は小さなPythonコマンドで再現確認する。
4. 手動操作が必要な範囲は、再現手順と確認結果を記録する。
5. Critical / High の不具合を最優先で修正する。
6. 修正時は既存仕様と保存互換を壊さない。
7. 仕様変更が必要になった場合は `docs/3. 仕様詳細.md` を更新する。
8. Phase 30完了時に `docs/4. 開発タスク.md` を更新し、本指示書を `docs/archive/` へ移動する。

## 8. Acceptance Criteria

- Phase 30.2-30.6のチェック項目をすべて実施済みにする。
- Critical / High の既知不具合が残っていない。
- Medium以下の未修正不具合がある場合は、理由とBacklog化方針が記録されている。
- `main.py` / 主要モジュールの構文チェックが通る。
- `assets_loaded=True` と `assets_loaded=False` の両方で探索画面がクラッシュしない。
- B1F-B2F / B3F-B4F / B5F-B10F の3Dビューが視認可能である。
- `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装結果と同期している。

## 9. Execution Result

Status: Completed

### Verification Summary

- Syntax / py_compile: Passed.
- Surface import: Passed. 15 surface PNGs were imported into `assets.pyxres`.
- 3D render smoke: Passed with `assets_loaded=True`.
- Dungeon render fallback: Passed with `assets_loaded=False`.
- Automated regression smoke: Passed 29 checks across Title, New Game, Town, Home, Guild, Shop, Dungeon, Battle, Log View, Inventory, Revive, Ending, save serialization, item use, grimoire learning, shop restock, stat allocation, victory, and boss flee lock.
- Static checks: Passed for JSON master references, Pyxel color range 0-15, and non-docstring ASCII string literals.
- Entrypoint launch: `timeout 3 python -B main.py` reached the expected timeout without startup crash.

### Findings

- No Critical / High issues were detected.
- No code fix was required in this phase.
- `docs/3. 仕様詳細.md` had an outdated note saying side walls stayed solid color. The specification was synchronized to the current `ui/renderer_3d.py` implementation, where side walls are tiled by 1px vertical strips and the left wall is flipped.

### Commands Run

```text
python -B -c "paths=('main.py','tools/convert_image2_assets.py','ui/renderer_3d.py'); [compile(open(p, encoding='utf-8').read(), p, 'exec') for p in paths]; print('compile ok')"
python -B -m py_compile constants.py data.py logic/map_generator.py main.py npc.py systems/persistence.py tools/convert_image2_assets.py ui/renderer_3d.py window.py
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B tools/convert_image2_assets.py --surfaces
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B -c "import pyxel; from ui.renderer_3d import draw_3d_view; pyxel.init(256,256,display_scale=1); pyxel.load('assets.pyxres'); draw_3d_view(lambda d,s: (d==2 and s==0) or (s in (-1,1) and d < 3), True, 5); print('render ok', flush=True); pyxel.quit()"
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp python -B
env SDL_AUDIODRIVER=dummy XDG_RUNTIME_DIR=/tmp timeout 3 python -B main.py
```
