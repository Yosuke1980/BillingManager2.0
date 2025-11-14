#!/usr/bin/env python3
"""
自動照合機能のテストスクリプト

app.pyに追加した_auto_reconcile_payments()メソッドの動作を確認する
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from order_management.database_manager import OrderManagementDB

def test_auto_reconcile():
    """自動照合機能のテスト"""
    print("=" * 60)
    print("自動照合機能のテスト")
    print("=" * 60)

    # データベース接続
    db = OrderManagementDB('order_management.db')

    # 照合前の未照合件数を確認
    print("\n【照合前の状態】")
    import sqlite3

    order_conn = sqlite3.connect('order_management.db')
    order_cursor = order_conn.cursor()

    order_cursor.execute("""
        SELECT COUNT(*) FROM expense_items
        WHERE payment_matched_id IS NULL
          AND payment_status != '支払済'
          AND (archived = 0 OR archived IS NULL)
    """)
    before_unmatched = order_cursor.fetchone()[0]
    print(f"未照合費用項目: {before_unmatched}件")

    order_cursor.execute("""
        SELECT COUNT(*) FROM expense_items
        WHERE payment_status = '支払済'
    """)
    before_paid = order_cursor.fetchone()[0]
    print(f"支払済費用項目: {before_paid}件")

    order_conn.close()

    # 自動照合を実行
    print("\n【自動照合を実行中...】")
    result = db.reconcile_payments_with_expenses('billing.db')

    print(f"\n照合成功: {result['matched']}件")
    print(f"未照合費用項目: {result['unmatched_expenses']}件")
    print(f"未照合支払い: {result['unmatched_payments']}件")

    # 照合後の状態を確認
    print("\n【照合後の状態】")

    order_conn = sqlite3.connect('order_management.db')
    order_cursor = order_conn.cursor()

    order_cursor.execute("""
        SELECT COUNT(*) FROM expense_items
        WHERE payment_status = '支払済'
    """)
    after_paid = order_cursor.fetchone()[0]
    print(f"支払済費用項目: {after_paid}件")

    increase = after_paid - before_paid
    print(f"\n支払済件数の増加: {increase}件")

    if increase > 0:
        print("\n✓ 自動照合が正常に動作しています")

        # 最近照合された項目を表示
        order_cursor.execute("""
            SELECT id, item_name, amount, payment_matched_id, actual_payment_date
            FROM expense_items
            WHERE payment_status = '支払済'
              AND payment_matched_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 5
        """)
        recent_matched = order_cursor.fetchall()

        if recent_matched:
            print("\n最近照合された費用項目（最新5件）:")
            for item in recent_matched:
                item_id, item_name, amount, matched_id, payment_date = item
                print(f"  ID {item_id}: {item_name} / ¥{int(amount):,} / 支払ID:{matched_id} / {payment_date}")
    elif increase == 0:
        print("\n⚠ 新規照合はありませんでした（すでに照合済みの可能性）")
    else:
        print("\n✗ エラー: 支払済件数が減少しています")

    order_conn.close()

    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_auto_reconcile()
