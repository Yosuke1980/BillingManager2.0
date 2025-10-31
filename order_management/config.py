"""発注管理設定

Gmail連携の設定を管理します。
"""
import json
import os


class OrderConfig:
    """発注管理設定クラス"""

    CONFIG_FILE = "order_config.json"

    # デフォルト設定
    DEFAULT_CONFIG = {
        'gmail_address': '',
        'gmail_app_password': '',
        'email_signature': '────────────────────────\n担当: 〇〇\nEmail: xxx@example.com\n────────────────────────',
        'gmail_imap_server': 'imap.gmail.com',
        'gmail_imap_port': 993,
    }

    @classmethod
    def load_config(cls) -> dict:
        """設定ファイルを読み込み"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # デフォルト値とマージ
                    return {**cls.DEFAULT_CONFIG, **config}
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                return cls.DEFAULT_CONFIG.copy()
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def save_config(cls, config: dict) -> bool:
        """設定ファイルを保存"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
            return False

    @classmethod
    def get_gmail_config(cls) -> dict:
        """Gmail設定を取得"""
        config = cls.load_config()
        return {
            'address': config.get('gmail_address', ''),
            'app_password': config.get('gmail_app_password', ''),
            'signature': config.get('email_signature', ''),
            'imap_server': config.get('gmail_imap_server', 'imap.gmail.com'),
            'imap_port': config.get('gmail_imap_port', 993),
        }

    @classmethod
    def is_gmail_configured(cls) -> bool:
        """Gmail設定が完了しているか確認"""
        config = cls.get_gmail_config()
        return bool(config['address'] and config['app_password'])
