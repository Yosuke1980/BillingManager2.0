"""統合取引先マスタのテストスクリプト

Phase 6で実装した統合取引先マスタ機能をテストします。
"""
from partner_manager import PartnerManager


def test_partner_migration():
    """データマイグレーションのテスト"""
    print("=" * 60)
    print("統合取引先マスタ - データマイグレーションテスト")
    print("=" * 60)

    pm = PartnerManager()

    # 取引先区分ごとの件数を確認
    counts = pm.get_partner_count_by_type()
    print(f"\n取引先区分ごとの件数:")
    print(f"  発注先: {counts['発注先']}件")
    print(f"  支払先: {counts['支払先']}件")
    print(f"  両方: {counts['両方']}件")
    print(f"  合計: {counts['合計']}件")

    if counts['合計'] > 0:
        print("\n✓ データマイグレーションが成功しています")
    else:
        print("\n✗ データマイグレーションが実行されていません")


def test_partner_crud():
    """CRUD操作のテスト"""
    print("\n" + "=" * 60)
    print("統合取引先マスタ - CRUD操作テスト")
    print("=" * 60)

    pm = PartnerManager()

    # 1. 新規作成
    print("\n1. 新規取引先を作成")
    from datetime import datetime
    unique_code = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"

    partner_data = {
        'name': f'テスト取引先株式会社_{unique_code}',
        'code': unique_code,
        'contact_person': 'テスト太郎',
        'email': 'test@example.com',
        'phone': '03-1234-5678',
        'address': '東京都渋谷区',
        'partner_type': '両方',
        'notes': 'テスト用の取引先',
    }

    try:
        partner_id = pm.save_partner(partner_data, is_new=True)
        print(f"✓ 取引先を作成しました: ID={partner_id}")
    except Exception as e:
        print(f"✗ 取引先の作成に失敗しました: {e}")
        return

    # 2. 取得
    print("\n2. 作成した取引先を取得")
    partner = pm.get_partner_by_id(partner_id)
    if partner:
        print(f"✓ 取引先を取得しました:")
        print(f"  ID: {partner[0]}")
        print(f"  名前: {partner[1]}")
        print(f"  コード: {partner[2]}")
        print(f"  担当者: {partner[3]}")
        print(f"  取引先区分: {partner[7]}")
    else:
        print(f"✗ 取引先の取得に失敗しました")
        return

    # 3. 更新
    print("\n3. 取引先情報を更新")
    update_data = {
        'id': partner_id,
        'name': f'テスト取引先株式会社_{unique_code}',
        'code': unique_code,
        'contact_person': 'テスト次郎',  # 変更
        'email': 'test2@example.com',  # 変更
        'phone': '03-1234-5678',
        'address': '東京都渋谷区',
        'partner_type': '発注先',  # 変更
        'notes': 'テスト用の取引先（更新済み）',  # 変更
    }

    try:
        pm.save_partner(update_data, is_new=False)
        print(f"✓ 取引先を更新しました")

        # 更新後の情報を確認
        updated = pm.get_partner_by_id(partner_id)
        print(f"  担当者: {updated[3]}")
        print(f"  メール: {updated[4]}")
        print(f"  取引先区分: {updated[7]}")
    except Exception as e:
        print(f"✗ 取引先の更新に失敗しました: {e}")

    # 4. 検索
    print("\n4. 取引先を検索")
    results = pm.get_partners(search_term="テスト")
    print(f"✓ 「テスト」で検索: {len(results)}件")
    for result in results[:3]:  # 最大3件表示
        print(f"  - {result[1]} ({result[2]}) [{result[7]}]")

    # 5. フィルタリング
    print("\n5. 取引先区分でフィルタリング")
    suppliers = pm.get_partners(partner_type="発注先")
    payees = pm.get_partners(partner_type="支払先")
    both = pm.get_partners(partner_type="両方")
    print(f"  発注先: {len(suppliers)}件")
    print(f"  支払先: {len(payees)}件")
    print(f"  両方: {len(both)}件")

    # 6. 重複チェック
    print("\n6. 重複チェック")
    is_dup_name = pm.check_duplicate_name(f'テスト取引先株式会社_{unique_code}', exclude_id=partner_id)
    is_dup_code = pm.check_duplicate_code(unique_code, exclude_id=partner_id)
    print(f"  名前の重複: {'あり' if is_dup_name else 'なし'}")
    print(f"  コードの重複: {'あり' if is_dup_code else 'なし'}")

    # 7. 削除
    print("\n7. テスト用取引先を削除")
    try:
        pm.delete_partner(partner_id)
        print(f"✓ 取引先を削除しました")

        # 削除確認
        deleted = pm.get_partner_by_id(partner_id)
        if deleted is None:
            print(f"✓ 削除が確認できました")
        else:
            print(f"✗ 削除に失敗しました")
    except Exception as e:
        print(f"✗ 取引先の削除に失敗しました: {e}")


def main():
    """メインテスト"""
    print("\n" + "=" * 60)
    print("Phase 6: 統合取引先マスタ機能テスト")
    print("=" * 60 + "\n")

    # データマイグレーションのテスト
    test_partner_migration()

    # CRUD操作のテスト
    test_partner_crud()

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. アプリを起動して取引先マスタが正常に動作することを確認")
    print("2. 統合取引先マスタUI画面を作成")
    print("3. 既存機能（発注管理）の参照先をpartnersに変更")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
