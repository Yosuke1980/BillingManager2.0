"""契約テーブル削除とProductionsベース設計への移行マイグレーション

このスクリプトは以下の変更を実行します：
1. 新しいテーブルを作成
   - expense_templates (費用テンプレート)
   - production_partners (番組-制作会社関連)
   - expense_generation_log (費用生成ログ)

2. expense_itemsテーブルの変更
   - template_id カラム追加
   - cast_id カラム追加
   - generation_month カラム追加
   - contract_id カラム削除

3. 契約関連テーブルの削除
   - contracts
   - contract_cast
   - contract_renewal_history

4. インデックスの追加
"""

import sqlite3
import sys
from datetime import datetime
from utils import log_message


def backup_database(db_path):
    """データベースをバックアップ"""
    backup_path = db_path.replace('.db', f'_migration_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    import shutil
    shutil.copy2(db_path, backup_path)
    log_message(f"✓ データベースバックアップ作成: {backup_path}")
    return backup_path


def execute_migration(db_path='database/order_management.db', dry_run=False):
    """マイグレーションを実行

    Args:
        db_path: データベースファイルパス
        dry_run: Trueの場合、実行せずにSQLを表示のみ
    """

    if not dry_run:
        # バックアップ作成
        backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if dry_run:
            log_message("=== DRY RUN MODE (実行せずSQL表示のみ) ===\n")

        # ========================================
        # Step 1: 新しいテーブルを作成
        # ========================================

        log_message("Step 1: 新しいテーブルを作成中...")

        # 1.1 expense_templates テーブル
        sql_expense_templates = """
        CREATE TABLE IF NOT EXISTS expense_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 紐付け
            production_id INTEGER NOT NULL,
            partner_id INTEGER NOT NULL,
            cast_id INTEGER,

            -- 費用情報
            item_name TEXT NOT NULL,
            work_type TEXT DEFAULT '制作',
            amount REAL NOT NULL,

            -- 自動生成設定
            generation_type TEXT DEFAULT '月次',
            generation_day INTEGER DEFAULT 1,
            payment_timing TEXT DEFAULT '翌月末払い',
            auto_generate_enabled INTEGER DEFAULT 1,

            -- 期間
            start_date DATE,
            end_date DATE,

            -- その他
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
            FOREIGN KEY (partner_id) REFERENCES partners(id),
            FOREIGN KEY (cast_id) REFERENCES cast(id)
        );
        """

        if dry_run:
            print(sql_expense_templates)
        else:
            cursor.execute(sql_expense_templates)
            log_message("  ✓ expense_templates テーブル作成")

        # 1.2 production_partners テーブル
        sql_production_partners = """
        CREATE TABLE IF NOT EXISTS production_partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            production_id INTEGER NOT NULL,
            partner_id INTEGER NOT NULL,
            role TEXT DEFAULT '制作',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
            FOREIGN KEY (partner_id) REFERENCES partners(id),
            UNIQUE(production_id, partner_id)
        );
        """

        if dry_run:
            print(sql_production_partners)
        else:
            cursor.execute(sql_production_partners)
            log_message("  ✓ production_partners テーブル作成")

        # 1.3 expense_generation_log テーブル
        sql_expense_generation_log = """
        CREATE TABLE IF NOT EXISTS expense_generation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            generation_month TEXT NOT NULL,
            expense_item_id INTEGER,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (template_id) REFERENCES expense_templates(id) ON DELETE CASCADE,
            FOREIGN KEY (expense_item_id) REFERENCES expense_items(id) ON DELETE SET NULL,
            UNIQUE(template_id, generation_month)
        );
        """

        if dry_run:
            print(sql_expense_generation_log)
        else:
            cursor.execute(sql_expense_generation_log)
            log_message("  ✓ expense_generation_log テーブル作成")

        # ========================================
        # Step 2: expense_items テーブルにカラム追加
        # ========================================

        log_message("\nStep 2: expense_items テーブルにカラム追加中...")

        # 既存カラムをチェック
        cursor.execute("PRAGMA table_info(expense_items)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        # template_id カラム追加
        if 'template_id' not in existing_columns:
            sql_add_template_id = "ALTER TABLE expense_items ADD COLUMN template_id INTEGER REFERENCES expense_templates(id) ON DELETE SET NULL;"
            if dry_run:
                print(sql_add_template_id)
            else:
                cursor.execute(sql_add_template_id)
                log_message("  ✓ template_id カラム追加")
        else:
            log_message("  → template_id カラムは既に存在")

        # cast_id カラム追加
        if 'cast_id' not in existing_columns:
            sql_add_cast_id = "ALTER TABLE expense_items ADD COLUMN cast_id INTEGER REFERENCES cast(id);"
            if dry_run:
                print(sql_add_cast_id)
            else:
                cursor.execute(sql_add_cast_id)
                log_message("  ✓ cast_id カラム追加")
        else:
            log_message("  → cast_id カラムは既に存在")

        # generation_month カラム追加
        if 'generation_month' not in existing_columns:
            sql_add_generation_month = "ALTER TABLE expense_items ADD COLUMN generation_month TEXT;"
            if dry_run:
                print(sql_add_generation_month)
            else:
                cursor.execute(sql_add_generation_month)
                log_message("  ✓ generation_month カラム追加")
        else:
            log_message("  → generation_month カラムは既に存在")

        # ========================================
        # Step 3: インデックスを作成
        # ========================================

        log_message("\nStep 3: インデックスを作成中...")

        indexes = [
            ("idx_expense_templates_production", "expense_templates", "production_id"),
            ("idx_expense_templates_partner", "expense_templates", "partner_id"),
            ("idx_expense_templates_cast", "expense_templates", "cast_id"),
            ("idx_expense_templates_auto_generate", "expense_templates", "auto_generate_enabled, generation_type"),
            ("idx_production_partners_production", "production_partners", "production_id"),
            ("idx_production_partners_partner", "production_partners", "partner_id"),
            ("idx_expense_generation_template", "expense_generation_log", "template_id"),
            ("idx_expense_generation_month", "expense_generation_log", "generation_month"),
            ("idx_expense_items_template", "expense_items", "template_id"),
            ("idx_expense_items_cast", "expense_items", "cast_id"),
            ("idx_expense_items_generation_month", "expense_items", "generation_month"),
        ]

        for idx_name, table_name, columns in indexes:
            sql_create_index = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({columns});"
            if dry_run:
                print(sql_create_index)
            else:
                cursor.execute(sql_create_index)
                log_message(f"  ✓ {idx_name} 作成")

        # ========================================
        # Step 4: 契約関連テーブルを削除
        # ========================================

        log_message("\nStep 4: 契約関連テーブルを削除中...")

        tables_to_drop = [
            "contract_renewal_history",
            "contract_cast",
            "contracts"
        ]

        for table_name in tables_to_drop:
            # テーブルが存在するかチェック
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone():
                sql_drop = f"DROP TABLE IF EXISTS {table_name};"
                if dry_run:
                    print(sql_drop)
                else:
                    cursor.execute(sql_drop)
                    log_message(f"  ✓ {table_name} テーブル削除")
            else:
                log_message(f"  → {table_name} テーブルは存在しません")

        # ========================================
        # Step 5: expense_items.contract_id カラムを削除
        # ========================================

        log_message("\nStep 5: expense_items.contract_id カラムを削除中...")

        # SQLiteでカラム削除は再作成が必要
        if 'contract_id' in existing_columns:
            if not dry_run:
                # 1. 新しいテーブルを作成（contract_id なし）
                cursor.execute("""
                    CREATE TABLE expense_items_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        production_id INTEGER NOT NULL,
                        partner_id INTEGER,
                        cast_id INTEGER,
                        item_name TEXT NOT NULL,
                        work_type TEXT DEFAULT '制作',
                        amount REAL NOT NULL,
                        implementation_date DATE,
                        order_number TEXT UNIQUE,
                        order_date DATE,
                        status TEXT DEFAULT '発注予定',
                        invoice_received_date DATE,
                        expected_payment_date DATE,
                        expected_payment_amount REAL,
                        payment_scheduled_date DATE,
                        actual_payment_date DATE,
                        payment_status TEXT DEFAULT '未払い',
                        payment_verified_date DATE,
                        payment_matched_id INTEGER,
                        payment_difference REAL DEFAULT 0,
                        invoice_number TEXT,
                        withholding_tax REAL,
                        consumption_tax REAL,
                        payment_amount REAL,
                        invoice_file_path TEXT,
                        payment_method TEXT,
                        approver TEXT,
                        approval_date DATE,
                        gmail_draft_id TEXT,
                        gmail_message_id TEXT,
                        email_sent_at TIMESTAMP,
                        contact_person TEXT,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        template_id INTEGER,
                        generation_month TEXT,
                        FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
                        FOREIGN KEY (partner_id) REFERENCES partners(id),
                        FOREIGN KEY (cast_id) REFERENCES cast(id),
                        FOREIGN KEY (template_id) REFERENCES expense_templates(id) ON DELETE SET NULL
                    )
                """)

                # 2. データをコピー（contract_id 以外）
                cursor.execute("""
                    INSERT INTO expense_items_new
                    SELECT
                        id, production_id, partner_id, cast_id, item_name, work_type, amount,
                        implementation_date, order_number, order_date, status,
                        invoice_received_date, expected_payment_date, expected_payment_amount,
                        payment_scheduled_date, actual_payment_date, payment_status,
                        payment_verified_date, payment_matched_id, payment_difference,
                        invoice_number, withholding_tax, consumption_tax, payment_amount,
                        invoice_file_path, payment_method, approver, approval_date,
                        gmail_draft_id, gmail_message_id, email_sent_at,
                        contact_person, notes, created_at, updated_at,
                        template_id, generation_month
                    FROM expense_items
                """)

                # 3. 古いテーブルを削除
                cursor.execute("DROP TABLE expense_items")

                # 4. 新しいテーブルをリネーム
                cursor.execute("ALTER TABLE expense_items_new RENAME TO expense_items")

                log_message("  ✓ contract_id カラム削除（テーブル再作成）")
            else:
                print("-- expense_items テーブル再作成（contract_id カラム削除）")
        else:
            log_message("  → contract_id カラムは既に存在しません")

        # ========================================
        # Step 6: スキーマバージョンを記録
        # ========================================

        log_message("\nStep 6: スキーマバージョンを記録中...")

        if not dry_run:
            cursor.execute("""
                INSERT INTO schema_versions (version, migration_name, success)
                VALUES (?, ?, ?)
            """, (8, 'remove_contracts_add_templates', 1))
            log_message("  ✓ スキーマバージョン 8 を記録")

        # コミット
        if not dry_run:
            conn.commit()
            log_message("\n✅ マイグレーション完了！")
        else:
            log_message("\n=== DRY RUN 完了（実際の変更は行われていません） ===")

        return True

    except Exception as e:
        if not dry_run:
            conn.rollback()
        log_message(f"\n❌ マイグレーションエラー: {e}")
        import traceback
        log_message(traceback.format_exc())
        return False

    finally:
        conn.close()


def verify_migration(db_path='database/order_management.db'):
    """マイグレーション結果を検証"""
    log_message("\n=== マイグレーション検証 ===")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 新しいテーブルの存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        expected_new_tables = ['expense_templates', 'production_partners', 'expense_generation_log']
        expected_deleted_tables = ['contracts', 'contract_cast', 'contract_renewal_history']

        log_message("\n新規テーブル:")
        for table in expected_new_tables:
            if table in tables:
                log_message(f"  ✓ {table} - 存在")
            else:
                log_message(f"  ✗ {table} - 存在しない（エラー）")

        log_message("\n削除テーブル:")
        for table in expected_deleted_tables:
            if table not in tables:
                log_message(f"  ✓ {table} - 削除済み")
            else:
                log_message(f"  ✗ {table} - まだ存在（エラー）")

        # expense_items のカラム確認
        log_message("\nexpense_items テーブルのカラム:")
        cursor.execute("PRAGMA table_info(expense_items)")
        columns = [row[1] for row in cursor.fetchall()]

        expected_new_columns = ['template_id', 'cast_id', 'generation_month']
        for col in expected_new_columns:
            if col in columns:
                log_message(f"  ✓ {col} - 存在")
            else:
                log_message(f"  ✗ {col} - 存在しない（エラー）")

        if 'contract_id' not in columns:
            log_message(f"  ✓ contract_id - 削除済み")
        else:
            log_message(f"  ✗ contract_id - まだ存在（エラー）")

        # データ件数確認
        log_message("\nデータ件数:")
        cursor.execute("SELECT COUNT(*) FROM expense_items")
        count = cursor.fetchone()[0]
        log_message(f"  expense_items: {count}件")

        cursor.execute("SELECT COUNT(*) FROM productions")
        count = cursor.fetchone()[0]
        log_message(f"  productions: {count}件")

        cursor.execute("SELECT COUNT(*) FROM partners")
        count = cursor.fetchone()[0]
        log_message(f"  partners: {count}件")

        log_message("\n✅ 検証完了")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='契約テーブル削除マイグレーション')
    parser.add_argument('--dry-run', action='store_true', help='実行せずにSQLを表示のみ')
    parser.add_argument('--verify', action='store_true', help='マイグレーション結果を検証')
    parser.add_argument('--db', default='database/order_management.db', help='データベースファイルパス')

    args = parser.parse_args()

    if args.verify:
        verify_migration(args.db)
    else:
        success = execute_migration(args.db, args.dry_run)

        if success and not args.dry_run:
            verify_migration(args.db)
            sys.exit(0)
        elif not success:
            log_message("\n⚠️ マイグレーション失敗")
            sys.exit(1)
