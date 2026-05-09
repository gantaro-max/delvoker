# Implementation Plan: Phase 14 - Polish & Active Skills (Full)

## 1. Task Overview
多対多戦闘の導入により煩雑になった情報の整理、聴覚的ストレスの軽減、および戦略性の拡充を目的に以下のアップデートを実施します。
1. **UI/Audio Polish**: 表示の重なり解消とBGMの音色改善。
2. **Active Skills**: ジョブ固有スキルの実装と戦闘中のスキル選択UI。
3. **Visual Upgrade**: 3Dビューへのテクスチャマッピング導入（プロトタイプ）。

## 2. Target Files
- `/workspaces/games/main.py`: UIロジック、オーディオ定義、スキル実行フローの修正。
- `/workspaces/games/constants.py`: `STATE_BATTLE_SKILL = 22` 定数の追加、コマンド定義更新。
- `/workspaces/games/data.py`: `Skill` クラスの拡張およびジョブ固有初期スキルの定義。
- `/workspaces/games/ui/renderer_3d.py`: `draw_3d_view` をテクスチャ描画（`pyxel.blt`）対応に更新。
- `/workspaces/games/docs/3. 仕様詳細.md`: 新スキルおよびオーディオ仕様の追記。
- `/workspaces/games/docs/4. 開発タスク.md`: フェーズ進捗の更新。

## 3. Sub-Phases & Instructions

### Phase 14.1: UI & Audio Polish
1. **バトルUIの改善**: `main.py` の `_draw_battle` を修正。現在はスキル名を 1 行に結合していますが、これを 2x2 のグリッド表示に変更します。
   - 表示開始座標: `cx, cy + 52`
   - グリッド間隔: 横 60px、縦 8px
2. **倉庫UIの改善**: `main.py` の `_draw_home` (Warehouseサブメニュー) を修正。アイテム名の文字数制限を `[:22]` から `[:18]` に短縮し、中央の区切り線との衝突を回避します。
3. **BGMの再定義**: `main.py` の `_init_audio` を修正。
   - BGM 3, 4, 5 の波形を `s` (Square) から `t` (Triangle) に変更。
   - 音量パラメータ（`5` または `6`）を `2` または `3` に下げ、低密度で耳に優しい音に変更。

### Phase 14.2: ジョブ固有スキルの実装
1. **スキルコマンドの追加**: `constants.py` の `COMMANDS` リストに `"Skill"` を追加し、`STATE_BATTLE_SKILL` を通じて戦闘中にスキル選択画面へ遷移可能にします。
2. **ジョブ固有スキルの定義**: `data.py` の各ジョブに初期スキルを実装します。
   - **Warrior**: `Provoke` (MP: 3) - 敵のターゲットを自身に固定し、2ターンの間被ダメージを 25% 軽減。
   - **Thief**: `Quick Strike` (MP: 4) - ダイスダメージ + AGI の半分をダメージに加算。
   - **Mage**: `Mana Bolt` (MP: 5) - MAG に基づく無属性魔法ダメージ。
3. **実行ロジックの実装**: `main.py` に `STATE_BATTLE_SKILL` の `update` / `draw` 処理を追加。多対多戦闘において、スキルターゲットを選択できるよう `STATE_BATTLE_TARGET` と連携させます。

### Phase 14.3: 3D壁面テクスチャ描画 (Prototype)
1. **テクスチャ描画ロジック**: `ui/renderer_3d.py` を修正。`self.assets_loaded` が True の場合、`pyxel.rect` による壁面塗りつぶしの代わりに、`pyxel.blt` を使用します。
2. **バイオーム対応準備**: タイルマップの情報を参照し、階層ごとに異なる 8x8 ピクセルのパターンを壁面に繰り返し描画（タイリング）するプロトタイプを実装します。

### Phase 14.4: ドキュメント同期
1. **仕様詳細の更新**: `docs/3. 仕様詳細.md` に Section 10「アクティブスキル仕様」を追記し、各スキルの計算式を記載します。
2. **タスクリストの更新**: `docs/4. 開発タスク.md` の Phase 13 を完了に、Phase 14 を「着手」に変更します。

## 4. Constraints
- **ASCII制約**: ゲーム内メッセージ、スキル名などは全て半角英数字（ASCII）を維持すること。
- **描画互換性**: `assets.pyxres` が存在しない場合、自動的に従来の単色描画（`pyxel.rect`）にフォールバックすること。
- **セーブ互換性**: スキル習得情報の追加に伴い、既存のセーブデータ読み込み時にエラーが出ないよう `systems/persistence.py` でデフォルト値を設定すること。

## 5. Success Criteria
1. スキル名がグリッド状に整理されている。
2. BGMが耳に優しい音色になっている。
3. 戦闘中に「Skill」コマンドからジョブ固有の特技を選択・実行できる。
4. 3Dビューの壁面に、単色塗りつぶし以外のパターンが表示される（アセットロード時）。

---
※ Claude Code への追加指示：
1. まずは **Phase 14.1** の UI と BGM の修正から着手してください。
2. 次に **Phase 14.2** のスキル実装において、多対多戦闘へのターゲット選択ロジックの統合案を提示してから実装に入ってください。