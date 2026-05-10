# Implementation Plan: Phase 20 - Shop Restock, Party Card HUD & Genesis Rarity

## 1. Task Overview
ショップの全商品表示による画面溢れを解消し、探索歩数に連動して品揃えが変わる動的陳列へ刷新します。あわせて、探索中HUDをパーティカード型に変更し、ポーターが後衛であることとNPCの状態を常時確認できるようにします。さらに、アイテム収集のエンドコンテンツとして5段階レアリティと最上位 `Genesis` 級を導入します。

主目的:
- ショップを15品目に制限し、画面内で読みやすく表示する。
- 迷宮探索と街ショップ確認のループに小さな期待感を作る。
- 探索中にパーティ全員のHP/MP、装備、状態異常を一目で把握できるようにする。
- `Genesis` 級アイテムを、エンチャントに依存しない圧倒的な基礎性能アイテムとして定義する。

## 2. Target Files
- `/workspaces/games/constants.py`: ショップ在庫数・再入荷歩数・レア混入率などの定数追加。
- `/workspaces/games/main.py`: `shop_stock` / `steps_to_restock`、歩数連動更新、ショップUI、カード型 `draw_status`、購入時の在庫参照。
- `/workspaces/games/data.py`: レアリティ体系、`Genesis` 生成、`make_enchanted_weapon` / `make_enchanted_armor` の抽選更新。
- `/workspaces/games/data/items.json`: 必要なら Genesis 用ベース候補や value 調整を追加。
- `/workspaces/games/data/enchants.json`: Legend 判定に使う強力エンチャントの重みやタグが必要なら追加。
- `/workspaces/games/systems/persistence.py`: Genesis / rarity 固有値の保存復元が必要な場合に更新。
- `/workspaces/games/docs/3. 仕様詳細.md`: ショップ在庫、HUD、レアリティ仕様を追記。
- `/workspaces/games/docs/4. 開発タスク.md`: Phase 20 のタスクと完了チェックを追加。

## 3. Sub-Phases & Instructions

### Phase 20.1: ショップ動的陳列システム
1. **定数追加**: `constants.py` に以下を追加する。
   - `SHOP_STOCK_SIZE = 15`
   - `SHOP_RESTOCK_STEPS = 100`
   - `SHOP_RARE_SLOT_RATE = 0.08`（5〜10%の中間値）
2. **Appフィールド追加**: `App.__init__` に以下を追加する。
   - `self.shop_stock = []`
   - `self.steps_to_restock = SHOP_RESTOCK_STEPS`
   - 初期化終盤で `_restock_shop(force=True)` を呼び、初回在庫を生成する。
3. **ティア別商品候補**: `main.py` に `_shop_tier_keys(floor)` を追加する。
   - 既存 `_drop_pools(floor)` の思想に合わせ、B1-3 / B4-6 / B7-10 の3段階で商品候補を返す。
   - 商品候補は `SHOP_KEYS` と `ITEM_CATALOG` の積集合に限定し、存在しないキーを混ぜない。
   - 消耗品（herb, potion, ether, antidote等）は全ティアに一定数含めてよい。
4. **再入荷処理**: `_restock_shop(force=False)` を追加する。
   - 基本在庫は現在階層ティアの候補から `SHOP_STOCK_SIZE` 件までランダム抽選する。
   - 候補が15未満の場合のみ重複を許可するか、下位ティア候補を補充する。
   - 5〜10% の確率で1スロットだけ「レア枠」に差し替える。
   - レア枠候補:
     - 現在より1つ上のティアの商品キー。
     - または武器/防具キーをもとに生成した Rare/Epic/Legend/Genesis 品。
   - `steps_to_restock` を `SHOP_RESTOCK_STEPS` に戻す。
5. **在庫アイテム表現**: `shop_stock` は購入処理の都合上、以下のどちらかで統一する。
   - 推奨: `list[Item]` として clone 済み商品を持つ。エンチャント済み/Genesis もそのまま購入できる。
   - 代替: `list[str]` を基本にし、レア枠だけ `(key, item)` の構造にする。ただしUIと購入処理が複雑になるため非推奨。
6. **歩数連動**: `_upd_dungeon` の移動成功時 (`moved == True`) に `steps_to_restock -= 1` する。
   - `steps_to_restock <= 0` で `_restock_shop()` を呼ぶ。
   - 階段移動、ボス撃破、墓イベント回収など「区切り」のイベント後にも必要なら `_restock_shop(force=True)` を呼んでよい。
