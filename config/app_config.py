"""アプリケーション設定

このモジュールはアプリケーション全体の設定値を管理します。
"""
import os


class AppConfig:
    """アプリケーション設定クラス

    アプリケーション全体で使用される設定値を一元管理します。
    """

    # ウィンドウ設定
    WINDOW_TITLE = "ラジオ局支払い・費用管理システム"
    WINDOW_GEOMETRY = (100, 100, 1400, 1600)  # x, y, width, height

    # アプリケーション情報
    APP_VERSION = "1.0"
    APP_DESCRIPTION = "ラジオ局支払い・費用管理システム\nVersion 1.0\n\nPyQt5ベースの業務管理アプリケーション"

    # データフォルダ設定
    @staticmethod
    def get_data_folder():
        """データフォルダのパスを取得

        Returns:
            str: データフォルダの絶対パス
        """
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data"
        )

    # CSVヘッダーマッピング
    HEADER_MAPPING = {
        "おもて情報.件名": "subject",
        "明細情報.明細項目": "project_name",
        "おもて情報.請求元": "payee",
        "おもて情報.支払先コード": "payee_code",
        "明細情報.金額": "amount",
        "おもて情報.自社支払期限": "payment_date",
        "全体情報.状態": "status",
    }

    # タブ名称
    TAB_NAMES = {
        'payment': '💰 支払い情報',
        'order_management': '📄 発注管理',
        'master_management': '📚 マスター管理',
        'production_management': '🎬 番組・イベント管理',
        'data_management': '📂 データ管理',
    }

    # UI設定
    TITLE_LABEL_TEXT = "支払い・費用データ管理システム"
    TITLE_FONT_SIZE = 14
    STATUS_FONT_SIZE = 10

    # ステータスメッセージ
    STATUS_LOADING = "読み込み中..."
    STATUS_NO_CSV = "CSVファイルが見つかりません"
    STATUS_RELOAD_SUCCESS = "データを再読み込みしました"
    STATUS_RELOAD_FAILED = "データの再読み込みに失敗しました"
