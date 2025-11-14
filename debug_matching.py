#!/usr/bin/env python3
"""
ID 2854の照合デバッグスクリプト
"""

import sqlite3
from datetime import datetime

# order_management.dbから費用項目を取得
order_conn = sqlite3.connect('order_management.db')
order_cursor = order_conn.cursor()

order_cursor.execute("""
    SELECT ei.id, ei.item_name, p.name as partner_name, p.code as partner_code,
           ei.amount, ei.expected_payment_date, ei.payment_status
    FROM expense_items ei
    LEFT JOIN partners p ON ei.partner_id = p.id
    WHERE ei.id = 2854
""")
expense = order_cursor.fetchone()

print("=" * 60)
print("費用項目情報:")
print("=" * 60)
print(f"ID: {expense[0]}")
print(f"項目名: {expense[1]}")
print(f"取引先名: {expense[2]}")
print(f"取引先コード: {expense[3]}")
print(f"金額: ¥{int(expense[4]):,}")
print(f"支払予定日: {expense[5]}")
print(f"支払状態: {expense[6]}")

# billing.dbから候補を取得
billing_conn = sqlite3.connect('billing.db')
billing_cursor = billing_conn.cursor()

billing_cursor.execute("""
    SELECT id, payee, payee_code, amount, payment_date, status
    FROM payments
    WHERE payee_code = '092011' AND amount = 50000.0
    ORDER BY id DESC
""")
payments = billing_cursor.fetchall()

print("\n" + "=" * 60)
print("候補となる支払いレコード:")
print("=" * 60)

for payment in payments:
    payment_id, payee, payee_code, payment_amount, payment_date, payment_status = payment

    print(f"\n--- Payment ID: {payment_id} ---")
    print(f"支払先: {payee}")
    print(f"支払先コード: {payee_code}")
    print(f"金額: ¥{int(payment_amount):,}")
    print(f"支払日: {payment_date}")
    print(f"ステータス: {payment_status}")

    # 照合条件チェック
    print("\n[照合条件チェック]")

    # 1. 取引先チェック
    name_match = (payee and expense[2] and payee.strip() == expense[2].strip())
    code_match = (payee_code and expense[3] and payee_code.strip() == expense[3].strip())
    print(f"1. 取引先名一致: {name_match} ('{payee}' vs '{expense[2]}')")
    print(f"   取引先コード一致: {code_match} ('{payee_code}' vs '{expense[3]}')")
    print(f"   → {'✓ PASS' if (name_match or code_match) else '✗ FAIL'}")

    if not (name_match or code_match):
        continue

    # 2. 金額チェック
    if payment_amount and expense[4]:
        amount_diff = abs(payment_amount - expense[4]) / expense[4]
        print(f"2. 金額差異: {amount_diff:.2%} (閾値: 5%)")
        print(f"   → {'✓ PASS' if amount_diff <= 0.05 else '✗ FAIL'}")

        if amount_diff > 0.05:
            continue
    else:
        print(f"2. 金額: ✗ FAIL (どちらかがNone)")
        continue

    # 3. 日付チェック
    if payment_date and expense[5]:
        print(f"3. 日付比較:")
        print(f"   支払日: {payment_date}")
        print(f"   支払予定日: {expense[5]}")

        # 複数の日付形式を試す
        date_formats = ['%Y-%m-%d', '%Y/%m/%d']
        pay_date = None
        exp_date = None

        for fmt in date_formats:
            try:
                pay_date = datetime.strptime(payment_date, fmt)
                print(f"   支払日パース成功: {fmt}")
                break
            except:
                pass

        for fmt in date_formats:
            try:
                exp_date = datetime.strptime(expense[5], fmt)
                print(f"   支払予定日パース成功: {fmt}")
                break
            except:
                pass

        if pay_date and exp_date:
            date_diff = abs((pay_date - exp_date).days)
            print(f"   日付差異: {date_diff}日 (閾値: 7日)")
            print(f"   → {'✓ PASS' if date_diff <= 7 else '✗ FAIL'}")

            if date_diff <= 7:
                print("\n✓✓✓ この支払いレコードは照合条件を満たしています ✓✓✓")
        else:
            print(f"   → ✗ FAIL (日付のパースに失敗)")
    else:
        print(f"3. 日付: ✗ FAIL (どちらかがNone)")

order_conn.close()
billing_conn.close()

print("\n" + "=" * 60)
