#!/usr/bin/env python3
"""
新規マイグレーションファイル作成ヘルパー

使用方法:
    python create_migration.py "マイグレーション名"

例:
    python create_migration.py "add_email_column_to_partners"
"""

import sys
import os
import re
from datetime import datetime


def get_next_version(migrations_dir):
    """次のバージョン番号を取得"""
    if not os.path.exists(migrations_dir):
        return 1

    existing_files = [f for f in os.listdir(migrations_dir)
                     if f.endswith('.sql') and re.match(r'^\d{3}_', f)]

    if not existing_files:
        return 1

    versions = [int(f[:3]) for f in existing_files]
    return max(versions) + 1


def generate_migration_template(version, name):
    """マイグレーションファイルのテンプレート生成"""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""-- マイグレーション: {name}
-- バージョン: {version:03d}
-- 作成日: {today}
-- 説明: TODO: ここに説明を記述

-- ここにSQLを記述
-- 例:
-- ALTER TABLE table_name ADD COLUMN column_name TEXT;
-- CREATE INDEX IF NOT EXISTS idx_name ON table_name(column_name);

"""


def generate_rollback_template(version, name):
    """ロールバックファイルのテンプレート生成"""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""-- ロールバック: {name}
-- バージョン: {version:03d}
-- 作成日: {today}

-- ここにロールバックSQLを記述
-- 例:
-- DROP INDEX IF EXISTS idx_name;
-- ALTER TABLE table_name DROP COLUMN column_name;

"""


def main():
    if len(sys.argv) < 2:
        print("使用方法: python create_migration.py \"マイグレーション名\"")
        print("\n例:")
        print("  python create_migration.py \"add_email_to_partners\"")
        return 1

    migration_name = sys.argv[1]
    migrations_dir = "migrations"

    # migrationsディレクトリが存在しない場合は作成
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)

    # rollbackディレクトリも作成
    rollback_dir = os.path.join(migrations_dir, "rollback")
    if not os.path.exists(rollback_dir):
        os.makedirs(rollback_dir)

    # 次のバージョン番号を取得
    next_version = get_next_version(migrations_dir)

    # ファイル名生成
    filename = f"{next_version:03d}_{migration_name}.sql"
    filepath = os.path.join(migrations_dir, filename)

    # マイグレーションファイル作成
    template = generate_migration_template(next_version, migration_name)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"✓ マイグレーションファイルを作成しました:")
    print(f"  {filepath}")

    # ロールバックファイル作成
    rollback_filename = f"{next_version:03d}_rollback.sql"
    rollback_filepath = os.path.join(rollback_dir, rollback_filename)

    rollback_template = generate_rollback_template(next_version, migration_name)
    with open(rollback_filepath, 'w', encoding='utf-8') as f:
        f.write(rollback_template)

    print(f"✓ ロールバックファイルを作成しました:")
    print(f"  {rollback_filepath}")

    print(f"\n次のステップ:")
    print(f"  1. {filepath} を編集してSQLを記述")
    print(f"  2. {rollback_filepath} も編集してロールバックSQLを記述")
    print(f"  3. git add {filepath} {rollback_filepath}")
    print(f"  4. git commit -m \"Add migration: {migration_name}\"")
    print(f"  5. git push")

    return 0


if __name__ == "__main__":
    sys.exit(main())
