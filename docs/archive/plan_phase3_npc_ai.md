---
Target Plan File: docs/plan_phase3_npc_ai.md
---

1. **Task Overview:**
   ノンプレイヤーキャラクター (NPC) の基本的なAIを実装します。これには、アイドル、ランダム移動、プレイヤー追跡などの単純な移動パターンと、基本的なインタラクションロジックが含まれます。

2. **Target Files:**
   - `/workspaces/games/main.py` (ゲームループへのNPCの統合、`update` および `draw` メソッドの呼び出し)
   - `/workspaces/games/character.py` (既存のキャラクター基底クラスがある場合、NPC固有のロジックのために拡張)
   - `/workspaces/games/npc.py` (新規ファイル: NPCクラスおよびAIロジック)
   - `/workspaces/games/data.py` (NPCの種類、ステータス、初期位置などのマスターデータ定義)

3. **Step-by-Step Instructions:**
   - **`/workspaces/games/npc.py` の新規作成:**
     - `NPC` クラスを定義します。既存の `Character` 基底クラスがあればそれを継承するか、新規に作成します。
     - AIの状態 (例: `IDLE`, `WANDER`, `CHASE`)、移動速度、現在のターゲットなどのプロパティを含めます。
     - NPCのAIロジックを処理する `update` メソッドを実装します。
       - `IDLE`: 静止状態、またはアイドルアニメーションを再生します。
       - `WANDER`: 定義されたエリア内、または短時間ランダムに移動します。
       - `CHASE`: プレイヤーが一定範囲内にいる場合、プレイヤーに向かって移動します。
     - NPCのスプライト描画を処理する `draw` メソッドを実装します。

   - **`/workspaces/games/main.py` の修正:**
     - `npc.py` から `NPC` クラスをインポートします。
     - 1つ以上の `NPC` オブジェクトをインスタンス化します。
     - メインゲームループ内で、すべてのアクティブなNPCの `update` および `draw` メソッドを呼び出します。
     - NPCのリスト (例: `self.npcs = []`) を管理します。

   - **`/workspaces/games/data.py` の修正 (該当する場合):**
     - 異なるNPCタイプ (例: `NPC_SLIME`, `NPC_GOBLIN`) の定義を追加します。これには、スプライト、初期状態、AIパラメータ (例: 追跡範囲、徘徊時間) などを含めます。

4. **Constraints:**
   - Pyxelの16色パレット (0-15) を厳守してください。
   - 画面解像度は256x256ピクセル以内です。
   - ゲーム内テキスト (NPC名、メッセージなど) は、必ずASCII文字 (半角英数字・記号) のみを使用してください。
   - Pyxelでのパフォーマンスを考慮し、AIロジックはシンプルに保ってください。

5. **Success Criteria:**
   - NPCが画面上に正しく描画されること。
   - NPCが基本的なAI動作 (例: アイドル、ランダム移動) を示すこと。
   - NPCがプレイヤーを検知し、簡単な追跡行動を開始すること。
   - NPCの描画やAIに関連するゲームのクラッシュや視覚的な不具合が発生しないこと。