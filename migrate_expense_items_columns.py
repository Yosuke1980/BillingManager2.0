#!/usr/bin/env python3
"""
expense_itemsテーブルに不足しているカラムを追加するスクリプト

既存のカラムはスキップし、不足しているカラムのみ追加します。
"""

import sqlite3
import sys


def get_existing_columns(cursor, table_name):
    """テーブルの既存カラムを取得"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def add_missing_columns():
    """不足しているカラムを追加"""

    # 追加すべきカラムの定義
    columns_to_add = [
        ("actual_payment_date", "DATE"),
        ("invoice_number", "TEXT"),
        ("withholding_tax", "REAL"),
        ("consumption_tax", "REAL"),
        ("payment_amount", "REAL"),
        ("invoice_file_path", "TEXT"),
        ("payment_method", "TEXT"),
        ("approver", "TEXT"),
        ("approval_date", "DATE"),
        ("partner_id", "INTEGER"),
        ("contract_id", "INTEGER"),
        ("work_type", "TEXT DEFAULT '制作'"),
        ("expected_payment_date", "DATE"),
        ("payment_status", "TEXT DEFAULT '未払い'"),
        ("payment_verified_date", "DATE"),
        ("payment_matched_id", "INTEGER"),
        ("payment_difference", "REAL DEFAULT 0"),
        ("expected_payment_amount", "REAL"),
    ]

    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()

    try:
        # 既存カラムを取得
        existing_columns = get_existing_columns(cursor, "expense_items")
        print(f"既存カラム数: {len(existing_columns)}")

        # 不足しているカラムを追加
        added_count = 0
        skipped_count = 0

        for column_name, column_def in columns_to_add:
            if column_name in existing_columns:
                print(f"  ⊚ {column_name} - 既に存在（スキップ）")
                skipped_count += 1
            else:
                try:
                    sql = f"ALTER TABLE expense_items ADD COLUMN {column_name} {column_def}"
                    cursor.execute(sql)
                    print(f"  ✓ {column_name} - 追加完了")
                    added_count += 1
                except Exception as e:
                    print(f"  ✗ {column_name} - エラー: {e}")

        conn.commit()

        print(f"\n結果:")
        print(f"  追加: {added_count}カラム")
        print(f"  スキップ: {skipped_count}カラム")

        # 最終確認
        final_columns = get_existing_columns(cursor, "expense_items")
        print(f"\n最終カラム数: {len(final_columns)}")

        return added_count > 0

    except Exception as e:
        print(f"\nエラー: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    print("="*70)
    print("expense_itemsテーブル カラム追加スクリプト")
    print("="*70)

    success = add_missing_columns()

    if success:
        print("\n✅ カラム追加完了")
        print("\nアプリケーションを起動できます:")
        print("  python3 app.py")
        sys.exit(0)
    else:
        print("\n⚠️  変更なし（すべてのカラムが既に存在）")
        sys.exit(0)
