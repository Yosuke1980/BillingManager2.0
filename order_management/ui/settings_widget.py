"""設定ウィジェット

発注管理の設定を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from order_management.config import OrderConfig
from order_management.ui.gmail_settings_dialog import GmailSettingsDialog
from order_management.gmail_manager import GmailManager


class SettingsWidget(QWidget):
    """設定ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_current_status()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # Gmail設定グループ
        gmail_group = QGroupBox("Gmail連携設定")
        gmail_layout = QVBoxLayout()

        self.status_label = QLabel("未設定")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        button_layout = QHBoxLayout()
        self.settings_button = QPushButton("Gmail設定")
        self.test_button = QPushButton("接続テスト")

        self.settings_button.clicked.connect(self.open_gmail_settings)
        self.test_button.clicked.connect(self.test_gmail_connection)

        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()

        gmail_layout.addWidget(QLabel("Gmail連携の状態:"))
        gmail_layout.addWidget(self.status_label)
        gmail_layout.addLayout(button_layout)

        gmail_group.setLayout(gmail_layout)
        layout.addWidget(gmail_group)

        # 使い方の説明
        info_group = QGroupBox("使い方")
        info_layout = QVBoxLayout()

        info_text = QLabel(
            "1. 「Gmail設定」ボタンをクリックして、Gmailアドレスとアプリパスワードを設定してください\n"
            "2. 「接続テスト」ボタンでGmail接続を確認できます\n"
            "3. 設定完了後、案件一覧タブから発注メールの下書きを作成できます\n\n"
            "※アプリパスワードの取得方法:\n"
            "  Googleアカウントの「セキュリティ」→「2段階認証プロセス」→「アプリパスワード」から生成"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #555; padding: 10px;")

        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()

    def _load_current_status(self):
        """現在の設定状態を読み込み"""
        if OrderConfig.is_gmail_configured():
            config = OrderConfig.get_gmail_config()
            self.status_label.setText(f"設定済: {config['address']}")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.status_label.setText("未設定")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")

    def open_gmail_settings(self):
        """Gmail設定ダイアログを開く"""
        dialog = GmailSettingsDialog(self)
        if dialog.exec_():
            self._load_current_status()
            QMessageBox.information(self, "成功", "Gmail設定を保存しました")

    def test_gmail_connection(self):
        """Gmail接続をテスト"""
        if not OrderConfig.is_gmail_configured():
            QMessageBox.warning(self, "警告", "Gmail設定が未設定です。\n先に「Gmail設定」を行ってください。")
            return

        config = OrderConfig.get_gmail_config()

        try:
            gmail = GmailManager(
                config['address'],
                config['app_password'],
                config['imap_server'],
                config['imap_port']
            )

            success, message = gmail.test_connection()

            if success:
                QMessageBox.information(self, "接続成功", message)
            else:
                QMessageBox.warning(self, "接続失敗", message)

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"接続テスト中にエラーが発生しました:\n{str(e)}")
