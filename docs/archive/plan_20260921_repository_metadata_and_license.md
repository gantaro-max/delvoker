# Implementation Plan: Phase 42 - Repository Metadata and Licensing

## Goal
GitHub公開前にリポジトリのDescription・Topics・ライセンス範囲を明確化する。

## Changes
- GitHub Descriptionを、Delvokerのポーター支援型ダンジョンRPGという特徴が伝わる英文へ更新する。
- GitHub TopicsへPython、Pyxel、ダンジョンRPG、手続き生成などの分類語を設定する。
- ルートへ標準MIT Licenseを追加し、コードと非画像ドキュメントへ適用する。
- 追跡済みの画像・`assets.pyxres`へCC BY 4.0を適用し、`assets/LICENSE.md`と`ASSET_CREDITS.md`で範囲・出典・帰属方法を明示する。
- READMEとSSOTへライセンス方針を同期する。

## Verification
- GitHub APIでDescription・Topicsが期待値と一致すること。
- 追跡済みPNGと`assets.pyxres`が資産ライセンスの対象に含まれること。
- `git diff --check`と既存テストが成功すること。

完了後、本指示書を`docs/archive/`へ移動する。
