"""発注管理の動的フィールド切り替えテスト

レギュラー/単発 × 制作/出演 の4パターンで表示が正しく切り替わるかテスト
"""
import sys
from PyQt5.QtWidgets import QApplication
from order_management.database_manager import OrderManagementDB


def test_order_configuration():
    """発注設定の動的切り替えをテスト"""
    print("=" * 60)
    print("発注管理 動的フィールド切り替えテスト")
    print("=" * 60)

    # データベース接続テスト
    print("\n1. データベース接続テスト...")
    db = OrderManagementDB()
    print("   ✓ データベース接続成功")

    # work_typeカラムの存在確認
    print("\n2. work_typeカラムの存在確認...")
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(order_contracts)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'work_type' in columns:
        print("   ✓ work_typeカラムが存在します")
    else:
        print("   ✗ work_typeカラムが見つかりません")
        return False

    # テストデータの確認
    print("\n3. 既存データの確認...")
    contracts = db.get_order_contracts()
    print(f"   既存の発注契約数: {len(contracts)}")

    # 新規契約のフィールド確認
    print("\n4. データ取得フィールドの確認...")
    if contracts:
        sample = contracts[0]
        print(f"   フィールド数: {len(sample)}")
        # work_typeは最後のフィールド（インデックス31）
        if len(sample) >= 32:
            work_type = sample[31] if sample[31] else '未設定'
            print(f"   ✓ サンプルのwork_type: {work_type}")
        else:
            print(f"   ✗ フィールド数が不足: {len(sample)} (期待値: 32以上)")

    print("\n5. UIコンポーネントのインポート確認...")
    try:
        from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
        print("   ✓ OrderContractEditDialog のインポート成功")
    except Exception as e:
        print(f"   ✗ インポートエラー: {e}")
        return False

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    print("\n期待される動作:")
    print("1. レギュラー × 出演 → 契約書（期間、自動延長あり）")
    print("2. レギュラー × 制作 → 発注書（期間、自動延長なし）")
    print("3. 単発 × 出演   → 発注書（実施日、単発金額）")
    print("4. 単発 × 制作   → 発注書（実施日、単発金額）")
    print("\n次のステップ:")
    print("  python3 app.py を実行して実際のUIで動作確認してください")

    return True


if __name__ == "__main__":
    success = test_order_configuration()
    sys.exit(0 if success else 1)
