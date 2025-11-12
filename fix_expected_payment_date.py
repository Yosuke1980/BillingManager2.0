#!/usr/bin/env python3
"""
費用項目のexpected_payment_dateがNULLの場合、implementation_dateとpayment_timingから計算して補完するスクリプト
"""
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

def calculate_payment_date(impl_date_str, payment_timing):
    """
    実施日と支払タイミングから支払予定日を計算

    Args:
        impl_date_str: 実施日 (YYYY-MM-DD形式 or YYYY/MM/DD形式)
        payment_timing: 支払タイミング ('当月末払い' or '翌月末払い')

    Returns:
        支払予定日 (YYYY-MM-DD形式)
    """
    if not impl_date_str:
        return None

    # 日付フォーマットを正規化
    impl_date_str = impl_date_str.replace('/', '-')
    impl_date = datetime.strptime(impl_date_str, '%Y-%m-%d')

    if payment_timing == '当月末払い':
        # 当月末（実施月の末日）
        payment_date = impl_date.replace(day=1) + relativedelta(months=1, days=-1)
    else:  # 翌月末払い（デフォルト）
        # 翌月末（実施月の翌月末）
        payment_date = impl_date.replace(day=1) + relativedelta(months=2, days=-1)

    return payment_date.strftime('%Y-%m-%d')

def fix_expected_payment_dates():
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # expected_payment_dateがNULLで、implementation_dateと契約がある費用項目を検索
        cursor.execute("""
            SELECT ei.id, ei.implementation_date, c.payment_timing, p.name
            FROM expense_items ei
            LEFT JOIN contracts c ON ei.contract_id = c.id
            LEFT JOIN productions p ON ei.production_id = p.id
            WHERE ei.expected_payment_date IS NULL
              AND ei.implementation_date IS NOT NULL
              AND ei.contract_id IS NOT NULL
        """)

        items_to_fix = cursor.fetchall()

        if not items_to_fix:
            print("修正が必要な費用項目はありませんでした。")
            return

        print(f"\n修正対象: {len(items_to_fix)}件の費用項目")
        print("\n対象の費用項目:")

        updates = []
        for item_id, impl_date, payment_timing, prod_name in items_to_fix:
            expected_date = calculate_payment_date(impl_date, payment_timing or '翌月末払い')
            updates.append((expected_date, item_id))
            print(f"  - 費用項目ID: {item_id}, 番組: {prod_name}, 実施日: {impl_date}, 支払タイミング: {payment_timing or '翌月末払い'}, 支払予定日: {expected_date}")

        # 確認
        response = input("\n上記の費用項目のexpected_payment_dateを更新しますか？ (y/n): ")
        if response.lower() != 'y':
            print("キャンセルしました。")
            return

        # 更新実行
        for expected_date, item_id in updates:
            cursor.execute("""
                UPDATE expense_items
                SET expected_payment_date = ?
                WHERE id = ?
            """, (expected_date, item_id))

        updated_count = cursor.rowcount
        conn.commit()

        print(f"\n✓ {len(updates)}件の費用項目を更新しました。")

        # 更新後の確認
        cursor.execute("""
            SELECT COUNT(*) FROM expense_items
            WHERE expected_payment_date IS NULL
              AND implementation_date IS NOT NULL
        """)
        remaining = cursor.fetchone()[0]

        if remaining > 0:
            print(f"\n注意: {remaining}件の費用項目はまだexpected_payment_dateがNULLです。")
            print("（契約が紐づいていない可能性があります）")

    except Exception as e:
        conn.rollback()
        print(f"エラーが発生しました: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_expected_payment_dates()
