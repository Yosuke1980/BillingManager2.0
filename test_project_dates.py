"""案件の日付フィールドと複製機能のテストスクリプト

レギュラー案件の開始日・終了日と案件複製機能をテストします。
"""
from order_management.database_manager import OrderManagementDB


def test_regular_project_dates():
    """レギュラー案件の日付フィールドをテスト"""
    print("=" * 60)
    print("レギュラー案件の日付フィールドテスト")
    print("=" * 60)

    db = OrderManagementDB()

    # レギュラー案件を作成
    project_data = {
        'name': 'テストレギュラー案件',
        'date': '2025-04-01',  # 開始日としても使用
        'type': 'レギュラー',
        'budget': 500000.0,
        'start_date': '2025-04-01',
        'end_date': '2025-09-30',
    }

    project_id = db.save_project(project_data, is_new=True)
    print(f"✓ レギュラー案件を作成しました: ID={project_id}")

    # 作成した案件を取得
    project = db.get_project_by_id(project_id)
    if project:
        print(f"  - 案件名: {project[1]}")
        print(f"  - タイプ: {project[3]}")
        print(f"  - 開始日: {project[6]}")
        print(f"  - 終了日: {project[7]}")

    # 単発案件を作成（比較用）
    single_project_data = {
        'name': 'テスト単発案件',
        'date': '2025-08-09',
        'type': '単発',
        'budget': 100000.0,
        'start_date': '',
        'end_date': '',
    }

    single_project_id = db.save_project(single_project_data, is_new=True)
    print(f"\n✓ 単発案件を作成しました: ID={single_project_id}")

    # 作成した案件を取得
    single_project = db.get_project_by_id(single_project_id)
    if single_project:
        print(f"  - 案件名: {single_project[1]}")
        print(f"  - タイプ: {single_project[3]}")
        print(f"  - 実施日: {single_project[2]}")
        print(f"  - 開始日: {single_project[6] or '(なし)'}")
        print(f"  - 終了日: {single_project[7] or '(なし)'}")

    print()
    return project_id, single_project_id


def test_project_duplication(project_id):
    """案件複製機能をテスト"""
    print("=" * 60)
    print("案件複製機能テスト")
    print("=" * 60)

    db = OrderManagementDB()

    # 元の案件に費用項目を追加（order_numberを一意にする）
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    expense1_data = {
        'project_id': project_id,
        'item_name': 'テスト費用項目1',
        'supplier_id': None,
        'amount': 50000.0,
        'status': '発注予定',
        'order_number': f'TEST-{timestamp}-001',
        'implementation_date': '2025-05-15',
        'payment_scheduled_date': '2025-06-30',
        'notes': 'テスト用の費用項目',
    }

    expense2_data = {
        'project_id': project_id,
        'item_name': 'テスト費用項目2',
        'supplier_id': None,
        'amount': 30000.0,
        'status': '発注済',
        'order_number': f'TEST-{timestamp}-002',
        'implementation_date': '2025-06-15',
        'payment_scheduled_date': '2025-07-31',
        'notes': 'テスト用の費用項目2',
    }

    expense1_id = db.save_expense_order(expense1_data, is_new=True)
    expense2_id = db.save_expense_order(expense2_data, is_new=True)
    print(f"✓ 元の案件に費用項目を追加しました: {expense1_id}, {expense2_id}")

    # 元の案件情報を取得
    original_project = db.get_project_by_id(project_id)
    print(f"\n元の案件:")
    print(f"  - 案件名: {original_project[1]}")
    print(f"  - タイプ: {original_project[3]}")
    print(f"  - 予算: {original_project[4]:,.0f}円")
    print(f"  - 開始日: {original_project[6]}")
    print(f"  - 終了日: {original_project[7]}")

    original_expenses = db.get_expenses_by_project(project_id)
    print(f"  - 費用項目: {len(original_expenses)}件")

    # 案件を複製
    new_project_id = db.duplicate_project(project_id)
    print(f"\n✓ 案件を複製しました: 新ID={new_project_id}")

    # 複製された案件情報を取得
    new_project = db.get_project_by_id(new_project_id)
    print(f"\n複製された案件:")
    print(f"  - 案件名: {new_project[1]}")
    print(f"  - タイプ: {new_project[3]}")
    print(f"  - 予算: {new_project[4]:,.0f}円")
    print(f"  - 開始日: {new_project[6]}")
    print(f"  - 終了日: {new_project[7]}")

    new_expenses = db.get_expenses_by_project(new_project_id)
    print(f"  - 費用項目: {len(new_expenses)}件")

    # 検証
    if new_project[1] == original_project[1] + "（コピー）":
        print("\n✓ 案件名に「（コピー）」が追加されました")
    else:
        print(f"\n✗ 案件名が正しくコピーされませんでした: {new_project[1]}")

    if new_project[3] == original_project[3]:
        print("✓ タイプが正しくコピーされました")
    else:
        print(f"✗ タイプが正しくコピーされませんでした")

    if new_project[4] == original_project[4]:
        print("✓ 予算が正しくコピーされました")
    else:
        print(f"✗ 予算が正しくコピーされませんでした")

    if new_project[6] == original_project[6] and new_project[7] == original_project[7]:
        print("✓ 開始日と終了日が正しくコピーされました")
    else:
        print(f"✗ 日付が正しくコピーされませんでした")

    if len(new_expenses) == len(original_expenses):
        print(f"✓ 費用項目が正しくコピーされました（{len(new_expenses)}件）")
    else:
        print(f"✗ 費用項目が正しくコピーされませんでした")

    print()


def main():
    """メインテスト"""
    print("\n" + "=" * 60)
    print("案件の日付フィールドと複製機能テスト開始")
    print("=" * 60 + "\n")

    # レギュラー案件と単発案件を作成
    project_id, single_project_id = test_regular_project_dates()

    # 案件複製機能をテスト
    test_project_duplication(project_id)

    print("=" * 60)
    print("テスト完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. アプリを起動して「発注管理」タブを開く")
    print("2. 「案件」サブタブで案件一覧を確認")
    print("3. レギュラー案件の日付表示が「開始日 ～ 終了日」になっているか確認")
    print("4. 案件を選択して「複製」ボタンをクリック")
    print("5. 新しい案件編集ダイアログで、タイプを「レギュラー」と「単発」で切り替え")
    print("6. 日付フィールドが適切に切り替わることを確認")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
