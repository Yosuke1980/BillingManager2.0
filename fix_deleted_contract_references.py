#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
削除された契約を参照している費用項目の修正スクリプト

このスクリプトは以下の処理を行います：
1. 削除済み契約を参照している費用項目を検出
2. マッチする契約（同じ番組・取引先・業務種別）がある場合、最新の契約に紐付け
3. マッチする契約がない場合、contract_idをNULLにクリア
4. 処理結果をレポート
"""

import sqlite3
import sys
from datetime import datetime

DB_PATH = 'order_management.db'

def fix_deleted_contract_references():
    """削除済み契約参照の修正"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # バックアップのタイムスタンプ
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n契約紐付け修正スクリプト開始: {timestamp}")
        print("=" * 80)

        # 1. 削除済み契約を参照している費用項目を取得
        cursor.execute("""
            SELECT ei.id, ei.item_name, ei.production_id, ei.partner_id, ei.work_type,
                   ei.contract_id as old_contract_id,
                   prod.name as production_name, part.name as partner_name
            FROM expense_items ei
            LEFT JOIN contracts old_c ON ei.contract_id = old_c.id
            LEFT JOIN productions prod ON ei.production_id = prod.id
            LEFT JOIN partners part ON ei.partner_id = part.id
            WHERE ei.contract_id IS NOT NULL
              AND old_c.id IS NULL
              AND (ei.archived = 0 OR ei.archived IS NULL)
            ORDER BY ei.id
        """)

        items_with_deleted_contracts = cursor.fetchall()
        total_items = len(items_with_deleted_contracts)

        print(f"\n削除済み契約を参照している費用項目: {total_items}件\n")

        if total_items == 0:
            print("修正が必要な項目はありません。")
            return

        # 統計用カウンタ
        updated_count = 0
        cleared_count = 0
        skipped_count = 0

        # レポート用リスト
        updates = []
        clears = []

        for item in items_with_deleted_contracts:
            expense_id, item_name, production_id, partner_id, work_type, old_contract_id, production_name, partner_name = item

            # マッチする契約を検索（同じ番組・取引先・業務種別）
            cursor.execute("""
                SELECT id, contract_start_date
                FROM contracts
                WHERE production_id = ?
                  AND partner_id = ?
                  AND work_type = ?
                ORDER BY id DESC
                LIMIT 1
            """, (production_id, partner_id, work_type))

            matching_contract = cursor.fetchone()

            if matching_contract:
                new_contract_id = matching_contract[0]

                # 契約IDを更新
                cursor.execute("""
                    UPDATE expense_items
                    SET contract_id = ?
                    WHERE id = ?
                """, (new_contract_id, expense_id))

                updated_count += 1
                updates.append({
                    'expense_id': expense_id,
                    'item_name': item_name,
                    'production': production_name,
                    'partner': partner_name,
                    'old_contract_id': old_contract_id,
                    'new_contract_id': new_contract_id
                })

            else:
                # マッチする契約がない場合、contract_idをNULLにクリア
                cursor.execute("""
                    UPDATE expense_items
                    SET contract_id = NULL
                    WHERE id = ?
                """, (expense_id,))

                cleared_count += 1
                clears.append({
                    'expense_id': expense_id,
                    'item_name': item_name,
                    'production': production_name,
                    'partner': partner_name,
                    'old_contract_id': old_contract_id
                })

        # コミット
        conn.commit()

        # レポート表示
        print("\n" + "=" * 80)
        print("処理結果サマリー")
        print("=" * 80)
        print(f"総処理件数: {total_items}件")
        print(f"  - 契約に紐付けた: {updated_count}件")
        print(f"  - contract_idをクリア: {cleared_count}件")
        print(f"  - スキップ: {skipped_count}件")

        # 詳細レポート：更新した項目
        if updates:
            print("\n" + "-" * 80)
            print(f"契約に紐付けた項目（{updated_count}件）:")
            print("-" * 80)
            for i, update in enumerate(updates[:10], 1):  # 最初の10件のみ表示
                print(f"{i}. 費用項目ID: {update['expense_id']}")
                print(f"   項目名: {update['item_name']}")
                print(f"   番組: {update['production']}")
                print(f"   取引先: {update['partner']}")
                print(f"   旧契約ID: {update['old_contract_id']} → 新契約ID: {update['new_contract_id']}")
                print()

            if len(updates) > 10:
                print(f"   ... 他 {len(updates) - 10}件")

        # 詳細レポート：クリアした項目
        if clears:
            print("\n" + "-" * 80)
            print(f"contract_idをクリアした項目（{cleared_count}件）:")
            print("-" * 80)
            for i, clear in enumerate(clears[:10], 1):  # 最初の10件のみ表示
                print(f"{i}. 費用項目ID: {clear['expense_id']}")
                print(f"   項目名: {clear['item_name']}")
                print(f"   番組: {clear['production']}")
                print(f"   取引先: {clear['partner']}")
                print(f"   旧契約ID: {clear['old_contract_id']} → NULL")
                print()

            if len(clears) > 10:
                print(f"   ... 他 {len(clears) - 10}件")

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
    fix_deleted_contract_references()
