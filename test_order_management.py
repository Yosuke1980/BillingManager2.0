"""発注管理機能のテストスクリプト

Phase 1の基本機能をテストします。
"""
import sqlite3
from order_management.database_manager import OrderManagementDB


def test_database_creation():
    """データベース作成をテスト"""
    print("=" * 60)
    print("データベース作成テスト")
    print("=" * 60)

    conn = sqlite3.connect("order_management.db")
    cursor = conn.cursor()

    # テーブル一覧を取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"作成されたテーブル数: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    conn.close()

    expected_tables = ['suppliers', 'projects', 'expenses_order', 'order_history', 'status_history']
    actual_tables = [table[0] for table in tables]

    for expected in expected_tables:
        if expected in actual_tables:
            print(f"✓ {expected} テーブルが存在します")
        else:
            print(f"✗ {expected} テーブルが存在しません")

    print()


def test_supplier_operations():
    """発注先マスター操作をテスト"""
    print("=" * 60)
    print("発注先マスター操作テスト")
    print("=" * 60)

    db = OrderManagementDB()

    # 新規発注先を追加
    supplier_data = {
        'name': 'テスト株式会社',
        'contact_person': '田中太郎',
        'email': 'tanaka@test.co.jp',
        'phone': '03-1234-5678',
        'address': '東京都渋谷区',
        'notes': 'テストデータです',
    }

    try:
        supplier_id = db.save_supplier(supplier_data, is_new=True)
        print(f"✓ 発注先を追加しました (ID: {supplier_id})")
    except Exception as e:
        print(f"✗ 発注先の追加に失敗: {e}")
        return

    # 発注先一覧を取得
    suppliers = db.get_suppliers()
    print(f"✓ 発注先一覧を取得しました ({len(suppliers)}件)")

    # IDで発注先を取得
    supplier = db.get_supplier_by_id(supplier_id)
    if supplier:
        print(f"✓ 発注先を取得しました: {supplier[1]}")
    else:
        print("✗ 発注先の取得に失敗")

    # 発注先を更新
    supplier_data['id'] = supplier_id
    supplier_data['contact_person'] = '佐藤次郎'
    try:
        db.save_supplier(supplier_data, is_new=False)
        print("✓ 発注先を更新しました")
    except Exception as e:
        print(f"✗ 発注先の更新に失敗: {e}")

    # 発注先を削除
    try:
        db.delete_supplier(supplier_id)
        print("✓ 発注先を削除しました")
    except Exception as e:
        print(f"✗ 発注先の削除に失敗: {e}")

    print()


def test_project_operations():
    """案件操作をテスト"""
    print("=" * 60)
    print("案件操作テスト")
    print("=" * 60)

    db = OrderManagementDB()

    # 新規案件を追加
    project_data = {
        'name': '夏休みイベント',
        'date': '2025-08-09',
        'type': '単発',
        'budget': 150000.0,
    }

    try:
        project_id = db.save_project(project_data, is_new=True)
        print(f"✓ 案件を追加しました (ID: {project_id})")
    except Exception as e:
        print(f"✗ 案件の追加に失敗: {e}")
        return

    # 案件一覧を取得
    projects = db.get_projects()
    print(f"✓ 案件一覧を取得しました ({len(projects)}件)")

    # IDで案件を取得
    project = db.get_project_by_id(project_id)
    if project:
        print(f"✓ 案件を取得しました: {project[1]}")
    else:
        print("✗ 案件の取得に失敗")

    # 予算・実績サマリーを取得
    summary = db.get_project_summary(project_id)
    print(f"✓ サマリー取得: 予算={summary['budget']:,.0f}円, 実績={summary['actual']:,.0f}円, 残={summary['remaining']:,.0f}円")

    # 案件を削除
    try:
        db.delete_project(project_id)
        print("✓ 案件を削除しました")
    except Exception as e:
        print(f"✗ 案件の削除に失敗: {e}")

    print()


def main():
    """メインテスト"""
    print("\n" + "=" * 60)
    print("発注管理機能 Phase 1 テスト開始")
    print("=" * 60 + "\n")

    test_database_creation()
    test_supplier_operations()
    test_project_operations()

    print("=" * 60)
    print("テスト完了")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
