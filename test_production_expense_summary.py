#!/usr/bin/env python3
"""番組別費用集計のテスト

レギュラー番組と単発イベントの表示が正しく動作するか確認します。
"""

from order_management.database_manager import OrderManagementDB

def main():
    print("番組別費用集計のテストを開始...")
    db = OrderManagementDB()

    try:
        print("\n1. 全件取得テスト...")
        items = db.get_production_expense_summary()
        print(f"   取得件数: {len(items)}件")

        print("\n2. データ構造チェック...")
        if items:
            first_item = items[0]
            print(f"   カラム数: {len(first_item)}（期待値: 12）")
            print(f"\n   カラム内容:")
            print(f"     [0] production_id: {first_item[0]}")
            print(f"     [1] production_name: {first_item[1]}")
            print(f"     [2] production_type: {first_item[2]}")
            print(f"     [3] item_count: {first_item[3]}")
            print(f"     [4] total_amount: {first_item[4]}")
            print(f"     [5] unpaid_count: {first_item[5]}")
            print(f"     [6] unpaid_amount: {first_item[6]}")
            print(f"     [7] paid_count: {first_item[7]}")
            print(f"     [8] paid_amount: {first_item[8]}")
            print(f"     [9] pending_count: {first_item[9]}")
            print(f"     [10] month_count: {first_item[10]}")
            print(f"     [11] monthly_average: {first_item[11]}")

        print("\n3. 番組種別別の集計...")
        type_counts = {}
        for item in items:
            production_type = item[2] or "不明"
            type_counts[production_type] = type_counts.get(production_type, 0) + 1

        for prod_type, count in sorted(type_counts.items()):
            print(f"   {prod_type}: {count}件")

        print("\n4. レギュラー番組のサンプル（上位5件）...")
        regular_items = db.get_production_expense_summary(production_type_filter="レギュラー", sort_by='monthly_average')
        for i, item in enumerate(regular_items[:5], 1):
            production_name = item[1]
            production_type = item[2]
            total_amount = item[4]
            month_count = item[10]
            monthly_average = item[11]
            print(f"   {i}. {production_name} ({production_type})")
            print(f"      総費用: ¥{int(total_amount):,} / {month_count}ヶ月 = ¥{int(monthly_average):,}/月")

        print("\n5. イベントのサンプル（上位5件）...")
        event_items = db.get_production_expense_summary(production_type_filter="イベント", sort_by='total_amount')
        for i, item in enumerate(event_items[:5], 1):
            production_name = item[1]
            production_type = item[2]
            total_amount = item[4]
            month_count = item[10]
            print(f"   {i}. {production_name} ({production_type})")
            print(f"      総費用: ¥{int(total_amount):,} ({month_count}ヶ月)")

        print("\n6. 月額平均でソートテスト...")
        sorted_items = db.get_production_expense_summary(sort_by='monthly_average')[:3]
        print(f"   月額平均トップ3:")
        for i, item in enumerate(sorted_items, 1):
            print(f"   {i}. {item[1]}: ¥{int(item[11]):,}/月")

        print("\n✅ テスト完了")

    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
