# データベース管理ガイド

## 概要

このプロジェクトでは、シンプルなSQLマイグレーションシステムを使用してデータベーススキーマを管理しています。

データベースファイル（*.db）はGit管理から除外されており、代わりにマイグレーションファイル（SQL）で管理されます。

## ディレクトリ構造

```
BillingManager2.0/
├── migrations/              # マイグレーションSQL
│   ├── 001_create_contracts_table.sql
│   ├── 002_ensure_expense_items_complete.sql
│   ├── 003_create_cast_tables.sql
│   ├── 004_create_history_tables.sql
│   └── rollback/           # ロールバックSQL
│       ├── 001_rollback.sql
│       ├── 002_rollback.sql
│       ├── 003_rollback.sql
│       └── 004_rollback.sql
├── migration_manager.py     # マイグレーション管理システム
├── init_database.py         # 初期セットアップスクリプト
├── create_migration.py      # 新規マイグレーション作成ヘルパー
├── fix_windows_complete.py  # Windows修復スクリプト
└── *.db                     # データベースファイル（Git管理外）
```

## 新規環境セットアップ

### Mac/Linux

```bash
# リポジトリをクローン
git clone https://github.com/Yosuke1980/BillingManager2.0.git
cd BillingManager2.0

# データベース初期化
python3 init_database.py

# アプリケーション起動
python3 app.py
```

### Windows

```cmd
# リポジトリをクローン
git clone https://github.com/Yosuke1980/BillingManager2.0.git
cd BillingManager2.0

# データベース初期化
python init_database.py

# アプリケーション起動
python app.py
```

## マイグレーションの作成

新しいテーブルやカラムを追加する場合：

```bash
# 新規マイグレーションファイル作成
python create_migration.py "add_email_to_partners"

# 生成されたファイルを編集
# migrations/005_add_email_to_partners.sql
# migrations/rollback/005_rollback.sql

# Git管理に追加
git add migrations/005_add_email_to_partners.sql
git add migrations/rollback/005_rollback.sql
git commit -m "Add migration: add email to partners"
git push
```

## マイグレーション実行

### 自動実行（推奨）

アプリケーション起動時に自動的に未実行のマイグレーションが実行されます。

### 手動実行

```python
from migration_manager import MigrationManager

mm = MigrationManager("order_management.db")
result = mm.run_migrations()

print(f"適用: {result['applied']}件")
```

### コマンドライン実行

```bash
# すべての未実行マイグレーションを実行
python migration_manager.py order_management.db

# ドライラン（実行内容を表示のみ）
python migration_manager.py order_management.db --dry-run

# マイグレーション履歴を表示
python migration_manager.py order_management.db --history

# 整合性チェック
python migration_manager.py order_management.db --validate

# ロールバック（2ステップ戻る）
python migration_manager.py order_management.db --rollback 2
```

## トラブルシューティング

### Windowsで「no such table: contracts」エラーが出る

```bash
# 完全修復スクリプト実行
python fix_windows_complete.py
```

このスクリプトは以下を実行します：
1. 既存データベースをバックアップ
2. 古いデータベースファイルを削除
3. 全マイグレーションを実行して新規作成
4. データベースを検証

### マイグレーションをやり直したい

```python
from migration_manager import MigrationManager

mm = MigrationManager("order_management.db")

# 2ステップ戻る
mm.rollback(steps=2)

# 再実行
mm.run_migrations()
```

### マイグレーションファイルが改ざんされている警告

```bash
# 整合性チェック
python migration_manager.py order_management.db --validate
```

一度適用したマイグレーションファイルは変更しないでください。
修正が必要な場合は、新しいマイグレーションを作成してください。

### データベースが破損した場合

```bash
# Windows
python fix_windows_complete.py

# Mac/Linux
rm order_management.db
python3 init_database.py
```

## マイグレーションファイルの命名規則

```
{3桁連番}_{説明}.sql
```

- 連番は001から開始
- 説明は小文字スネークケース
- 例: `005_add_email_to_partners.sql`

## ベストプラクティス

### DO（推奨）

✅ 新しいテーブルやカラムは必ずマイグレーションファイルで追加
✅ マイグレーションファイルは小さく、単一の目的に絞る
✅ ロールバックファイルも必ず作成
✅ マイグレーション適用前にバックアップを取る
✅ 本番環境では必ずdry-runで確認してから実行

### DON'T（非推奨）

❌ 適用済みのマイグレーションファイルを変更しない
❌ 直接SQLiteでテーブルを作成・変更しない
❌ データベースファイルをGitに追加しない
❌ マイグレーションを飛ばして実行しない

## 開発フロー

### スキーマ変更時

1. `python create_migration.py "変更内容"`
2. SQLファイル編集（migrations/XXX_*.sql）
3. ロールバックSQLファイル編集（migrations/rollback/XXX_rollback.sql）
4. `git add migrations/`
5. `git commit -m "Add migration: 変更内容"`
6. `git push`

### 新規環境セットアップ時

1. `git clone ...`
2. `python init_database.py`
3. `python app.py`

### Windows同期時

1. `git pull`
2. アプリ起動（自動マイグレーション実行）
3. エラーが出た場合: `python fix_windows_complete.py`

## FAQ

### Q: データベースファイルはどこにありますか？

A: プロジェクトルートに `order_management.db`, `billing.db`, `payee_master.db` が作成されます。
これらはGit管理外です。

### Q: 既存のデータは移行されますか？

A: いいえ。マイグレーションはスキーマのみを管理します。
データ移行が必要な場合は、別途マイグレーションSQLでINSERT文を記述してください。

### Q: マイグレーションが失敗した場合は？

A: 自動的にロールバックされます。エラーメッセージを確認して、SQLを修正してください。

### Q: 本番環境ではどうすればいいですか？

A:
1. バックアップを取る
2. `--dry-run`で確認
3. マイグレーション実行
4. 検証
5. 問題があればロールバック

## 参考リンク

- [マイグレーション詳細ガイド](docs/MIGRATION_GUIDE.md)（未作成）
- [新規環境セットアップ](docs/SETUP_NEW_ENVIRONMENT.md)（未作成）
- [migration_manager.py のドキュメント](migration_manager.py) - ソースコード内のdocstring参照
