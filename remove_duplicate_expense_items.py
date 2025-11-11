#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重複費用項目の削除スクリプト

このスクリプトは以下の処理を行います：
1. 完全に重複している費用項目を検出
   （同じ契約ID、番組、取引先、業務種別、金額、実施日、支払予定日）
2. 重複グループごとに、IDが最小のものを残し、それ以外を削除
3. 処理結果をレポート
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'order_management.db'

def remove_duplicate_expense_items():
    """重複費用項目の削除"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n重複費用項目削除スクリプト開始: {timestamp}")
        print("=" * 80)

        # 1. 重複している費用項目を検出
        cursor.execute("""
            SELECT contract_id, production_id, partner_id, work_type,
                   amount, implementation_date, expected_payment_date,
                   COUNT(*) as count,
                   GROUP_CONCAT(id) as ids,
                   GROUP_CONCAT(item_name) as item_names
            FROM expense_items
            WHERE contract_id IS NOT NULL
              AND (archived = 0 OR archived IS NULL)
            GROUP BY contract_id, production_id, partner_id, work_type,
                     amount, implementation_date, expected_payment_date
            HAVING COUNT(*) > 1
            ORDER BY contract_id, implementation_date
        """)

        duplicate_groups = cursor.fetchall()
        total_groups = len(duplicate_groups)

        print(f"\n重複グループ数: {total_groups}組")

        if total_groups == 0:
            print("重複している費用項目はありません。")
            return

        # 統計用カウンタ
        total_deleted = 0
        deleted_items = []

        print("\n" + "-" * 80)
        print("重複検出詳細:")
        print("-" * 80)

        for group in duplicate_groups:
            contract_id, production_id, partner_id, work_type, amount, impl_date, payment_date, count, ids_str, item_names_str = group

            # IDリストを解析
            ids = [int(id_str) for id_str in ids_str.split(',')]
            item_names = item_names_str.split(',')

            # 最小IDを残し、それ以外を削除
            keep_id = min(ids)
            delete_ids = [id for id in ids if id != keep_id]

            # 番組名と取引先名を取得
            cursor.execute("""
                SELECT prod.name, part.name
                FROM expense_items ei
                LEFT JOIN productions prod ON ei.production_id = prod.id
                LEFT JOIN partners part ON ei.partner_id = part.id
                WHERE ei.id = ?
            """, (keep_id,))

            prod_name, partner_name = cursor.fetchone()

            print(f"\nグループ {total_deleted + 1}:")
            print(f"  契約ID: {contract_id}")
            print(f"  番組: {prod_name or '(なし)'}")
            print(f"  取引先: {partner_name or '(なし)'}")
            print(f"  業務種別: {work_type}")
            print(f"  金額: ¥{int(amount):,}")
            print(f"  実施日: {impl_date}")
            print(f"  支払予定日: {payment_date}")
            print(f"  重複数: {count}件")
            print(f"  残すID: {keep_id} ({item_names[ids.index(keep_id)]})")
            print(f"  削除ID: {', '.join(map(str, delete_ids))}")

            # 削除実行
            for delete_id in delete_ids:
                cursor.execute("""
                    DELETE FROM expense_items WHERE id = ?
                """, (delete_id,))

                deleted_items.append({
                    'id': delete_id,
                    'item_name': item_names[ids.index(delete_id)],
                    'contract_id': contract_id,
                    'production': prod_name,
                    'partner': partner_name,
                    'amount': amount,
                    'kept_id': keep_id
                })

                total_deleted += 1

        # コミット
        conn.commit()

        # レポート表示
        print("\n" + "=" * 80)
        print("処理結果サマリー")
        print("=" * 80)
        print(f"重複グループ数: {total_groups}組")
        print(f"削除した費用項目: {total_deleted}件")
        print(f"残した費用項目: {total_groups}件")

        # 削除された項目の詳細（最初の10件）
        if deleted_items:
            print("\n" + "-" * 80)
            print(f"削除された費用項目（最初の10件）:")
            print("-" * 80)
            for i, item in enumerate(deleted_items[:10], 1):
                print(f"{i}. ID: {item['id']} → 残したID: {item['kept_id']}")
                print(f"   項目名: {item['item_name']}")
                print(f"   番組: {item['production']}")
                print(f"   取引先: {item['partner']}")
                print(f"   金額: ¥{int(item['amount']):,}")
                print()

            if len(deleted_items) > 10:
                print(f"   ... 他 {len(deleted_items) - 10}件")

        print("\n" + "=" * 80)
        print("処理が完了しました。")
        print("=" * 80)

    except Exception as e:
        conn.rollback()
        print(f"\nエラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        conn.close()

if __name__ == '__main__':
    remove_duplicate_expense_items()
