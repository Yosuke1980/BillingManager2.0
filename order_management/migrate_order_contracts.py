"""発注書マスタテーブルのマイグレーション

レギュラー番組の発注書管理機能を追加します。
発注書の期間管理、PDFファイル管理、配布ステータス管理を実現します。
"""
import sqlite3
import os
from datetime import datetime


def migrate_order_contracts(db_path="order_management.db"):
    """発注書マスタテーブルを作成"""

    print(f"発注書マスタテーブルのマイグレーションを開始: {db_path}")

    if not os.path.exists(db_path):
        print(f"エラー: データベースファイルが見つかりません: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 発注書マスタテーブルが既に存在するかチェック
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='order_contracts'
        """)

        if cursor.fetchone():
            print("発注書マスタテーブルは既に存在します。")
            return True

        # 発注書マスタテーブルを作成
        cursor.execute("""
            CREATE TABLE order_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                contract_start_date DATE NOT NULL,
                contract_end_date DATE NOT NULL,
                contract_period_type TEXT DEFAULT '半年',
                pdf_status TEXT DEFAULT '未配布',
                pdf_file_path TEXT,
                pdf_distributed_date DATE,
                confirmed_by TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            )
        """)

        print("✅ order_contracts テーブルを作成しました")

        # インデックスを作成
        cursor.execute("""
            CREATE INDEX idx_order_contracts_program
            ON order_contracts(program_id)
        """)

        cursor.execute("""
            CREATE INDEX idx_order_contracts_partner
            ON order_contracts(partner_id)
        """)

        cursor.execute("""
            CREATE INDEX idx_order_contracts_end_date
            ON order_contracts(contract_end_date)
        """)

        print("✅ インデックスを作成しました")

        conn.commit()

        print("✅ 発注書マスタテーブルのマイグレーションが完了しました")
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
        migrate_order_contracts(db_path)
    else:
        print(f"データベースファイルが見つかりません: {db_path}")
        print("カレントディレクトリ:", os.getcwd())
