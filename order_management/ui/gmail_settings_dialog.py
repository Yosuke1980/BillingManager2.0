"""Gmail設定ダイアログ

Gmail連携に必要な設定を行うダイアログです。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QDialogButtonBox, QLabel, QGroupBox
)
from PyQt5.QtCore import Qt
from order_management.config import OrderConfig


class GmailSettingsDialog(QDialog):
    """Gmail設定ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gmail連携設定")
        self.setMinimumWidth(600)
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        """UIセットアップ"""
        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)

        # 説明ラベル
        info_label = QLabel(
            "Gmail連携を使用するには、Googleアカウントでアプリパスワードを生成してください。\n"
            "アプリパスワードの生成方法: https://support.google.com/accounts/answer/185833"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)

        # Gmail設定グループ
        gmail_group = QGroupBox("Gmail設定")
        gmail_layout = QFormLayout()

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@gmail.com")

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("16桁のアプリパスワード")

        gmail_layout.addRow("メールアドレス:", self.email_edit)
        gmail_layout.addRow("アプリパスワード:", self.password_edit)

        gmail_group.setLayout(gmail_layout)
        layout.addWidget(gmail_group)

        # 署名設定グループ
        signature_group = QGroupBox("メール署名")
        signature_layout = QVBoxLayout()

        self.signature_edit = QTextEdit()
        self.signature_edit.setPlaceholderText(
            "────────────────────────\n"
            "担当: 〇〇\n"
            "Email: xxx@example.com\n"
            "────────────────────────"
        )
        self.signature_edit.setMaximumHeight(150)

        signature_layout.addWidget(self.signature_edit)
        signature_group.setLayout(signature_layout)
        layout.addWidget(signature_group)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_current_settings(self):
        """現在の設定を読み込み"""
        config = OrderConfig.get_gmail_config()
        self.email_edit.setText(config.get('address', ''))
        self.password_edit.setText(config.get('app_password', ''))
        self.signature_edit.setPlainText(config.get('signature', ''))

    def get_settings(self) -> dict:
        """入力された設定を取得"""
        return {
            'gmail_address': self.email_edit.text().strip(),
            'gmail_app_password': self.password_edit.text().strip(),
            'email_signature': self.signature_edit.toPlainText(),
        }

    def accept(self):
        """OK押下時の処理"""
        settings = self.get_settings()

        # バリデーション
        if not settings['gmail_address']:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "入力エラー", "メールアドレスを入力してください")
            return

        if not settings['gmail_app_password']:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "入力エラー", "アプリパスワードを入力してください")
            return

        # 設定を保存
        config = OrderConfig.load_config()
        config.update(settings)
        if OrderConfig.save_config(config):
            super().accept()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "エラー", "設定の保存に失敗しました")
