#!/usr/bin/env python3
"""レギュラー番組の月別表示テスト

レギュラー番組が月別にグループ化されて表示されるか確認します。
"""

from order_management.database_manager import OrderManagementDB

def main():
    print("レギュラー番組の月別表示テストを開始...")
    db = OrderManagementDB()

    try:
        print("\n1. レギュラー番組を取得...")
        regular_items = db.get_production_expense_summary(production_type_filter="レギュラー")

        if not regular_items:
            print("   ❌ レギュラー番組が見つかりませんでした")
            return

        # 最初のレギュラー番組をテスト対象にする
        test_production = regular_items[0]
        production_id = test_production[0]
        production_name = test_production[1]
        production_type = test_production[2]

        print(f"   テスト対象: {production_name} (ID: {production_id}, 種別: {production_type})")

        print("\n2. 月別集計を取得...")
        monthly_summary = db.get_production_expense_monthly_summary(production_id)

        if not monthly_summary:
            print("   ❌ 月別集計が見つかりませんでした")
            return

        print(f"   月数: {len(monthly_summary)}ヶ月")
        print(f"\n   月別サマリー:")

        for i, month_data in enumerate(monthly_summary[:5], 1):  # 最初の5ヶ月のみ表示
            month = month_data[0]
            item_count = month_data[1]
            total_amount = month_data[2] or 0
            unpaid_count = month_data[3]
            paid_count = month_data[4]

            print(f"   {i}. 📅 {month} ({item_count}件 / ¥{int(total_amount):,})")
            print(f"      未払い: {unpaid_count}件 / 支払済: {paid_count}件")

        print("\n3. 特定月の詳細を取得...")
        test_month = monthly_summary[0][0]
        month_details = db.get_production_expense_details_by_month(production_id, test_month)

        print(f"   対象月: {test_month}")
        print(f"   費用項目数: {len(month_details)}件")

        if month_details:
            print(f"\n   最初の3項目:")
            for i, detail in enumerate(month_details[:3], 1):
                partner_name = detail[1]
                item_name = detail[2]
                amount = detail[3]
                expected_payment_date = detail[5]
                payment_status = detail[6]

                print(f"   {i}. {partner_name} - {item_name}")
                print(f"      金額: ¥{int(amount):,} / 支払予定: {expected_payment_date} / 状態: {payment_status}")

        print("\n4. イベントとの比較...")
        event_items = db.get_production_expense_summary(production_type_filter="イベント")

        if event_items:
            test_event = event_items[0]
            event_id = test_event[0]
            event_name = test_event[1]
            event_type = test_event[2]

            print(f"   イベント例: {event_name} (種別: {event_type})")

            event_details = db.get_production_expense_details(event_id)
            print(f"   全費用項目数: {len(event_details)}件（月別グループ化なし）")

        print("\n✅ テスト完了")
        print("\n📋 実装確認:")
        print("   - レギュラー番組: 月別にグループ化して表示")
        print("   - イベント: 全項目を一括表示")

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
