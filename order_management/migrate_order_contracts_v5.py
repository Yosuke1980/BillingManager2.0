"""発注書マスタ（order_contracts）のマイグレーション V5

費用項目ごとの管理に対応:
1. project_id カラムを追加（案件ID）
2. item_name カラムを追加（費用項目名: 例「山田太郎出演料」）
3. order_status の値を更新（「未」→「未完了」、「済」→「完了」）
"""

import sqlite3
import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log_message


def migrate_v5():
    """マイグレーションV5を実行"""
    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()

    try:
        # 1. project_id カラムを追加
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN project_id INTEGER")
            log_message("order_contracts テーブルに project_id カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("project_id カラムは既に存在します")
            else:
                raise

        # 2. item_name カラムを追加
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN item_name TEXT")
            log_message("order_contracts テーブルに item_name カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("item_name カラムは既に存在します")
            else:
                raise

        # 3. 既存データの order_status を更新
        cursor.execute("""
            UPDATE order_contracts
            SET order_status = '未完了'
            WHERE order_status = '未'
        """)
        updated_uncompleted = cursor.rowcount
        log_message(f"order_status を「未」→「未完了」に更新: {updated_uncompleted}件")

        cursor.execute("""
            UPDATE order_contracts
            SET order_status = '完了'
            WHERE order_status = '済'
        """)
        updated_completed = cursor.rowcount
        log_message(f"order_status を「済」→「完了」に更新: {updated_completed}件")

        conn.commit()
        log_message("マイグレーションV5が正常に完了しました")
        return True

    except Exception as e:
        conn.rollback()
        log_message(f"マイグレーションV5でエラーが発生しました: {e}")
        import traceback
        log_message(traceback.format_exc())
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("発注書マスタ マイグレーション V5 を実行します...")
    success = migrate_v5()
    if success:
        print("✅ マイグレーション完了")
    else:
        print("❌ マイグレーション失敗")
