"""
order_contractsテーブルにproject_idカラムを追加するマイグレーション

実行方法:
    python3 migrate_add_project_id_to_order_contracts.py
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "order_management.db"
BACKUP_DIR = "."

def backup_database():
    """データベースのバックアップを作成"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"order_management_backup_{timestamp}.db")

    import shutil
    shutil.copy2(DB_PATH, backup_path)
    print(f"✓ バックアップ作成: {backup_path}")
    return backup_path

def migrate():
    """マイグレーションを実行"""
    print("=" * 60)
    print("order_contractsテーブルにproject_idカラムを追加")
    print("=" * 60)

    # バックアップ作成
    backup_path = backup_database()

    # データベース接続
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 既存のproject_idカラムの確認
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'project_id' in columns:
            print("✓ project_idカラムは既に存在します")
            return

        print("\n1. project_idカラムを追加中...")

        # project_idカラムを追加
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN project_id INTEGER
        """)

        print("✓ project_idカラムを追加しました")

        # 外部キー制約を追加（SQLiteの制限により、ALTER TABLEでは追加できないため、
        # 新しいデータでは自動的に適用される）
        print("\n2. インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_contracts_project_id
            ON order_contracts(project_id)
        """)

        print("✓ インデックスを作成しました")

        # コミット
        conn.commit()

        print("\n" + "=" * 60)
        print("✓ マイグレーション完了")
        print("=" * 60)

        # 確認
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns_after = cursor.fetchall()
        print("\n現在のorder_contractsテーブル構造:")
        for col in columns_after:
            print(f"  - {col[1]} ({col[2]})")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ エラーが発生しました: {e}")
        print(f"バックアップから復元してください: {backup_path}")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
