# Windows側でのデータベース同期修正手順

## 問題
Windows側で `no such table: contracts` エラーが発生している。
これはorder_management.dbがGitHubから正しく同期されていないことが原因。

## 解決方法

### 手順1: GitHubから最新版を強制取得

Windows側のコマンドプロンプトまたはPowerShellで以下を実行：

```cmd
cd C:\Users\watanabe\Desktop\GitHub\BillingManager2.0

# 現在のローカル変更をバックアップ（念のため）
copy order_management.db order_management.db.old

# Gitから最新のデータベースを強制的に取得
git fetch origin
git checkout origin/main -- order_management.db

# 確認
git status
```

### 手順2: アプリケーションを再起動

```cmd
python app.py
```

## エラーが解消しない場合

### 代替方法A: データベースファイルを直接削除して再取得

```cmd
# データベースを削除
del order_management.db

# Gitから取得
git checkout main -- order_management.db

# または完全にリセット
git restore order_management.db
```

### 代替方法B: リポジトリ全体を再クローン

最終手段として、新しいフォルダに再クローン：

```cmd
cd C:\Users\watanabe\Desktop\GitHub
git clone https://github.com/Yosuke1980/BillingManager2.0.git BillingManager2.0_new
cd BillingManager2.0_new
python app.py
```

## データベースの構造確認

正しく同期された場合、以下のコマンドでcontractsテーブルが存在することを確認できます：

```cmd
# PowerShellの場合
sqlite3 order_management.db ".tables"

# 出力に "contracts" が含まれていればOK
```

## 注意事項

- データベースはバイナリファイルなため、Gitでの管理には注意が必要
- 本番環境では、データベースはGit管理せずマイグレーションスクリプトで管理するのが推奨
- 開発段階では共有のため一時的にGit管理している
