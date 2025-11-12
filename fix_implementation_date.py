#!/usr/bin/env python3
"""
費用項目のimplementation_dateがNULLの場合、番組のstart_dateで補完するスクリプト
"""
import sqlite3

def fix_implementation_dates():
    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # implementation_dateがNULLで、番組にstart_dateがある費用項目を検索
        cursor.execute("""
            SELECT ei.id, ei.production_id, p.name, p.start_date
            FROM expense_items ei
            JOIN productions p ON ei.production_id = p.id
            WHERE ei.implementation_date IS NULL
              AND p.start_date IS NOT NULL
        """)

        items_to_fix = cursor.fetchall()

        if not items_to_fix:
            print("修正が必要な費用項目はありませんでした。")
            return

        print(f"\n修正対象: {len(items_to_fix)}件の費用項目")
        print("\n対象の費用項目:")
        for item_id, prod_id, prod_name, start_date in items_to_fix:
            print(f"  - 費用項目ID: {item_id}, 番組: {prod_name} (ID: {prod_id}), 実施日に設定: {start_date}")

        # 確認
        response = input("\n上記の費用項目のimplementation_dateを番組のstart_dateで更新しますか？ (y/n): ")
        if response.lower() != 'y':
            print("キャンセルしました。")
            return

        # 更新実行
        cursor.execute("""
            UPDATE expense_items
            SET implementation_date = (
                SELECT start_date
                FROM productions
                WHERE id = expense_items.production_id
            )
            WHERE implementation_date IS NULL
              AND production_id IN (
                  SELECT id FROM productions WHERE start_date IS NOT NULL
              )
        """)

        updated_count = cursor.rowcount
        conn.commit()

        print(f"\n✓ {updated_count}件の費用項目を更新しました。")

        # 更新後の確認
        cursor.execute("""
            SELECT COUNT(*) FROM expense_items
            WHERE implementation_date IS NULL
        """)
        remaining = cursor.fetchone()[0]

        if remaining > 0:
            print(f"\n注意: {remaining}件の費用項目はまだimplementation_dateがNULLです。")
            print("（番組にstart_dateが設定されていない可能性があります）")

    except Exception as e:
        conn.rollback()
        print(f"エラーが発生しました: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_implementation_dates()
