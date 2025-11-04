"""契約自動延長機能のマイグレーションスクリプト

データベースに契約自動延長用のカラムとテーブルを追加します。
"""
from order_management.database_manager import OrderManagementDB
from utils import log_message


def main():
    """メイン関数"""
    print("契約自動延長機能のマイグレーションを開始します...")

    db = OrderManagementDB()

    # マイグレーション実行
    success = db.migrate_add_auto_renewal_fields()

    if success:
        print("✅ マイグレーションが完了しました！")
        print("\n追加された機能:")
        print("  - 契約自動延長設定（契約ごとに有効/無効を設定可能）")
        print("  - 延長期間の設定（デフォルト: 3ヶ月）")
        print("  - 終了通知受領日の記録")
        print("  - 延長履歴の記録")
        print("\n次のステップ:")
        print("  1. アプリケーションを起動してください")
        print("  2. 発注管理タブで「自動延長チェック」ボタンを使用できます")
        print("  3. 契約編集画面で自動延長設定を変更できます")
    else:
        print("❌ マイグレーションに失敗しました")
        print("詳細はログを確認してください")


if __name__ == "__main__":
    main()
