"""契約・発注統合管理システムへの移行スクリプト

既存の order_contracts と expenses_order を
新しい contracts と expense_items に移行します。
"""
import sqlite3
import sys
from datetime import datetime


def create_new_tables(cursor):
    """新しいテーブルを作成"""
    print("新しいテーブルを作成中...")

    # contracts（契約管理テーブル）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 基本情報
            production_id INTEGER,
            project_id INTEGER,
            partner_id INTEGER NOT NULL,
            work_type TEXT DEFAULT '制作',

            -- 契約内容
            item_name TEXT NOT NULL,
            contract_type TEXT DEFAULT 'regular_fixed',

            -- 契約期間
            contract_start_date DATE NOT NULL,
            contract_end_date DATE NOT NULL,
            contract_period_type TEXT DEFAULT '半年',

            -- 金額・支払条件
            payment_type TEXT DEFAULT '月額固定',
            unit_price REAL,
            spot_amount REAL,
            payment_timing TEXT DEFAULT '翌月末払い',

            -- 書類管理
            document_type TEXT DEFAULT '発注書',
            document_status TEXT DEFAULT '未',
            pdf_file_path TEXT,

            -- メール送信
            email_to TEXT,
            email_subject TEXT,
            email_body TEXT,
            email_sent_date DATE,

            -- 自動延長設定
            auto_renewal_enabled INTEGER DEFAULT 1,
            renewal_period_months INTEGER DEFAULT 3,
            termination_notice_date DATE,
            last_renewal_date DATE,
            renewal_count INTEGER DEFAULT 0,

            -- その他
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
            FOREIGN KEY (partner_id) REFERENCES partners(id)
        )
    """)

    # インデックス作成
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_production ON contracts(production_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_partner ON contracts(partner_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_dates ON contracts(contract_start_date, contract_end_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contracts_work_type ON contracts(work_type)")

    # expense_items（費用項目テーブル）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- 契約との紐付け
            contract_id INTEGER,

            -- 基本情報
            production_id INTEGER NOT NULL,
            partner_id INTEGER,
            item_name TEXT NOT NULL,

            -- 金額
            amount REAL NOT NULL,

            -- 実施・発注情報
            implementation_date DATE,
            order_number TEXT UNIQUE,
            order_date DATE,
            status TEXT DEFAULT '発注予定',

            -- 請求・支払情報
            invoice_received_date DATE,
            expected_payment_date DATE,
            expected_payment_amount REAL,
            payment_scheduled_date DATE,
            payment_date DATE,
            payment_status TEXT DEFAULT '未払い',
            payment_verified_date DATE,
            payment_matched_id INTEGER,
            payment_difference REAL DEFAULT 0,

            -- メール・通信
            gmail_draft_id TEXT,
            gmail_message_id TEXT,
            email_sent_at TIMESTAMP,

            -- その他
            contact_person TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
            FOREIGN KEY (production_id) REFERENCES productions(id) ON DELETE CASCADE,
            FOREIGN KEY (partner_id) REFERENCES partners(id)
        )
    """)

    # インデックス作成
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_items_contract ON expense_items(contract_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_items_production ON expense_items(production_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_items_partner ON expense_items(partner_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_items_payment_date ON expense_items(expected_payment_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_items_status ON expense_items(status, payment_status)")

    print("  ✓ contracts テーブル作成完了")
    print("  ✓ expense_items テーブル作成完了")


def migrate_contracts(cursor):
    """order_contracts → contracts への移行"""
    print("\n契約データを移行中...")

    cursor.execute("SELECT COUNT(*) FROM order_contracts")
    count = cursor.fetchone()[0]
    print(f"  移行対象: {count}件")

    cursor.execute("""
        INSERT INTO contracts (
            id, production_id, project_id, partner_id, work_type,
            item_name, contract_type,
            contract_start_date, contract_end_date, contract_period_type,
            payment_type, unit_price, spot_amount, payment_timing,
            document_type, document_status, pdf_file_path,
            email_to, email_subject, email_body, email_sent_date,
            auto_renewal_enabled, renewal_period_months,
            termination_notice_date, last_renewal_date, renewal_count,
            notes, created_at, updated_at
        )
        SELECT
            id, production_id, project_id, partner_id, work_type,
            item_name, contract_type,
            contract_start_date, contract_end_date, contract_period_type,
            payment_type, unit_price, spot_amount, payment_timing,
            order_type, order_status, pdf_file_path,
            email_to, email_subject, email_body, email_sent_date,
            auto_renewal_enabled, renewal_period_months,
            termination_notice_date, last_renewal_date, renewal_count,
            notes, created_at, updated_at
        FROM order_contracts
    """)

    migrated = cursor.rowcount
    print(f"  ✓ {migrated}件の契約を移行完了")
    return migrated


def migrate_expenses(cursor):
    """expenses_order → expense_items への移行"""
    print("\n費用項目データを移行中...")

    cursor.execute("SELECT COUNT(*) FROM expenses_order")
    count = cursor.fetchone()[0]
    print(f"  移行対象: {count}件")

    # supplier_id → partner_id として移行
    cursor.execute("""
        INSERT INTO expense_items (
            id, production_id, partner_id, item_name, amount,
            implementation_date, order_number, order_date, status,
            invoice_received_date, expected_payment_date,
            expected_payment_amount, payment_scheduled_date,
            payment_date, payment_status, payment_verified_date,
            payment_matched_id, payment_difference,
            gmail_draft_id, gmail_message_id, email_sent_at,
            contact_person, notes, created_at, updated_at
        )
        SELECT
            id, production_id, supplier_id, item_name, amount,
            implementation_date, order_number, order_date, status,
            invoice_received_date, expected_payment_date,
            expected_payment_amount, payment_scheduled_date,
            payment_date, payment_status, payment_verified_date,
            payment_matched_id, payment_difference,
            gmail_draft_id, gmail_message_id, email_sent_at,
            contact_person, notes, created_at, updated_at
        FROM expenses_order
    """)

    migrated = cursor.rowcount
    print(f"  ✓ {migrated}件の費用項目を移行完了")

    # contract_id の自動推定と紐付け
    print("\n  費用項目と契約の自動紐付け中...")
    cursor.execute("""
        UPDATE expense_items
        SET contract_id = (
            SELECT c.id
            FROM contracts c
            WHERE c.production_id = expense_items.production_id
              AND c.partner_id = expense_items.partner_id
              AND c.item_name = expense_items.item_name
              AND expense_items.implementation_date BETWEEN c.contract_start_date AND c.contract_end_date
            LIMIT 1
        )
        WHERE contract_id IS NULL
    """)

    linked = cursor.rowcount
    print(f"  ✓ {linked}件の費用項目を契約に紐付けました")

    return migrated


def rename_old_tables(cursor):
    """旧テーブルをリネーム（バックアップ）"""
    print("\n旧テーブルをバックアップ中...")

    # 既存のバックアップテーブルがあれば削除
    cursor.execute("DROP TABLE IF EXISTS order_contracts_old")
    cursor.execute("DROP TABLE IF EXISTS expenses_order_old")

    # リネーム
    cursor.execute("ALTER TABLE order_contracts RENAME TO order_contracts_old")
    cursor.execute("ALTER TABLE expenses_order RENAME TO expenses_order_old")

    print("  ✓ order_contracts → order_contracts_old")
    print("  ✓ expenses_order → expenses_order_old")


def verify_migration(cursor):
    """移行結果の検証"""
    print("\n移行結果を検証中...")

    cursor.execute("SELECT COUNT(*) FROM contracts")
    contracts_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM expense_items")
    expenses_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM expense_items WHERE contract_id IS NOT NULL")
    linked_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM order_contracts_old")
    old_contracts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM expenses_order_old")
    old_expenses = cursor.fetchone()[0]

    print(f"\n移行結果:")
    print(f"  contracts: {contracts_count}件（元: {old_contracts}件）")
    print(f"  expense_items: {expenses_count}件（元: {old_expenses}件）")
    print(f"  契約に紐付いた費用項目: {linked_count}件 / {expenses_count}件")

    if contracts_count == old_contracts and expenses_count == old_expenses:
        print("\n✅ すべてのデータが正常に移行されました")
        return True
    else:
        print("\n⚠️ データ数に差異があります")
        return False


def main():
    """メイン処理"""
    print("=" * 60)
    print("契約・発注統合管理システムへの移行")
    print("=" * 60)

    # データベース接続
    db_path = "order_management.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 新しいテーブルを作成
        create_new_tables(cursor)

        # 2. データを移行
        contracts_migrated = migrate_contracts(cursor)
        expenses_migrated = migrate_expenses(cursor)

        # 3. 旧テーブルをリネーム
        rename_old_tables(cursor)

        # 4. 検証
        if verify_migration(cursor):
            # コミット
            conn.commit()
            print("\n" + "=" * 60)
            print("✅ 移行が正常に完了しました")
            print("=" * 60)
            return 0
        else:
            print("\n" + "=" * 60)
            print("⚠️ 移行に問題がある可能性があります")
            print("変更はロールバックされます")
            print("=" * 60)
            conn.rollback()
            return 1

    except Exception as e:
        conn.rollback()
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
