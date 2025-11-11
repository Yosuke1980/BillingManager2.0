#!/usr/bin/env python3
"""番組別費用詳細UIのテスト

UIの表示内容が正しいか確認します。
"""

from order_management.database_manager import OrderManagementDB

def main():
    print("番組別費用詳細UIのテストを開始...")
    db = OrderManagementDB()

    try:
        print("\n1. レギュラー番組のテスト...")
        regular_items = db.get_production_expense_summary(production_type_filter="レギュラー", sort_by='monthly_average')

        if regular_items:
            print(f"   レギュラー番組数: {len(regular_items)}件")
            print(f"\n   上位3番組:")
            for i, item in enumerate(regular_items[:3], 1):
                production_name = item[1]
                production_type = item[2]
                total_amount = item[4]
                month_count = item[10]
                monthly_average = item[11]
                print(f"   {i}. {production_name} ({production_type})")
                print(f"      総費用: ¥{int(total_amount):,}")
                print(f"      期間: {month_count}ヶ月")
                print(f"      月額平均: ¥{int(monthly_average):,}/月")
                print(f"      表示形式: ¥{int(monthly_average):,}/月")

        print("\n2. イベントのテスト...")
        event_items = db.get_production_expense_summary(production_type_filter="イベント", sort_by='total_amount')

        if event_items:
            print(f"   イベント数: {len(event_items)}件")
            print(f"\n   上位3イベント:")
            for i, item in enumerate(event_items[:3], 1):
                production_name = item[1]
                production_type = item[2]
                total_amount = item[4]
                month_count = item[10]
                print(f"   {i}. {production_name} ({production_type})")
                print(f"      総費用: ¥{int(total_amount):,}")
                print(f"      期間: {month_count}ヶ月")
                print(f"      表示形式: ({month_count}ヶ月)")

        print("\n3. 色分けテスト...")
        all_items = db.get_production_expense_summary()

        color_map = {
            "レギュラー": "青系 (230, 240, 255)",
            "イベント": "黄系 (255, 250, 230)",
            "特番": "黄系 (255, 250, 230)",
            "コーナー": "青系 (230, 240, 255)",
        }

        print(f"   全番組数: {len(all_items)}件")
        for prod_type, color in color_map.items():
            count = sum(1 for item in all_items if item[2] == prod_type)
            if count > 0:
                print(f"   {prod_type}: {count}件 → 色: {color}")

        print("\n4. 番組詳細の取得テスト...")
        if all_items:
            first_production_id = all_items[0][0]
            first_production_name = all_items[0][1]

            print(f"   テスト対象: {first_production_name} (ID: {first_production_id})")

            details = db.get_production_expense_details(first_production_id)
            print(f"   費用項目数: {len(details)}件")

            if details:
                print(f"   最初の項目:")
                detail = details[0]
                print(f"     取引先: {detail[1]}")
                print(f"     項目名: {detail[2]}")
                print(f"     金額: ¥{int(detail[3]):,}")
                print(f"     実施日: {detail[4]}")
                print(f"     支払状態: {detail[6]}")

        print("\n✅ テスト完了")

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
