"""発注書管理機能のテスト"""
import os
import sys
from datetime import datetime, timedelta

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from order_management.database_manager import OrderManagementDB


def test_order_contracts():
    """発注書管理のテスト"""
    db = OrderManagementDB("order_management.db")

    print("=" * 60)
    print("発注書管理機能のテスト")
    print("=" * 60)

    # 番組を取得
    programs = db.get_programs()
    if not programs:
        print("❌ 番組データが見つかりません")
        return False

    print(f"\n✅ 番組データ: {len(programs)}件")
    test_program = programs[0]
    print(f"   テスト番組: {test_program[1]} (ID: {test_program[0]})")

    # 取引先を取得
    partners = db.get_partners()
    if not partners:
        print("❌ 取引先データが見つかりません")
        return False

    print(f"\n✅ 取引先データ: {len(partners)}件")
    test_partner = partners[0]
    print(f"   テスト取引先: {test_partner[1]} (ID: {test_partner[0]})")

    # テスト用の発注書データを作成
    today = datetime.now()
    contract_data = {
        'program_id': test_program[0],
        'partner_id': test_partner[0],
        'contract_start_date': today.strftime('%Y-%m-%d'),
        'contract_end_date': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
        'contract_period_type': '半年',
        'pdf_status': '未配布',
        'pdf_file_path': '',
        'pdf_distributed_date': '',
        'confirmed_by': '',
        'notes': 'テスト発注書'
    }

    # 発注書を追加
    print("\n--- 発注書の追加テスト ---")
    try:
        contract_id = db.save_order_contract(contract_data)
        print(f"✅ 発注書追加成功: ID={contract_id}")
    except Exception as e:
        print(f"❌ 発注書追加失敗: {str(e)}")
        return False

    # 発注書を取得
    print("\n--- 発注書の取得テスト ---")
    try:
        contract = db.get_order_contract_by_id(contract_id)
        if contract:
            print(f"✅ 発注書取得成功:")
            print(f"   番組名: {contract[2]}")
            print(f"   取引先: {contract[4]}")
            print(f"   期間: {contract[5]} ～ {contract[6]}")
            print(f"   契約期間: {contract[7]}")
            print(f"   PDFステータス: {contract[8]}")
        else:
            print("❌ 発注書が見つかりません")
            return False
    except Exception as e:
        print(f"❌ 発注書取得失敗: {str(e)}")
        return False

    # 発注書を更新
    print("\n--- 発注書の更新テスト ---")
    try:
        contract_data['id'] = contract_id
        contract_data['pdf_status'] = '配布済'
        contract_data['confirmed_by'] = 'テスト担当者'
        db.save_order_contract(contract_data)
        print("✅ 発注書更新成功")

        updated_contract = db.get_order_contract_by_id(contract_id)
        if updated_contract[8] == '配布済':
            print(f"   更新確認成功: PDFステータス={updated_contract[8]}")
        else:
            print(f"❌ 更新確認失敗: PDFステータス={updated_contract[8]}")
            return False
    except Exception as e:
        print(f"❌ 発注書更新失敗: {str(e)}")
        return False

    # PDFステータスの更新テスト
    print("\n--- PDFステータス更新テスト ---")
    try:
        db.update_pdf_status(contract_id, '受領確認済', today.strftime('%Y-%m-%d'), 'テスト確認者')
        print("✅ PDFステータス更新成功")

        updated_contract = db.get_order_contract_by_id(contract_id)
        if updated_contract[8] == '受領確認済':
            print(f"   更新確認成功: PDFステータス={updated_contract[8]}, 確認者={updated_contract[10]}")
        else:
            print(f"❌ 更新確認失敗")
            return False
    except Exception as e:
        print(f"❌ PDFステータス更新失敗: {str(e)}")
        return False

    # 番組マスタと同期テスト
    print("\n--- 番組マスタ同期テスト ---")
    try:
        # 元の番組情報を確認
        programs = db.get_programs()
        original_program = None
        for prog in programs:
            if prog[0] == test_program[0]:
                original_program = prog
                break

        print(f"   同期前の番組期間: {original_program[3]} ～ {original_program[4]}")

        # 同期実行
        if db.sync_contract_to_program(contract_id):
            print("✅ 番組マスタ同期成功")

            # 同期後の番組情報を確認
            programs = db.get_programs()
            synced_program = None
            for prog in programs:
                if prog[0] == test_program[0]:
                    synced_program = prog
                    break

            print(f"   同期後の番組期間: {synced_program[3]} ～ {synced_program[4]}")

            if synced_program[3] == contract_data['contract_start_date'] and \
               synced_program[4] == contract_data['contract_end_date']:
                print("   同期確認成功: 期間が正しく更新されました")
            else:
                print(f"❌ 同期確認失敗")
                return False
        else:
            print("❌ 番組マスタ同期失敗")
            return False
    except Exception as e:
        print(f"❌ 番組マスタ同期失敗: {str(e)}")
        return False

    # 期限切れ間近の発注書取得テスト
    print("\n--- 期限切れ間近の発注書取得テスト ---")
    try:
        # 期限間近の発注書を追加
        near_expiry_data = contract_data.copy()
        near_expiry_data.pop('id')
        near_expiry_data['contract_start_date'] = today.strftime('%Y-%m-%d')
        near_expiry_data['contract_end_date'] = (today + timedelta(days=20)).strftime('%Y-%m-%d')
        near_expiry_data['notes'] = 'テスト期限間近発注書'

        near_expiry_id = db.save_order_contract(near_expiry_data)
        print(f"✅ 期限間近の発注書追加: ID={near_expiry_id}")

        # 期限切れ間近を取得
        expiring = db.get_expiring_contracts(days_before=30)
        print(f"✅ 期限切れ間近の発注書: {len(expiring)}件")

        found = False
        for exp in expiring:
            if exp[0] == near_expiry_id:
                found = True
                print(f"   - {exp[2]} (期限: {exp[6]})")

        if found:
            print("   期限切れ検出成功")
        else:
            print("❌ 期限切れ検出失敗")
            return False

        # クリーンアップ
        db.delete_order_contract(near_expiry_id)
        print(f"   テストデータ削除: ID={near_expiry_id}")

    except Exception as e:
        print(f"❌ 期限切れテスト失敗: {str(e)}")
        return False

    # 発注書を削除
    print("\n--- 発注書の削除テスト ---")
    try:
        db.delete_order_contract(contract_id)
        print("✅ 発注書削除成功")

        deleted_contract = db.get_order_contract_by_id(contract_id)
        if deleted_contract is None:
            print("   削除確認成功: 発注書が正しく削除されました")
        else:
            print("❌ 削除確認失敗: 発注書がまだ存在します")
            return False
    except Exception as e:
        print(f"❌ 発注書削除失敗: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("✅ すべてのテストが成功しました！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_order_contracts()
    sys.exit(0 if success else 1)
