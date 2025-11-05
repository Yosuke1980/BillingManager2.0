"""
project_id修正のテストスクリプト

発注書の保存と読み込みをテストします
"""
from order_management.database_manager import OrderManagementDB
from datetime import datetime

def test_save_and_load():
    """保存と読み込みのテスト"""
    db = OrderManagementDB()

    print("=" * 60)
    print("発注書のproject_id保存・読み込みテスト")
    print("=" * 60)

    # テストデータ作成
    test_contract = {
        'production_id': 1,  # 既存の番組IDを想定
        'project_id': None,  # 案件なし（通常放送）
        'item_name': 'テスト発注項目',
        'partner_id': 1,  # 既存の取引先IDを想定
        'contract_start_date': '2025-01-01',
        'contract_end_date': '2025-06-30',
        'contract_period_type': '半年',
        'order_type': '発注書',
        'order_status': '未完了',
        'payment_type': '月額固定',
        'unit_price': 50000,
        'payment_timing': '翌月末払い',
        'work_type': '制作',
        'order_category': 'レギュラー',
        'notes': 'project_id修正テスト'
    }

    try:
        # 1. 新規保存テスト（project_id=None）
        print("\n1. 新規保存テスト（project_id=None）...")
        contract_id = db.save_order_contract(test_contract)
        print(f"✓ 保存成功: contract_id={contract_id}")

        # 2. 読み込みテスト
        print("\n2. 読み込みテスト...")
        loaded_contract = db.get_order_contract_by_id(contract_id)
        if loaded_contract:
            print(f"✓ 読み込み成功")
            print(f"  - contract[0] (id): {loaded_contract[0]}")
            print(f"  - contract[1] (production_id): {loaded_contract[1]}")
            print(f"  - contract[20] (project_id): {loaded_contract[20]}")
            print(f"  - contract[21] (project_name): {loaded_contract[21]}")

            # project_idの確認
            if loaded_contract[20] is None:
                print("✓ project_idは正しくNULLです")
            else:
                print(f"✗ エラー: project_idがNULLではありません: {loaded_contract[20]}")
        else:
            print("✗ 読み込み失敗")
            return False

        # 3. 更新テスト（project_id=2を設定）
        print("\n3. 更新テスト（project_id=2を設定）...")
        test_contract['id'] = contract_id
        test_contract['project_id'] = 2  # 案件IDを設定
        db.save_order_contract(test_contract)
        print("✓ 更新成功")

        # 4. 更新後の読み込み確認
        print("\n4. 更新後の読み込み確認...")
        updated_contract = db.get_order_contract_by_id(contract_id)
        if updated_contract:
            print(f"✓ 読み込み成功")
            print(f"  - contract[20] (project_id): {updated_contract[20]}")
            print(f"  - contract[21] (project_name): {updated_contract[21]}")

            if updated_contract[20] == 2:
                print("✓ project_idは正しく保存・読み込みされています")
            else:
                print(f"✗ エラー: project_idが期待値と異なります: {updated_contract[20]}")
                return False
        else:
            print("✗ 読み込み失敗")
            return False

        # 5. クリーンアップ（テストデータ削除）
        print("\n5. テストデータをクリーンアップ...")
        db.delete_order_contract(contract_id)
        print("✓ クリーンアップ完了")

        print("\n" + "=" * 60)
        print("✓ すべてのテストが成功しました！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n✗ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_save_and_load()
    exit(0 if success else 1)
