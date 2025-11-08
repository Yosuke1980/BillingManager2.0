# マイグレーションディレクトリ

このディレクトリには、データベーススキーマのマイグレーションファイルが格納されています。

## ディレクトリ構造

```
migrations/
├── 001_create_contracts_table.sql
├── 002_ensure_expense_items_complete.sql
├── 003_create_cast_tables.sql
├── 004_create_history_tables.sql
├── rollback/
│   ├── 001_rollback.sql
│   ├── 002_rollback.sql
│   ├── 003_rollback.sql
│   └── 004_rollback.sql
└── README.md (このファイル)
```

## マイグレーションファイル一覧

### 001_create_contracts_table.sql
**目的**: contractsテーブル作成
**説明**: 契約管理の中核テーブル（発注書・契約書の統合管理）
**依存**: productions, partners

### 002_ensure_expense_items_complete.sql
**目的**: expense_itemsテーブルの完全性確保
**説明**: expense_itemsテーブルを作成し、全カラムを定義
**依存**: contracts, productions, partners

### 003_create_cast_tables.sql
**目的**: 出演者関連テーブル作成
**説明**: cast, contract_cast, production_castテーブルの作成
**依存**: contracts, productions, partners

### 004_create_history_tables.sql
**目的**: 履歴管理テーブル作成
**説明**: contract_renewal_history, order_history, status_historyテーブルの作成
**依存**: contracts, expense_items

## 新規マイグレーションの作成

```bash
# ヘルパースクリプトを使用（推奨）
python create_migration.py "説明"

# 手動作成の場合
# 1. 次の連番を確認（現在の最大は004）
# 2. migrations/005_説明.sql を作成
# 3. migrations/rollback/005_rollback.sql を作成
```

## マイグレーションファイルの命名規則

- フォーマット: `{3桁連番}_{説明}.sql`
- 連番は001から開始
- 説明は小文字スネークケース
- 例: `005_add_email_to_partners.sql`

## マイグレーションファイルのテンプレート

```sql
-- マイグレーション: 説明
-- バージョン: XXX
-- 作成日: YYYY-MM-DD
-- 説明: 詳細な説明

-- ここにSQLを記述
CREATE TABLE IF NOT EXISTS table_name (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ...
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_name ON table_name(column_name);
```

## ロールバックファイルのテンプレート

```sql
-- ロールバック: 説明
-- バージョン: XXX
-- 作成日: YYYY-MM-DD

-- ここにロールバックSQLを記述
DROP INDEX IF EXISTS idx_name;
DROP TABLE IF EXISTS table_name;
```

## 注意事項

### 必ず守ること

1. **一度適用したマイグレーションファイルは変更しない**
   - チェックサムで改ざんを検出します
   - 修正が必要な場合は新しいマイグレーションを作成

2. **連番は欠番なく順序通りに**
   - 001, 002, 003, ... と連続した番号を使用
   - 欠番があると警告が表示されます

3. **ロールバックファイルも必ず作成**
   - 各マイグレーションに対応するrollbackファイルを作成
   - テストしてロールバックが正常に動作することを確認

4. **CREATE TABLE には IF NOT EXISTS を使用**
   - 冪等性を保つため
   - 何度実行しても安全にする

5. **外部キー制約に注意**
   - 依存するテーブルが先に作成されていることを確認
   - ON DELETE, ON UPDATE の動作を明示

### 推奨事項

- マイグレーションは小さく、単一の目的に絞る
- 複雑な変更は複数のマイグレーションに分割
- コメントで変更理由を記載
- テーブル作成後は必要なインデックスも作成
- 本番適用前にバックアップを取る

## トラブルシューティング

### マイグレーションが失敗する

```bash
# エラー内容を確認
python migration_manager.py order_management.db --history

# SQLを修正して再実行
# 失敗したマイグレーションは自動的にロールバックされます
```

### チェックサム不一致の警告

適用済みのマイグレーションファイルが変更されています。
**絶対に適用済みファイルを変更しないでください。**

解決方法：
1. ファイルを元に戻す
2. 新しいマイグレーションを作成して修正内容を反映

### 連番が飛んでいる

```bash
# 整合性チェック
python migration_manager.py order_management.db --validate
```

欠番がある場合は、連番を詰めて修正してください。

## 実行順序

マイグレーションは以下の順序で実行されます：

1. schema_versionsテーブルの作成（自動）
2. 未実行のマイグレーションをバージョン順に取得
3. トランザクション開始
4. SQLを順次実行
5. schema_versionsに記録
6. コミット（エラー時はロールバック）

## Git管理

- ✅ **マイグレーションファイル（*.sql）**: Git管理
- ✅ **ロールバックファイル**: Git管理
- ❌ **データベースファイル（*.db）**: Git管理外
- ❌ **バックアップファイル**: Git管理外

## 関連ファイル

- [migration_manager.py](../migration_manager.py) - マイグレーション管理システム本体
- [init_database.py](../init_database.py) - 初期セットアップスクリプト
- [create_migration.py](../create_migration.py) - 新規マイグレーション作成ヘルパー
- [README_DATABASE.md](../README_DATABASE.md) - データベース管理ガイド
