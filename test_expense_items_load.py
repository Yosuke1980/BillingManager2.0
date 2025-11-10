#!/usr/bin/env python3
"""費用項目読み込みテスト

費用項目を読み込んで問題がないか確認します。
"""

from order_management.database_manager import OrderManagementDB
from datetime import datetime

def main():
    print("費用項目の読み込みテストを開始...")
    db = OrderManagementDB()

    try:
        print("\n1. 全件取得テスト...")
        items = db.get_expense_items_with_details()
        print(f"   取得件数: {len(items)}件")

        print("\n2. データ構造チェック...")
        if items:
            first_item = items[0]
            print(f"   カラム数: {len(first_item)}")
            print(f"   最初のレコード:")
            print(f"     ID: {first_item[0]}")
            print(f"     番組名: {first_item[2]}")
            print(f"     取引先名: {first_item[4]}")
            print(f"     項目名: {first_item[5]}")
            print(f"     金額: {first_item[6]}")
            print(f"     実施日: {first_item[7]}")
            print(f"     支払予定日: {first_item[8]}")

        print("\n3. 日付フォーマットチェック...")
        error_count = 0
        for item in items:
            expected_payment_date = item[8]
            if expected_payment_date:
                try:
                    datetime.strptime(expected_payment_date, '%Y-%m-%d')
                except Exception as e:
                    error_count += 1
                    print(f"   ❌ ID {item[0]}: 日付フォーマットエラー '{expected_payment_date}' - {e}")
                    if error_count >= 10:
                        print("   （エラーが多いため、10件で打ち切り）")
                        break

        if error_count == 0:
            print("   ✅ 全ての日付が正しい形式です")
        else:
            print(f"   ⚠️  {error_count}件の日付フォーマットエラーがあります")

        print("\n4. NULL値チェック...")
        null_production = sum(1 for item in items if item[1] is None)
        null_partner = sum(1 for item in items if item[3] is None)
        print(f"   production_id がNULL: {null_production}件")
        print(f"   partner_id がNULL: {null_partner}件")

        print("\n✅ テスト完了")

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
