#!/usr/bin/env python3
"""
費用項目ID 2952の支払い状態を修正するスクリプト
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from order_management.database_manager import OrderManagementDB

def main():
    print("=" * 60)
    print("費用項目ID 2952の支払い状態修正スクリプト")
    print("=" * 60)

    # データベース接続
    db = OrderManagementDB('order_management.db')

    # 修正前の状態を確認
    print("\n【修正前の状態】")
    import sqlite3
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, item_name, amount, expected_payment_date,
               payment_status, payment_matched_id, actual_payment_date
        FROM expense_items
        WHERE id = 2952
    """)
    before = cursor.fetchone()
    if before:
        print(f"ID: {before[0]}")
        print(f"費用項目: {before[1]}")
        print(f"金額: ¥{int(before[2]):,}")
        print(f"支払予定日: {before[3]}")
        print(f"支払状態: {before[4]}")
        print(f"照合ID: {before[5]}")
        print(f"実際の支払日: {before[6]}")

    conn.close()

    # 自動照合を実行
    print("\n【自動照合を実行中...】")
    result = db.reconcile_payments_with_expenses('billing.db')

    print(f"\n照合成功: {result['matched']}件")
    print(f"未照合費用項目: {result['unmatched_expenses']}件")
    print(f"未照合支払い: {result['unmatched_payments']}件")

    # 修正後の状態を確認
    print("\n【修正後の状態】")
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, item_name, amount, expected_payment_date,
               payment_status, payment_matched_id, actual_payment_date
        FROM expense_items
        WHERE id = 2952
    """)
    after = cursor.fetchone()
    if after:
        print(f"ID: {after[0]}")
        print(f"費用項目: {after[1]}")
        print(f"金額: ¥{int(after[2]):,}")
        print(f"支払予定日: {after[3]}")
        print(f"支払状態: {after[4]}")
        print(f"照合ID: {after[5]}")
        print(f"実際の支払日: {after[6]}")

        # 変更があったか確認
        if before != after:
            print("\n✓ 状態が更新されました")
            if after[4] == '支払済':
                print("✓ 支払い済みステータスに更新されました")
        else:
            print("\n⚠ 状態に変更がありませんでした")

    conn.close()

    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
