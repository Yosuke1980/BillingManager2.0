#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
費用項目データのインポートスクリプト
CSVファイルから費用項目データをexpense_itemsテーブルに上書きします
"""

import sqlite3
import csv
import sys
from datetime import datetime

def parse_date(date_str):
    """日付文字列をYYYY-MM-DD形式に変換"""
    if not date_str or date_str.strip() == '':
        return None

    try:
        # YYYY/MM/DD形式をYYYY-MM-DDに変換
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    except:
        pass

    return None

def parse_amount(amount_str):
    """金額文字列をfloatに変換"""
    if not amount_str or amount_str.strip() == '':
        return None

    try:
        return float(amount_str.strip())
    except:
        return None

def import_expense_items(csv_file_path, db_path):
    """CSVファイルから費用項目をインポート"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 既存のexpense_itemsテーブルの構造を確認
    cursor.execute("PRAGMA table_info(expense_items)")
    columns = cursor.fetchall()

    if not columns:
        print("エラー: expense_itemsテーブルが存在しません")
        conn.close()
        return False

    print("既存のexpense_itemsテーブル構造:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # 既存データを削除
    print("\n既存データを削除中...")
    cursor.execute("DELETE FROM expense_items")
    deleted_count = cursor.rowcount
    print(f"削除されたレコード数: {deleted_count}")

    # CSVファイルを読み込み
    print(f"\nCSVファイルを読み込み中: {csv_file_path}")

    imported_count = 0
    error_count = 0

    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # CSVの各フィールドをデータベースカラムにマッピング
                cursor.execute("""
                    INSERT INTO expense_items (
                        contract_id,
                        production_name,
                        partner_name,
                        item_name,
                        work_type,
                        amount,
                        execution_date,
                        order_number,
                        order_date,
                        status,
                        invoice_received_date,
                        scheduled_payment_date,
                        actual_payment_date,
                        invoice_number,
                        payment_status,
                        withholding_tax,
                        consumption_tax,
                        payment_amount,
                        invoice_file_path,
                        payment_method,
                        approver,
                        approval_date,
                        remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('契約ID', '').strip() or None,
                    row.get('番組名', '').strip() or None,
                    row.get('取引先名', '').strip() or None,
                    row.get('項目名', '').strip() or None,
                    row.get('業務種別', '').strip() or None,
                    parse_amount(row.get('金額', '')),
                    parse_date(row.get('実施日', '')),
                    row.get('発注番号', '').strip() or None,
                    parse_date(row.get('発注日', '')),
                    row.get('状態', '').strip() or None,
                    parse_date(row.get('請求書受領日', '')),
                    parse_date(row.get('支払予定日', '')),
                    parse_date(row.get('実際支払日', '')),
                    row.get('請求書番号', '').strip() or None,
                    row.get('支払状態', '').strip() or None,
                    parse_amount(row.get('源泉徴収額', '')),
                    parse_amount(row.get('消費税額', '')),
                    parse_amount(row.get('支払金額', '')),
                    row.get('請求書ファイルパス', '').strip() or None,
                    row.get('支払方法', '').strip() or None,
                    row.get('承認者', '').strip() or None,
                    parse_date(row.get('承認日', '')),
                    row.get('備考', '').strip() or None
                ))

                imported_count += 1

                if imported_count % 10 == 0:
                    print(f"  インポート中... {imported_count}件")

            except Exception as e:
                error_count += 1
                print(f"エラー (行 {imported_count + error_count + 1}): {e}")
                print(f"  データ: {row}")

    # コミット
    conn.commit()

    # 結果を表示
    print(f"\n完了:")
    print(f"  インポート成功: {imported_count}件")
    print(f"  エラー: {error_count}件")

    # インポート後のデータを確認
    cursor.execute("SELECT COUNT(*) FROM expense_items")
    total = cursor.fetchone()[0]
    print(f"  データベース内の総レコード数: {total}件")

    conn.close()
    return True

if __name__ == "__main__":
    # CSVファイルのパスを指定
    csv_file = "/Volumes/MyDrive/GitHub/BillingManager2.0/expense_items.csv"
    db_file = "/Volumes/MyDrive/GitHub/BillingManager2.0/database/order_management.db"

    print("=" * 60)
    print("費用項目データインポートツール")
    print("=" * 60)

    import_expense_items(csv_file, db_file)

    print("\n処理が完了しました。")
