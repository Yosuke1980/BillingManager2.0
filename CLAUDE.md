# Claude Code 設定

## 自動Git操作
タスク完了時に自動的に以下を実行:
1. `git add .`
2. `git commit -m "適切なコミットメッセージ"`  
3. `git push`

## 開発フロー
- コードの変更・実装
- 自動テスト実行
- 自動コミット & プッシュ

## プロジェクト固有の設定
- **テストコマンド**: `python3 test_scheduling.py`
- **Windowsテスト**: `python3 test_windows_startup.py`
- **リントコマンド**: (設定なし)
- **ビルドコマンド**: (設定なし)

## 自動化の有効化
このファイルの存在により、Claude Codeはタスク完了時に自動的にGit操作を実行します。