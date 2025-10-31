"""費用マスター移行機能のテストスクリプト"""
from order_management.migrate_expense_master import ExpenseMasterMigrator

def test_migration():
    """移行をテスト実行"""
    print("=" * 60)
    print("費用マスター移行テスト")
    print("=" * 60)

    migrator = ExpenseMasterMigrator()

    print("\n移行を開始します...")
    stats = migrator.migrate()

    print("\n" + "=" * 60)
    print("移行結果")
    print("=" * 60)
    print(f"作成された案件: {stats['projects_created']}件")
    print(f"作成された費用項目: {stats['expenses_created']}件")
    print(f"取引先マッチング成功: {stats['partners_matched']}件")
    print(f"取引先未検出: {stats['partners_not_found']}件")
    print(f"スキップ（既存）: {stats['skipped']}件")
    print(f"エラー: {stats['errors']}件")

    print("\n" + "=" * 60)
    print("移行ログ")
    print("=" * 60)
    for line in migrator.get_migration_log():
        print(line)

    print("\n移行テスト完了")

if __name__ == "__main__":
    test_migration()
