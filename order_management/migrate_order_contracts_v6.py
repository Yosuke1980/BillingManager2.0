"""発注書マスタ（order_contracts）のマイグレーション V6

単発/レギュラー対応:
1. contract_type カラムを追加（発注種別: spot/regular_fixed/regular_count）
2. project_name_type カラムを追加（案件名の種別: program/custom）
3. custom_project_name カラムを追加（自由入力の案件名）
4. implementation_date カラムを追加（単発の実施日）
5. spot_amount カラムを追加（単発の金額）
"""

import sqlite3
import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import log_message


def migrate_v6():
    """マイグレーションV6を実行"""
    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()

    try:
        # 1. contract_type カラムを追加
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN contract_type TEXT DEFAULT 'regular_fixed'")
            log_message("order_contracts テーブルに contract_type カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("contract_type カラムは既に存在します")
            else:
                raise

        # 2. project_name_type カラムを追加
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN project_name_type TEXT DEFAULT 'program'")
            log_message("order_contracts テーブルに project_name_type カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("project_name_type カラムは既に存在します")
            else:
                raise

        # 3. custom_project_name カラムを追加
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN custom_project_name TEXT")
            log_message("order_contracts テーブルに custom_project_name カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("custom_project_name カラムは既に存在します")
            else:
                raise

        # 4. implementation_date カラムを追加（単発の実施日）
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN implementation_date DATE")
            log_message("order_contracts テーブルに implementation_date カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("implementation_date カラムは既に存在します")
            else:
                raise

        # 5. spot_amount カラムを追加（単発の金額）
        try:
            cursor.execute("ALTER TABLE order_contracts ADD COLUMN spot_amount REAL")
            log_message("order_contracts テーブルに spot_amount カラムを追加しました")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                log_message("spot_amount カラムは既に存在します")
            else:
                raise

        # 6. 既存データのデフォルト値設定
        cursor.execute("""
            UPDATE order_contracts
            SET contract_type = 'regular_fixed'
            WHERE contract_type IS NULL
        """)
        updated_count = cursor.rowcount
        log_message(f"既存レコードのcontract_typeをデフォルト値に設定: {updated_count}件")

        cursor.execute("""
            UPDATE order_contracts
            SET project_name_type = 'program'
            WHERE project_name_type IS NULL
        """)
        updated_count = cursor.rowcount
        log_message(f"既存レコードのproject_name_typeをデフォルト値に設定: {updated_count}件")

        conn.commit()
        log_message("マイグレーションV6が正常に完了しました")
        return True

    except Exception as e:
        conn.rollback()
        log_message(f"マイグレーションV6でエラーが発生しました: {e}")
        import traceback
        log_message(traceback.format_exc())
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("発注書マスタ マイグレーション V6 を実行します...")
    success = migrate_v6()
    if success:
        print("✅ マイグレーション完了")
    else:
        print("❌ マイグレーション失敗")
