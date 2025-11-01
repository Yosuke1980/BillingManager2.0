"""発注契約テーブルのマイグレーション V4

レギュラー番組の契約条件（回数ベース/月額ベース、支払タイミング）に対応するため、
order_contractsテーブルに新しいカラムを追加します。
"""
import sqlite3
import os
from datetime import datetime

def migrate_order_contracts_v4(db_path="order_management.db"):
    """発注契約テーブルに契約条件カラムを追加"""

    print(f"発注契約テーブル V4 マイグレーションを開始: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 既にpayment_typeカラムが存在するかチェック
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'payment_type' in columns:
            print("契約条件カラムは既に存在します。マイグレーションをスキップします。")
            return True

        print("新しいカラムを追加中...")

        # 各カラムを追加
        cursor.execute("ALTER TABLE order_contracts ADD COLUMN payment_type TEXT DEFAULT '月額固定'")
        cursor.execute("ALTER TABLE order_contracts ADD COLUMN unit_price REAL")
        cursor.execute("ALTER TABLE order_contracts ADD COLUMN payment_timing TEXT DEFAULT '翌月末払い'")

        # 既存データはデフォルト値で問題なし（月額固定・翌月末払い）

        conn.commit()
        print("✅ 発注契約テーブル V4 マイグレーションが完了しました")

        # 追加されたカラムを確認
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns = cursor.fetchall()
        print("\n追加されたカラム:")
        for col in columns:
            if col[1] in ['payment_type', 'unit_price', 'payment_timing']:
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

    if migrate_order_contracts_v4(db_path):
        print("\n✅ マイグレーション成功")
        sys.exit(0)
    else:
        print("\n❌ マイグレーション失敗")
        sys.exit(1)
