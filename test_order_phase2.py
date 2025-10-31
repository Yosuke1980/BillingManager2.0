"""発注管理機能 Phase 2 のテストスクリプト

Gmail連携機能をテストします。
"""
from order_management.order_number_generator import OrderNumberGenerator
from order_management.email_template import EmailTemplate
from order_management.config import OrderConfig


def test_order_number_generation():
    """発注番号生成をテスト"""
    print("=" * 60)
    print("発注番号生成テスト")
    print("=" * 60)

    generator = OrderNumberGenerator()

    # 今日の日付で発注番号を生成
    order_number = generator.generate_order_number()
    print(f"✓ 発注番号を生成しました: {order_number}")

    # 形式チェック
    if generator.validate_order_number(order_number):
        print(f"✓ 発注番号の形式が正しいです")
    else:
        print(f"✗ 発注番号の形式が不正です")

    # 指定日付で生成
    order_number2 = generator.generate_order_number("2025-08-09")
    print(f"✓ 指定日付の発注番号: {order_number2}")

    # 同じ日付で複数生成（連番確認）
    order_number3 = generator.generate_order_number("2025-08-09")
    print(f"✓ 同日2つ目の発注番号: {order_number3}")

    print()


def test_email_template():
    """メールテンプレートをテスト"""
    print("=" * 60)
    print("メールテンプレート生成テスト")
    print("=" * 60)

    # テストデータ
    data = {
        'contact_person': '田中太郎',
        'order_number': 'RB-20250809-001',
        'project_name': '夏休みイベント',
        'implementation_date': '2025-08-09',
        'item_name': '伊藤出演料',
        'amount': 10000,
        'payment_scheduled_date': '2025-09-30',
    }

    signature = "────────────────────────\n担当: テスト太郎\nEmail: test@example.com\n────────────────────────"

    # 件名生成
    subject = EmailTemplate.generate_subject(
        data['order_number'],
        data['implementation_date'],
        data['project_name'],
        data['item_name']
    )
    print(f"件名: {subject}")

    # 本文生成
    body = EmailTemplate.generate_body(data, signature)
    print("\n本文:")
    print("-" * 60)
    print(body)
    print("-" * 60)

    print("\n✓ メールテンプレートを生成しました")
    print()


def test_config():
    """設定管理をテスト"""
    print("=" * 60)
    print("設定管理テスト")
    print("=" * 60)

    # デフォルト設定を読み込み
    config = OrderConfig.load_config()
    print(f"✓ 設定を読み込みました")

    # Gmail設定を取得
    gmail_config = OrderConfig.get_gmail_config()
    print(f"Gmail設定:")
    print(f"  - アドレス: {gmail_config['address'] or '(未設定)'}")
    print(f"  - IMAPサーバー: {gmail_config['imap_server']}")
    print(f"  - IMAPポート: {gmail_config['imap_port']}")

    # 設定状態チェック
    if OrderConfig.is_gmail_configured():
        print("✓ Gmail設定が完了しています")
    else:
        print("ℹ Gmail設定が未設定です（テスト環境のため正常）")

    print()


def test_gmail_manager_structure():
    """GmailManager構造をテスト（実際の接続は行わない）"""
    print("=" * 60)
    print("GmailManager構造テスト")
    print("=" * 60)

    from order_management.gmail_manager import GmailManager

    # ダミー設定でインスタンス作成
    gmail = GmailManager(
        email_address="test@example.com",
        app_password="dummy_password"
    )

    print(f"✓ GmailManagerのインスタンスを作成しました")
    print(f"  - メールアドレス: {gmail.email_address}")
    print(f"  - IMAPサーバー: {gmail.imap_server}")
    print(f"  - IMAPポート: {gmail.imap_port}")

    print("\nℹ 実際のGmail接続テストは、UIの「接続テスト」ボタンから行ってください")
    print()


def main():
    """メインテスト"""
    print("\n" + "=" * 60)
    print("発注管理機能 Phase 2 テスト開始")
    print("=" * 60 + "\n")

    test_order_number_generation()
    test_email_template()
    test_config()
    test_gmail_manager_structure()

    print("=" * 60)
    print("Phase 2 テスト完了")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. アプリを起動して「発注管理」タブを開く")
    print("2. 「設定」サブタブでGmail設定を行う")
    print("3. 「接続テスト」ボタンでGmail接続を確認")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
