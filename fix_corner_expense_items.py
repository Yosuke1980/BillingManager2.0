#!/usr/bin/env python3
"""コーナーの費用項目データを修正するスクリプト

現状:
  production_id = コーナーID
  corner_id = NULL

修正後:
  production_id = 親番組ID
  corner_id = コーナーID
"""

import sqlite3
import sys

def main():
    db_path = 'order_management.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=" * 60)
        print("コーナー費用項目データ修正スクリプト")
        print("=" * 60)

        # 修正対象の確認
        cursor.execute("""
            SELECT
                ei.id,
                ei.production_id,
                ei.corner_id,
                p.name as corner_name,
                p.parent_production_id,
                parent.name as parent_name
            FROM expense_items ei
            JOIN productions p ON ei.production_id = p.id
            LEFT JOIN productions parent ON p.parent_production_id = parent.id
            WHERE p.parent_production_id IS NOT NULL
            ORDER BY p.parent_production_id, p.id
        """)

        items_to_fix = cursor.fetchall()

        if not items_to_fix:
            print("\n修正対象の費用項目が見つかりませんでした。")
            return

        print(f"\n修正対象: {len(items_to_fix)}件の費用項目")
        print("\n【修正内容のプレビュー】")

        # コーナーごとに集計
        corner_summary = {}
        for item in items_to_fix:
            corner_id = item[1]
            corner_name = item[3]
            parent_id = item[4]
            parent_name = item[5]

            key = (corner_id, corner_name, parent_id, parent_name)
            if key not in corner_summary:
                corner_summary[key] = 0
            corner_summary[key] += 1

        for (corner_id, corner_name, parent_id, parent_name), count in corner_summary.items():
            print(f"  {corner_name} (ID:{corner_id}) → 親番組: {parent_name} (ID:{parent_id})")
            print(f"    {count}件の費用項目を修正")

        # 確認
        print("\n上記の修正を実行しますか？ [y/N]: ", end='')
        response = input().strip().lower()

        if response != 'y':
            print("キャンセルしました。")
            return

        print("\n修正を実行中...")

        # 修正前のデータをログ出力
        print("\n【修正前のデータ】")
        for item in items_to_fix[:5]:  # 最初の5件のみ表示
            print(f"  ID:{item[0]} production_id:{item[1]} corner_id:{item[2]}")
        if len(items_to_fix) > 5:
            print(f"  ... 他 {len(items_to_fix) - 5}件")

        # トランザクション開始
        conn.execute("BEGIN TRANSACTION")

        try:
            # UPDATE文を実行
            cursor.execute("""
                UPDATE expense_items
                SET production_id = (
                        SELECT parent_production_id
                        FROM productions
                        WHERE id = expense_items.production_id
                    ),
                    corner_id = production_id
                WHERE production_id IN (
                    SELECT id FROM productions WHERE parent_production_id IS NOT NULL
                )
            """)

            updated_count = cursor.rowcount
            conn.commit()

            print(f"\n✓ 修正完了: {updated_count}件の費用項目を更新しました")

            # 修正後の確認
            cursor.execute("""
                SELECT
                    ei.id,
                    ei.production_id,
                    ei.corner_id,
                    parent.name as parent_name,
                    corner.name as corner_name
                FROM expense_items ei
                LEFT JOIN productions parent ON ei.production_id = parent.id
                LEFT JOIN productions corner ON ei.corner_id = corner.id
                WHERE ei.corner_id IS NOT NULL
                LIMIT 5
            """)

            print("\n【修正後のデータ（サンプル）】")
            for item in cursor.fetchall():
                print(f"  ID:{item[0]} production_id:{item[1]} ({item[3]}) corner_id:{item[2]} ({item[4]})")

        except Exception as e:
            conn.rollback()
            print(f"\nエラーが発生しました: {e}")
            print("変更はロールバックされました。")
            raise

    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    main()
