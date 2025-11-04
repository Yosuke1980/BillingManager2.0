"""業務種別カラム追加のマイグレーションスクリプト

order_contractsテーブルに業務種別（制作/出演）カラムを追加します。
"""
from order_management.database_manager import OrderManagementDB
from utils import log_message


def main():
    """メイン関数"""
    print("業務種別カラム追加のマイグレーションを開始します...")

    db = OrderManagementDB()

    # マイグレーション実行
    success = db.migrate_add_work_type()

    if success:
        print("✅ マイグレーションが完了しました！")
        print("\n追加されたカラム:")
        print("  - work_type: 業務種別（'制作' or '出演'、デフォルト: '制作'）")
        print("\n次のステップ:")
        print("  1. アプリケーションを起動してください")
        print("  2. 発注書編集画面で業務種別を選択できます")
        print("  3. 業務種別に応じて画面項目が自動調整されます")
    else:
        print("❌ マイグレーションに失敗しました")
        print("詳細はログを確認してください")


if __name__ == "__main__":
    main()
