"""番組>案件>発注の階層構造対応マイグレーション

このスクリプトを実行すると、データベーススキーマを拡張します:
1. programsテーブルに program_type, parent_program_id を追加
2. projectsテーブルに project_type を追加
3. 既存データにデフォルト値を設定
"""
import sys
from order_management.database_manager import OrderManagementDB
from utils import log_message


def main():
    """マイグレーションメイン処理"""
    print("=" * 60)
    print("番組>案件>発注の階層構造対応マイグレーション")
    print("=" * 60)
    print()
    print("このスクリプトは以下の変更を行います:")
    print("1. programsテーブルに program_type, parent_program_id カラムを追加")
    print("2. projectsテーブルに project_type カラムを追加")
    print("3. 既存データにデフォルト値を設定")
    print()

    response = input("マイグレーションを実行しますか？ (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("マイグレーションをキャンセルしました")
        return

    print()
    print("マイグレーションを開始します...")
    print()

    db = OrderManagementDB()

    try:
        success = db.migrate_to_hierarchy_structure()

        if success:
            print()
            print("✅ マイグレーションが正常に完了しました！")
            print()
            print("次のステップ:")
            print("1. アプリケーションを起動してください")
            print("2. 番組マスタで「番組種別」が確認できます")
            print("3. 発注書編集画面で「案件」が選択できるようになります")
            print()
        else:
            print()
            print("❌ マイグレーションに失敗しました")
            print("ログを確認してください")
            sys.exit(1)

    except Exception as e:
        print()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