7. **ショップ購入ロジック更新**: `_upd_shop` の Buy モードを `SHOP_KEYS` ではなく `self.shop_stock` 参照に変更する。
   - Up/Down は在庫数を基準に移動。
   - 購入時は `self.shop_stock[self.shop_idx].clone()` をバッグへ入れる。
   - Enchanted / Genesis アイテムの clone が正しく値を保持することを確認する。
8. **ショップUI刷新**: `_draw_shop` の Buy モードを15件制限の3列×5行グリッドへ変更する。
   - 各セルは安定サイズにする（例: `col_w = 76`, `row_h = 24`）。
   - 表示: カーソル、短縮名、価格、レアリティ色。
   - 下部に `Restock:{steps_to_restock}` と Gold を表示。
   - Sell モードは既存リスト形式を維持してよい。
9. **画面溢れ対策**: 商品名はセル幅に合わせて `[:14]` 程度に短縮し、価格と重ならないようにする。

### Phase 20.2: パーティ情報カード型HUD
1. **`draw_status` のレイアウト刷新**: `STATUS_Y` 以降を3枚のカードに分割する。
   - 横並び推奨: `card_w = SCREEN_W // 3`、高さは `SCREEN_H - STATUS_Y`。
   - index 0 はプレイヤー（ポーター）で `[REAR]` または `[POST]` タグを表示。
   - NPCは `[FRONT]` タグを表示。
   - プレイヤーカードの枠色は `COL_PEACH`、NPCカードは `COL_LIGHT_GRAY` などで差別化する。
2. **カード描画ヘルパー**: `_draw_party_card(member, x, y, w, h, role, border_col)` を追加する。
   - `draw_status` が肥大化しないようにする。
   - Refactor Agent 条件に該当するため、カード描画はヘルパー化する。
3. **HP/MPバー**:
   - HPは常時バー + 数値 (`HP 12/20`)。
   - MPはMPを持つメンバーならバー + 数値 (`MP 4/8`)。
   - バー色はHP割合に応じて Green / Orange / Red。
4. **装備表示**:
   - `W:` 武器名短縮（例: `W:Old Dagger` → `W:OldDag` など）
   - `A:` 防具名短縮、なければ `A:None`
   - アクセサリーはスペースがあれば `Acc:` も表示。収まらない場合は優先度を W/A > Acc とする。
5. **状態異常アイコン**:
   - 毒: `[P]` 緑、スタン: `[S]` 黄、Provoke等は必要に応じて `[V]` などASCIIタグ。
   - 各カード内の右上または下段に収める。
6. **補助情報の残し方**:
   - 座標・方角・階層・Gold・ヘルプテキストはカード外の1行に収めるか、カード内に短縮して配置する。
   - テキストがカード外へはみ出さないよう、全ラベルは短縮する。
7. **空スロット表示**:
   - パーティが3人未満の場合、空カードに `-- Empty --` を灰色で表示する。

### Phase 20.3: レアリティ体系拡張と Genesis 級
1. **レアリティ定義**: `data.py` の `EnchantedWeapon.rarity` / `EnchantedArmor.rarity` を以下の5段階へ整理する。
   - `normal`: 白。補正なし。
   - `rare`: 黄。エンチャント1つ。
   - `epic`: 桃。エンチャント2つ。
   - `legend`: 橙。強力なエンチャントの組み合わせ。
   - `genesis`: 水色系（Pyxel標準なら `COL_BLUE` または点滅で `COL_BLUE`/`COL_WHITE`）。エンチャント枠0。
2. **既存名との互換性**:
   - 現在の `common` / `magic` / `rare` / `cursed` 表示を参照しているUIがあるため、全UIを新レアリティ名へ更新する。
   - 呪い (`cursed`) を残す場合はレアリティではなく `is_cursed` / 表示修飾として扱う。
3. **Genesis表現**:
   - `EnchantedWeapon` / `EnchantedArmor` に `genesis=False` または `rarity_override=None` を持たせる。
   - Genesis は `prefix=None`, `suffix=None` を維持し、`rarity == "genesis"` を返す。
   - 武器: `dice_count`, `dice_sides`, `static_bonus` を Legend 最大級以上に直接補正する。
   - 防具: `def_bonus` を Legend 最大級以上に直接補正する。
   - `label()` は例: `Genesis Old Dagger (X-Y)` / `Genesis Leather Armor (DEF+X)` のようにASCII表記。
