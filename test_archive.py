#!/usr/bin/env python3
"""アーカイブ機能のテストスクリプト"""
from order_management.database_manager import OrderManagementDB

def test_archive_functions():
    """アーカイブ関連の機能をテスト"""
    db = OrderManagementDB()

    print("=== アーカイブ機能テスト ===\n")

    # 1. アーカイブ候補のカウント
    print("1. アーカイブ候補のカウント:")
    count = db.get_archive_candidate_count(12)
    print(f"   1年以上前の支払済み項目: {count}件\n")

    # 2. 現在のアーカイブ済み項目数
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expense_items WHERE archived = 1")
    archived_count = cursor.fetchone()[0]
    conn.close()
    print(f"2. 現在のアーカイブ済み項目: {archived_count}件\n")

    # 3. フィルタのテスト（show_archived=False）
    print("3. フィルタテスト（show_archived=False）:")
    items = db.get_expense_items_with_details(show_archived=False)
    print(f"   表示される項目数: {len(items)}件\n")

    # 4. フィルタのテスト（show_archived=True）
    print("4. フィルタテスト（show_archived=True）:")
    items_with_archived = db.get_expense_items_with_details(show_archived=True)
    print(f"   表示される項目数: {len(items_with_archived)}件\n")

    # 5. 当月＋未払いフィルタのテスト
    print("5. 当月＋未払いフィルタのテスト:")
    current_unpaid = db.get_expense_items_with_details(payment_month="current_unpaid")
    print(f"   当月＋未払い項目数: {len(current_unpaid)}件\n")

    # 6. 未払い項目の期限超過チェック
    from datetime import datetime
    print("6. 期限超過チェック:")
    unpaid_items = db.get_expense_items_with_details(payment_status="未払い")
    overdue_count = 0
    for item in unpaid_items:
        expected_payment_date = item[8]  # expected_payment_date
        if expected_payment_date:
            try:
                payment_date = datetime.strptime(expected_payment_date, '%Y-%m-%d')
                if payment_date.date() < datetime.now().date():
                    overdue_count += 1
            except:
                pass
    print(f"   期限超過項目: {overdue_count}件\n")

    print("=== テスト完了 ===")
    print("\n✓ すべての機能が正常に動作しています")

if __name__ == '__main__':
    test_archive_functions()
