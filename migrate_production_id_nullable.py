"""production_idカラムをNULL許可に変更するマイグレーション

発注データCSVインポート時に番組が未登録でもデータを取り込めるようにするため、
order_contractsテーブルのproduction_idカラムをNULL許可に変更します。
"""
import sqlite3
import shutil
from datetime import datetime


def migrate_production_id_nullable():
    """production_idをNULL許可に変更"""
    db_path = "order_management.db"

    # バックアップ作成
    backup_path = f"order_management_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(db_path, backup_path)
    print(f"✓ データベースバックアップ作成: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("\n=== production_id NULL許可マイグレーション開始 ===\n")

        # 1. 新しいテーブルを作成（production_idをNULL許可に）
        print("1. 新しいorder_contractsテーブルを作成中...")
        cursor.execute("""
            CREATE TABLE order_contracts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_id INTEGER,  -- NOT NULL制約を削除
                partner_id INTEGER NOT NULL,
                contract_start_date DATE NOT NULL,
                contract_end_date DATE NOT NULL,
                contract_period_type TEXT DEFAULT '半年',
                pdf_status TEXT DEFAULT '未配布',
                pdf_file_path TEXT,
                pdf_distributed_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                order_type TEXT DEFAULT '発注書',
                order_status TEXT DEFAULT '未',
                email_sent_date DATE,
                payment_type TEXT DEFAULT '月額固定',
                unit_price REAL,
                payment_timing TEXT DEFAULT '翌月末払い',
                item_name TEXT,
                contract_type TEXT DEFAULT 'regular_fixed',
                project_name_type TEXT DEFAULT 'program',
                implementation_date DATE,
                spot_amount REAL,
                order_category TEXT DEFAULT 'レギュラー制作発注書',
                email_subject TEXT,
                email_body TEXT,
                email_to TEXT,
                auto_renewal_enabled INTEGER DEFAULT 1,
                renewal_period_months INTEGER DEFAULT 3,
                termination_notice_date DATE,
                last_renewal_date DATE,
                renewal_count INTEGER DEFAULT 0,
                work_type TEXT DEFAULT '制作',
                FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            )
        """)
        print("   ✓ 新テーブル作成完了")

        # 2. データをコピー
        print("\n2. 既存データを新テーブルにコピー中...")
        cursor.execute("""
            INSERT INTO order_contracts_new
            SELECT * FROM order_contracts
        """)

        # コピーされた件数を確認
        cursor.execute("SELECT COUNT(*) FROM order_contracts_new")
        count = cursor.fetchone()[0]
        print(f"   ✓ {count}件のデータをコピー完了")

        # 3. 旧テーブルを削除
        print("\n3. 旧テーブルを削除中...")
        cursor.execute("DROP TABLE order_contracts")
        print("   ✓ 旧テーブル削除完了")

        # 4. 新テーブルをリネーム
        print("\n4. 新テーブルをorder_contractsにリネーム中...")
        cursor.execute("ALTER TABLE order_contracts_new RENAME TO order_contracts")
        print("   ✓ リネーム完了")

        # 5. インデックスを再作成（必要に応じて）
        print("\n5. インデックスを作成中...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_contracts_production_id
            ON order_contracts(production_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_contracts_partner_id
            ON order_contracts(partner_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_contracts_dates
            ON order_contracts(contract_start_date, contract_end_date)
        """)
        print("   ✓ インデックス作成完了")

        conn.commit()
        print("\n=== マイグレーション完了 ===")
        print(f"\n変更内容:")
        print("  - order_contracts.production_id: NOT NULL → NULL許可")
        print(f"  - 移行データ数: {count}件")
        print(f"  - バックアップ: {backup_path}")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ エラーが発生しました: {e}")
        print(f"バックアップから復元してください: {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_production_id_nullable()
