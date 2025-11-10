#!/usr/bin/env python3
"""新規作成した契約から費用項目を生成するスクリプト

2025年10月1日開始の契約から、各月の費用項目を自動生成します。
"""

from order_management.database_manager import OrderManagementDB

def main():
    db = OrderManagementDB()

    # 2025年10月1日開始の契約IDを取得
    import sqlite3
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, item_name
        FROM contracts
        WHERE contract_start_date = '2025-10-01'
        ORDER BY id
    """)

    contracts = cursor.fetchall()
    conn.close()

    print(f"対象契約数: {len(contracts)}件")
    print("-" * 60)

    total_generated = 0

    for contract_id, item_name in contracts:
        print(f"契約ID {contract_id}: {item_name}")

        try:
            count = db.generate_expense_items_from_contract(contract_id)
            total_generated += count
            print(f"  → {count}件の費用項目を生成")
        except Exception as e:
            print(f"  → エラー: {e}")

    print("-" * 60)
    print(f"\n合計生成件数: {total_generated}件")
    print(f"予想件数: {len(contracts)} × 7ヶ月 = {len(contracts) * 7}件")

if __name__ == '__main__':
    main()
