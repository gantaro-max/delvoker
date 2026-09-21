# Implementation Plan: Phase 40 Review Follow-up

## Goal
GitHub Actions の smoke ジョブで、バックグラウンド起動した Xvfb が標準出力・標準エラーのパイプを保持し続ける問題を解消する。

## Changes
- `.github/workflows/ci.yml`: Xvfb 起動を独立した step に分け、出力を `/dev/null` へリダイレクトして2秒待機する。
- `tools/capture_screenshots.py`: 未使用の `_LoopCapture` を削除し、`pyxel.run` を no-op に差し替える。
- `docs/4. 開発タスク.md`: レビュー追従修正と検証結果を Phase 40 に記録する。

## Verification
- Xvfb をリダイレクト付きでバックグラウンド起動し、スクリーンショット生成が終了すること。
- `pytest` が全件成功すること。
- `git diff --check` が成功すること。

完了後、この指示書を `docs/archive/` へ移動する。
