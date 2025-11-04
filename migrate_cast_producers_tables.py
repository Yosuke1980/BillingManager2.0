"""production_cast と production_producers テーブルのカラムを修正

program_id → production_id にリネーム
"""
import sqlite3

def migrate_cast_producers_tables(db_path="order_management.db"):
    print("=" * 70)
    print("production_cast と production_producers のカラム修正")
    print("=" * 70)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. production_cast の修正
        print("\n1. production_cast テーブルを修正中...")

        # 新しいテーブルを作成
        cursor.execute("""
            CREATE TABLE production_cast_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_id INTEGER NOT NULL,
                cast_id INTEGER NOT NULL,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
                FOREIGN KEY (cast_id) REFERENCES cast(id)
            )
        """)

        # データをコピー
        cursor.execute("""
            INSERT INTO production_cast_new (id, production_id, cast_id, role, created_at)
            SELECT id, program_id, cast_id, role, created_at
            FROM production_cast
        """)

        # テーブル入れ替え
        cursor.execute("DROP TABLE production_cast")
        cursor.execute("ALTER TABLE production_cast_new RENAME TO production_cast")

        print("   ✓ production_cast テーブル修正完了")

        # 2. production_producers の修正
        print("\n2. production_producers テーブルを修正中...")

        # 新しいテーブルを作成
        cursor.execute("""
            CREATE TABLE production_producers_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                production_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            )
        """)

        # データをコピー
        cursor.execute("""
            INSERT INTO production_producers_new (id, production_id, partner_id, created_at)
            SELECT id, program_id, partner_id, created_at
            FROM production_producers
        """)

        # テーブル入れ替え
        cursor.execute("DROP TABLE production_producers")
        cursor.execute("ALTER TABLE production_producers_new RENAME TO production_producers")

        print("   ✓ production_producers テーブル修正完了")

        conn.commit()

        print("\n" + "=" * 70)
        print("マイグレーション成功!")
        print("=" * 70)

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_cast_producers_tables()
