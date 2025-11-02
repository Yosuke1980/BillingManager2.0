"""order_contracts テーブルに order_category カラムを追加

発注種別を4分類に対応:
- レギュラー出演契約書
- レギュラー制作発注書
- 単発出演発注書
- 単発制作発注書
"""
import sqlite3
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def migrate():
    """マイグレーション実行"""
    # プロジェクトルートのorder_management.dbを使用
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "order_management.db")

    print(f"マイグレーションを開始します: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # order_category カラムの追加確認
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns = [column[1] for column in cursor.fetchall()]

        if "order_category" not in columns:
            print("order_category カラムを追加しています...")
            cursor.execute("""
                ALTER TABLE order_contracts
                ADD COLUMN order_category TEXT DEFAULT 'レギュラー制作発注書'
            """)
            print("✓ order_category カラムを追加しました")
        else:
            print("✓ order_category カラムは既に存在します")

        # 既存データのマイグレーション
        # contract_typeとorder_typeから推定
        print("\n既存データを更新しています...")

        # contract_type が 'spot' の場合は単発
        cursor.execute("""
            UPDATE order_contracts
            SET order_category = CASE
                WHEN contract_type = 'spot' THEN '単発制作発注書'
                WHEN order_type = '契約書' THEN 'レギュラー出演契約書'
                ELSE 'レギュラー制作発注書'
            END
            WHERE order_category = 'レギュラー制作発注書'
        """)

        updated_count = cursor.rowcount
        print(f"✓ {updated_count}件のレコードを更新しました")

        conn.commit()
        print("\nマイグレーション完了！")

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
