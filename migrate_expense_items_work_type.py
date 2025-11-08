"""データベースマイグレーション: expense_itemsテーブルにwork_typeカラムを追加

このスクリプトは、既存のorder_management.dbにwork_typeカラムを追加します。

実行方法:
    python migrate_expense_items_work_type.py

または、アプリ起動時に自動で実行されます。
"""
import sqlite3
import os


def check_column_exists(cursor, table_name, column_name):
    """テーブルに指定したカラムが存在するかチェック"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_add_work_type():
    """expense_itemsテーブルにwork_typeカラムを追加"""
    db_path = 'order_management.db'

    if not os.path.exists(db_path):
        print(f"❌ データベースファイル '{db_path}' が見つかりません")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # work_typeカラムが既に存在するかチェック
        if check_column_exists(cursor, 'expense_items', 'work_type'):
            print("✓ work_typeカラムは既に存在します。マイグレーション不要です。")
            return True

        print("📝 expense_itemsテーブルにwork_typeカラムを追加中...")

        # work_typeカラムを追加
        cursor.execute("""
            ALTER TABLE expense_items
            ADD COLUMN work_type TEXT DEFAULT '制作'
        """)

        print("✓ work_typeカラムを追加しました")

        # 既存データを契約から更新
        print("📝 既存データのwork_typeを契約から設定中...")
        cursor.execute("""
            UPDATE expense_items
            SET work_type = (
                SELECT c.work_type
                FROM contracts c
                WHERE c.id = expense_items.contract_id
            )
            WHERE expense_items.contract_id IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM contracts c
                WHERE c.id = expense_items.contract_id
              )
        """)

        updated_count = cursor.rowcount
        print(f"✓ {updated_count}件のwork_typeを更新しました")

        # 統計を表示
        cursor.execute("SELECT work_type, COUNT(*) FROM expense_items GROUP BY work_type")
        stats = cursor.fetchall()
        print("\n【更新後の統計】")
        for work_type, count in stats:
            print(f"  {work_type or '(null)'}: {count}件")

        conn.commit()
        print("\n✅ マイグレーション完了！")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ マイグレーション失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("データベースマイグレーション: work_typeカラム追加")
    print("=" * 60)
    print()

    success = migrate_add_work_type()

    if success:
        print("\n" + "=" * 60)
        print("マイグレーションが正常に完了しました")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("マイグレーションに失敗しました")
        print("=" * 60)
        exit(1)
