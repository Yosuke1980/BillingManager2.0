#!/usr/bin/env python3
"""
データベースのスキーマを最新版に更新する包括的なマイグレーションスクリプト
"""
import sqlite3
import os

# 必要なカラム定義（テーブル名: [(カラム名, 型, デフォルト値), ...]）
REQUIRED_COLUMNS = {
    'productions': [
        ('broadcast_days', 'TEXT', None),
        ('broadcast_time', 'TEXT', None),
        ('description', 'TEXT', None),
        ('end_date', 'DATE', None),
        ('end_time', 'TEXT', None),
        ('name', 'TEXT', None),
        ('parent_production_id', 'INTEGER', None),
        ('production_type', 'TEXT', "'レギュラー'"),
        ('start_date', 'DATE', None),
        ('start_time', 'TEXT', None),
        ('status', 'TEXT', "'進行中'"),
    ],
    'partners': [
        ('address', 'TEXT', None),
        ('code', 'TEXT', None),
        ('contact_person', 'TEXT', None),
        ('email', 'TEXT', None),
        ('name', 'TEXT', None),
        ('notes', 'TEXT', None),
        ('partner_type', 'TEXT', None),
        ('phone', 'TEXT', None),
    ],
    'contracts': [
        ('amount_pending', 'INTEGER', '0'),
        ('auto_renewal_enabled', 'INTEGER', '0'),
        ('contract_end_date', 'DATE', None),
        ('contract_period_type', 'TEXT', None),
        ('contract_start_date', 'DATE', None),
        ('contract_type', 'TEXT', None),
        ('document_status', 'TEXT', "'未完了'"),
        ('document_type', 'TEXT', None),
        ('email_body', 'TEXT', None),
        ('email_sent_date', 'DATE', None),
        ('email_subject', 'TEXT', None),
        ('email_to', 'TEXT', None),
        ('implementation_date', 'DATE', None),
        ('item_name', 'TEXT', None),
        ('last_renewal_date', 'DATE', None),
        ('notes', 'TEXT', None),
        ('order_category', 'TEXT', None),
        ('partner_id', 'INTEGER', None),
        ('payment_timing', 'TEXT', "'翌月末払い'"),
        ('payment_type', 'TEXT', None),
        ('pdf_distributed_date', 'DATE', None),
        ('pdf_file_path', 'TEXT', None),
        ('pdf_status', 'TEXT', "'未配布'"),
        ('production_id', 'INTEGER', None),
        ('project_id', 'INTEGER', None),
        ('project_name_type', 'TEXT', None),
        ('renewal_count', 'INTEGER', '0'),
        ('renewal_period_months', 'INTEGER', None),
        ('spot_amount', 'REAL', None),
        ('termination_notice_date', 'DATE', None),
        ('unit_price', 'REAL', None),
        ('work_type', 'TEXT', None),
    ],
    'expense_items': [
        ('actual_payment_date', 'DATE', None),
        ('amount', 'REAL', '0'),
        ('amount_pending', 'INTEGER', '0'),
        ('approval_date', 'DATE', None),
        ('approver', 'TEXT', None),
        ('archived', 'INTEGER', '0'),
        ('archived_date', 'DATE', None),
        ('consumption_tax', 'REAL', None),
        ('contact_person', 'TEXT', None),
        ('contract_id', 'INTEGER', None),
        ('corner_id', 'INTEGER', None),
        ('email_sent_at', 'TIMESTAMP', None),
        ('expected_payment_amount', 'REAL', None),
        ('expected_payment_date', 'DATE', None),
        ('gmail_draft_id', 'TEXT', None),
        ('gmail_message_id', 'TEXT', None),
        ('implementation_date', 'DATE', None),
        ('invoice_file_path', 'TEXT', None),
        ('invoice_number', 'TEXT', None),
        ('invoice_received_date', 'DATE', None),
        ('item_name', 'TEXT', None),
        ('notes', 'TEXT', None),
        ('order_date', 'DATE', None),
        ('order_number', 'TEXT', None),
        ('partner_id', 'INTEGER', None),
        ('payment_amount', 'REAL', None),
        ('payment_date', 'DATE', None),
        ('payment_difference', 'REAL', None),
        ('payment_matched_id', 'INTEGER', None),
        ('payment_method', 'TEXT', None),
        ('payment_scheduled_date', 'DATE', None),
        ('payment_status', 'TEXT', "'未払い'"),
        ('payment_verified_date', 'DATE', None),
        ('production_id', 'INTEGER', None),
        ('status', 'TEXT', "'発注予定'"),
        ('withholding_tax', 'REAL', None),
        ('work_type', 'TEXT', None),
    ]
}

def migrate_table(cursor, table_name, required_columns):
    """指定されたテーブルに不足しているカラムを追加"""
    # 現在のカラムを取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}

    added_columns = []

    for col_name, col_type, default_value in required_columns:
        if col_name not in existing_columns:
            # ALTER TABLE文を構築
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
            if default_value:
                alter_sql += f" DEFAULT {default_value}"

            try:
                cursor.execute(alter_sql)
                added_columns.append(col_name)
                print(f"  ✓ 追加: {col_name} ({col_type})")
            except sqlite3.OperationalError as e:
                print(f"  ✗ エラー: {col_name} - {e}")

    return added_columns

def migrate_database():
    """データベース全体をマイグレーション"""
    db_path = 'order_management.db'

    if not os.path.exists(db_path):
        print(f"エラー: {db_path} が見つかりません")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("=" * 70)
        print("データベース スキーマ マイグレーション")
        print("=" * 70)

        total_added = 0

        for table_name, required_columns in REQUIRED_COLUMNS.items():
            print(f"\n【{table_name} テーブル】")

            # 現在のカラム数を確認
            cursor.execute(f"PRAGMA table_info({table_name})")
            current_columns = cursor.fetchall()
            print(f"  現在のカラム数: {len(current_columns)}")

            # マイグレーション実行
            added = migrate_table(cursor, table_name, required_columns)

            if added:
                total_added += len(added)
                print(f"  → {len(added)} カラムを追加しました")
            else:
                print(f"  → すべてのカラムが存在します（マイグレーション不要）")

            # 更新後のカラム数
            cursor.execute(f"PRAGMA table_info({table_name})")
            updated_columns = cursor.fetchall()
            print(f"  更新後のカラム数: {len(updated_columns)}")

        conn.commit()

        print("\n" + "=" * 70)
        if total_added > 0:
            print(f"✓ マイグレーション完了！合計 {total_added} カラムを追加しました")
        else:
            print("✓ すべてのテーブルは最新です（マイグレーション不要）")
        print("=" * 70)

        return True

    except Exception as e:
        conn.rollback()
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()

    if success:
        print("\nアプリを起動してください: python app.py")
    else:
        print("\nマイグレーションに失敗しました")
