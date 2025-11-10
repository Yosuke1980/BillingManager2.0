#!/usr/bin/env python3
"""
費用項目の契約未登録レコードに対して自動的に契約を作成するスクリプト

要件:
- 出演: 契約書タイプ、3ヶ月ごと自動更新、2025-04-01 ~ 2025-06-30
- 制作: 発注書タイプ、6ヶ月更新、2025-04-01 ~ 2025-09-30
"""
import sqlite3
from datetime import datetime

def create_missing_contracts():
    """契約未登録の費用項目に対して契約を作成"""

    conn = sqlite3.connect('order_management.db')
    cursor = conn.cursor()

    try:
        # 契約未登録の費用項目を取得
        cursor.execute("""
            SELECT
                ei.id,
                ei.production_id,
                ei.partner_id,
                ei.work_type,
                ei.item_name,
                ei.amount,
                p.name as production_name,
                pa.name as partner_name
            FROM expense_items ei
            LEFT JOIN productions p ON ei.production_id = p.id
            LEFT JOIN partners pa ON ei.partner_id = pa.id
            WHERE ei.contract_id IS NULL
            ORDER BY ei.work_type, p.name
        """)

        expense_items = cursor.fetchall()

        print(f"契約未登録の費用項目: {len(expense_items)}件")

        created_contracts = []

        for item in expense_items:
            (expense_id, production_id, partner_id, work_type,
             item_name, amount, production_name, partner_name) = item

            if not production_id or not partner_id:
                print(f"  ⚠️  スキップ (ID: {expense_id}): 番組または取引先が未設定")
                continue

            # 契約タイプと期間を決定
            if work_type == '出演':
                document_type = '契約書'
                start_date = '2025-04-01'
                end_date = '2025-06-30'  # 3ヶ月
                auto_renewal = 1  # 自動延長ON
                renewal_period = 3  # 3ヶ月ごと
                order_category = 'レギュラー出演契約書'
                contract_type = 'regular_fixed'
            else:  # 制作
                document_type = '発注書'
                start_date = '2025-04-01'
                end_date = '2025-09-30'  # 6ヶ月
                auto_renewal = 0  # 自動延長OFF
                renewal_period = 6
                order_category = 'レギュラー制作発注書'
                contract_type = 'regular_fixed'

            # 既存の契約を確認（同じ番組・取引先・業務種別の組み合わせ）
            cursor.execute("""
                SELECT id FROM contracts
                WHERE production_id = ?
                AND partner_id = ?
                AND work_type = ?
                AND document_type = ?
                LIMIT 1
            """, (production_id, partner_id, work_type, document_type))

            existing_contract = cursor.fetchone()

            if existing_contract:
                contract_id = existing_contract[0]
                print(f"  ✓ 既存契約を使用 (ID: {contract_id}): {production_name} - {partner_name} ({work_type})")
            else:
                # 新規契約を作成
                cursor.execute("""
                    INSERT INTO contracts (
                        production_id, partner_id, item_name, work_type,
                        contract_type, unit_price, contract_start_date, contract_end_date,
                        document_type, auto_renewal_enabled, renewal_period_months,
                        order_category, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (
                    production_id, partner_id, item_name, work_type,
                    contract_type, amount, start_date, end_date,
                    document_type, auto_renewal, renewal_period, order_category
                ))

                contract_id = cursor.lastrowid
                created_contracts.append({
                    'id': contract_id,
                    'production': production_name,
                    'partner': partner_name,
                    'work_type': work_type,
                    'document_type': document_type
                })
                print(f"  ➕ 新規契約作成 (ID: {contract_id}): {production_name} - {partner_name} ({work_type}/{document_type})")

            # 費用項目に契約IDを設定
            cursor.execute("""
                UPDATE expense_items
                SET contract_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (contract_id, expense_id))

        # コミット
        conn.commit()

        print(f"\n{'='*60}")
        print(f"✅ 完了: {len(created_contracts)}件の新規契約を作成しました")
        print(f"{'='*60}")

        # サマリー表示
        if created_contracts:
            print("\n作成された契約:")
            cast_count = sum(1 for c in created_contracts if c['work_type'] == '出演')
            production_count = sum(1 for c in created_contracts if c['work_type'] == '制作')
            print(f"  - 出演（契約書）: {cast_count}件")
            print(f"  - 制作（発注書）: {production_count}件")

        # 契約未登録の残り件数を確認
        cursor.execute("""
            SELECT COUNT(*) FROM expense_items WHERE contract_id IS NULL
        """)
        remaining = cursor.fetchone()[0]
        print(f"\n契約未登録の残り: {remaining}件")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    create_missing_contracts()