4. **生成関数更新**:
   - `make_enchanted_weapon(base_key)` / `make_enchanted_armor(base_key)` の冒頭で `0.5%` 程度の Genesis 抽選を行う。
   - Genesis 抽選に当選した場合、prefix/suffix抽選をスキップして Genesis アイテムを返す。
   - 通常抽選は Rare/Epic/Legend の発生確率を明示的に管理する。
5. **Legend判定**:
   - 既存 `enchants.json` の強力接頭辞（例: `master`）や強力接尾辞の組み合わせを Legend とする。
   - 実装しやすさ優先なら、prefix+suffix のうち特定キーを含む場合に `legend`、それ以外の2枠付与は `epic` とする。
6. **価格と売却価格**:
   - Genesis / Legend は `value` を増やす。目安:
     - Rare: base × 1.5
     - Epic: base × 2.5
     - Legend: base × 4
     - Genesis: base × 8 以上
   - 売却は既存 `value * 0.3` のままでよい。
7. **clone / persistence対応**:
   - `clone()` が `genesis` や `rarity_override`、補正済み基礎性能を失わないようにする。
   - `systems/persistence.py` が EnchantedWeapon/Armor を保存している場合、Genesis フラグを追加保存する。
   - 既存セーブデータに Genesis フラグがない場合は `False` として復元する。
8. **UI色更新**:
   - インベントリ、ショップ、売却、NPC装備管理など、アイテム名の色分けを共通ヘルパー化する。
   - 推奨: `main.py` に `_item_color(item)` を追加し、`rarity` に応じて色を返す。
   - Genesis は `pyxel.frame_count` で `COL_BLUE` / `COL_WHITE` を交互に出す簡易明滅でもよい。

### Phase 20.4: ドキュメント同期
1. **仕様詳細更新**: `docs/3. 仕様詳細.md` に以下を追記する。
   - Shop Restock System: `shop_stock`, `steps_to_restock`, 15品目、100歩更新、レア枠。
   - Party Card HUD: `[REAR]` / `[FRONT]`、HP/MPバー、装備、状態異常。
   - Rarity System: Normal/Rare/Epic/Legend/Genesis の定義、色、生成確率、Genesis仕様。
2. **開発タスク更新**: `docs/4. 開発タスク.md` に Phase 20 を追加し、完了チェック欄を作成する。
3. **実装指示書の完了処理**: 実装・確認が完了したら、このファイルを `docs/archive/` に移動する。

## 4. Constraints
- **ASCII制約**: ゲーム内表示文字列はすべてASCIIにする。`Genesis`, `[REAR]`, `[FRONT]`, `Restock` など英字表記を使う。
- **Pyxel色制約**: 色番号は0〜15の範囲のみ使用する。
- **UI安定性**: ショップグリッドとHUDカードは固定寸法にし、商品名・装備名は必ず短縮して枠外にはみ出さないようにする。
- **既存セーブ互換性**: 新規フィールドがない既存データを読み込んでもクラッシュしないようにする。
- **在庫購入の一貫性**: エンチャント済み/Genesis商品は、表示された個体と購入される個体の性能が一致するようにする。
- **過度なリロール防止**: `shop_stock` はショップ画面を開くたびに無条件更新しない。歩数または明示イベントで更新する。
- **Refactor方針**: `_draw_shop` / `draw_status` が肥大化する場合は、セル描画・カード描画・アイテム色をヘルパーへ分離する。

## 5. Success Criteria
1. ショップBuy画面が15品目以内に制限され、3列×5行または同等に画面内へ収まる。
2. ダンジョンを歩くたびに `steps_to_restock` が減り、0でショップ在庫が更新される。
3. 現在階層ティアに沿った商品が中心に並び、低確率で上位ティアまたは高レア商品が1枠混ざる。
4. 表示されたエンチャント済み/Genesis商品を購入したとき、同じ性能のアイテムがバッグに入る。
5. 探索中HUDでプレイヤーが `[REAR]` または `[POST]` として表示され、NPCは `[FRONT]` として表示される。
6. 各パーティカードにHP/MPバー、装備短縮名、状態異常アイコンが収まる。
7. レアリティが Normal/Rare/Epic/Legend/Genesis の5段階で表示・色分けされる。
8. Genesis級が極低確率で生成され、prefix/suffixなしで高い基礎性能を持つ。
9. `docs/3. 仕様詳細.md` と `docs/4. 開発タスク.md` が実装内容と一致している。

---
※ 実装担当者への指示:
まず **Phase 20.1** の詳細タスク分解を作成し、`shop_stock` を `list[Item]` として扱う方針で購入処理・UI・clone/persistenceへの影響を確認してください。その後、HUD刷新とレアリティ拡張を順に進めてください。
