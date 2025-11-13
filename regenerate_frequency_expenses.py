#!/usr/bin/env python3
"""回数ベース契約の費用項目を再生成するスクリプト

既存の回数ベース契約について、費用項目を削除して最新のロジックで再生成します。
"""

import sys
sys.path.append('/Volumes/MyDrive/GitHub/BillingManager2.0')

from order_management.database_manager import OrderManagementDB

def main():
    db = OrderManagementDB()

    # 回数ベース契約を取得
    conn = db._get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.item_name, p.name as production_name, p.broadcast_days
        FROM contracts c
        LEFT JOIN productions p ON c.production_id = p.id
        WHERE c.payment_type = '回数ベース'
        ORDER BY c.id
    """)

    contracts = cursor.fetchall()
    conn.close()

    if not contracts:
        print("回数ベース契約が見つかりませんでした。")
        return

    print(f"\n回数ベース契約が {len(contracts)} 件見つかりました：\n")

    for contract in contracts:
        contract_id, item_name, production_name, broadcast_days = contract
        broadcast_info = f"放送曜日: {broadcast_days}" if broadcast_days else "⚠️ 放送曜日未設定"
        print(f"  契約ID {contract_id}: {item_name} ({production_name}) - {broadcast_info}")

    print("\n" + "="*70)
    print("⚠️  警告: この操作は既存の費用項目をすべて削除して再生成します。")
    print("="*70)

    response = input("\n費用項目を再生成しますか？ (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("キャンセルしました。")
        return

    print("\n費用項目を再生成中...\n")

    total_deleted = 0
    total_generated = 0
    errors = []

    for contract in contracts:
        contract_id, item_name, production_name, broadcast_days = contract

        try:
            # 既存の費用項目を削除
            deleted_count = db.delete_expense_items_by_contract(contract_id)
            total_deleted += deleted_count

            # 費用項目を再生成
            generated_count = db.generate_expense_items_from_contract(contract_id)
            total_generated += generated_count

            print(f"✓ 契約ID {contract_id} ({item_name}): {deleted_count}件削除, {generated_count}件生成")

        except Exception as e:
            error_msg = f"契約ID {contract_id} ({item_name}): {str(e)}"
            errors.append(error_msg)
            print(f"✗ {error_msg}")

    print(f"\n" + "="*70)
    print(f"処理完了")
    print(f"="*70)
    print(f"削除: {total_deleted}件")
    print(f"生成: {total_generated}件")

    if errors:
        print(f"\nエラー ({len(errors)}件):")
        for error in errors:
            print(f"  - {error}")
        print("\n⚠️  放送曜日が未設定の契約はエラーになります。")
        print("    番組・イベント管理で放送曜日を設定してから再度実行してください。")
    else:
        print("\n✓ すべての費用項目が正常に再生成されました。")
        print("\n次のステップ：")
        print("  1. アプリケーションを再起動してください")
        print("  2. 費用項目の金額と notes フィールドを確認してください")
        print("     （例: 実施回数: 4回 × ¥10,000 = ¥40,000）")

if __name__ == '__main__':
    main()
