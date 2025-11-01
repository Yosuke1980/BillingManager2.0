"""発注マスタテーブルのマイグレーション V2

3種類の発注管理（契約書・発注書・メール発注）に対応するため、
order_contractsテーブルに新しいカラムを追加します。
"""
import sqlite3
import os
from datetime import datetime


def migrate_order_contracts_v2(db_path="order_management.db"):
    """発注マスタテーブルに発注種別とメール関連カラムを追加"""

    print(f"発注マスタテーブル V2 マイグレーションを開始: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # テーブル存在確認
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='order_contracts'
        """)

        if not cursor.fetchone():
            print("エラー: order_contractsテーブルが存在しません。先にV1マイグレーションを実行してください。")
            return False

        # 既にorder_typeカラムが存在するかチェック
        cursor.execute("PRAGMA table_info(order_contracts)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'order_type' in columns:
            print("発注種別カラムは既に存在します。マイグレーションをスキップします。")
            return True

        print("新しいカラムを追加中...")

        # 発注種別カラムを追加（デフォルト: '発注書'）
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN order_type TEXT DEFAULT '発注書'
        """)
        print("✅ order_type カラムを追加しました")

        # 発注ステータスカラムを追加（デフォルト: '未'）
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN order_status TEXT DEFAULT '未'
        """)
        print("✅ order_status カラムを追加しました")

        # メール件名カラムを追加
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN email_subject TEXT
        """)
        print("✅ email_subject カラムを追加しました")

        # メール本文カラムを追加
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN email_body TEXT
        """)
        print("✅ email_body カラムを追加しました")

        # メール送信日カラムを追加
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN email_sent_date DATE
        """)
        print("✅ email_sent_date カラムを追加しました")

        # メール送信先カラムを追加
        cursor.execute("""
            ALTER TABLE order_contracts
            ADD COLUMN email_to TEXT
        """)
        print("✅ email_to カラムを追加しました")

        # 既存データのorder_statusをpdf_statusから推測して更新
        # pdf_status が '受領確認済' なら '済'、それ以外は '未'
        cursor.execute("""
            UPDATE order_contracts
            SET order_status = CASE
                WHEN pdf_status = '受領確認済' THEN '済'
                ELSE '未'
            END
            WHERE order_status = '未'
        """)
        print("✅ 既存データのorder_statusを更新しました")

        conn.commit()

        print("✅ 発注マスタテーブル V2 マイグレーションが完了しました")
        return True

    except Exception as e:
        print(f"❌ マイグレーションエラー: {str(e)}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    # テスト実行
    db_path = "order_management.db"
    if os.path.exists(db_path):
        migrate_order_contracts_v2(db_path)
    else:
        print(f"データベースファイルが見つかりません: {db_path}")
        print("カレントディレクトリ:", os.getcwd())
