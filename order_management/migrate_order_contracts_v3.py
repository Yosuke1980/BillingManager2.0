"""発注明細テーブルのマイグレーション V3

発注・支払照合機能に対応するため、expenses_orderテーブルに
支払追跡用のカラムを追加します。
"""
import sqlite3
import os
from datetime import datetime

def migrate_expenses_order_v3(db_path="order_management.db"):
    """発注明細テーブルに支払追跡カラムを追加"""

    print(f"発注明細テーブル V3 マイグレーションを開始: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 既にexpected_payment_dateカラムが存在するかチェック
        cursor.execute("PRAGMA table_info(expenses_order)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'expected_payment_date' in columns:
            print("支払追跡カラムは既に存在します。マイグレーションをスキップします。")
            return True

        print("新しいカラムを追加中...")

        # 各カラムを追加
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN expected_payment_date DATE")
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN expected_payment_amount REAL")
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN payment_matched_id INTEGER")
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN payment_status TEXT DEFAULT '未払い'")
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN payment_verified_date DATE")
        cursor.execute("ALTER TABLE expenses_order ADD COLUMN payment_difference REAL DEFAULT 0")

        # 既存データのexpected_payment_dateとexpected_payment_amountを設定
        # payment_scheduled_dateとamountから初期値を設定
        cursor.execute("""
            UPDATE expenses_order
            SET expected_payment_date = payment_scheduled_date,
                expected_payment_amount = amount
            WHERE expected_payment_date IS NULL
        """)

        conn.commit()
        print("✅ 発注明細テーブル V3 マイグレーションが完了しました")

        # 追加されたカラムを確認
        cursor.execute("PRAGMA table_info(expenses_order)")
        columns = cursor.fetchall()
        print("\n追加されたカラム:")
        for col in columns:
            if col[1] in ['expected_payment_date', 'expected_payment_amount', 'payment_matched_id',
                          'payment_status', 'payment_verified_date', 'payment_difference']:
                print(f"  - {col[1]} ({col[2]})")

        return True

    except Exception as e:
        print(f"❌ マイグレーションエラー: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # スクリプトが直接実行された場合
    import sys

    # デフォルトのDBパス
    default_db_path = os.path.join(os.path.dirname(__file__), "..", "order_management.db")

    # コマンドライン引数でDBパスを指定可能
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path

    print(f"使用するデータベース: {db_path}")

    if migrate_expenses_order_v3(db_path):
        print("\n✅ マイグレーション成功")
        sys.exit(0)
    else:
        print("\n❌ マイグレーション失敗")
        sys.exit(1)
