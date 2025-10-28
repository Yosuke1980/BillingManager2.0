"""ステータスバー管理モジュール

このモジュールはアプリケーションのステータスバーを管理します。
"""
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class StatusBarManager:
    """ステータスバー管理クラス

    アプリケーションのステータス情報を表示するフレームを管理します。
    """

    def __init__(self, parent=None):
        """初期化

        Args:
            parent: 親ウィジェット
        """
        self.frame = QFrame(parent)
        self.status_label = None
        self.last_update_label = None
        self._setup_ui()

    def _setup_ui(self):
        """UIをセットアップ"""
        layout = QHBoxLayout(self.frame)
        layout.setContentsMargins(0, 5, 0, 0)

        # ステータスラベル（左側）
        self.status_label = QLabel("読み込み中...")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setFont(QFont("", 10))
        layout.addWidget(self.status_label)

        # 余白
        layout.addStretch()

        # 最終更新ラベル（右側）
        self.last_update_label = QLabel("")
        self.last_update_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.last_update_label.setFont(QFont("", 10))
        layout.addWidget(self.last_update_label)

    def get_frame(self):
        """ステータスバーフレームを取得

        Returns:
            QFrame: ステータスバーのフレームウィジェット
        """
        return self.frame

    def set_status(self, text):
        """ステータステキストを設定

        Args:
            text: 表示するステータステキスト
        """
        if self.status_label:
            self.status_label.setText(text)

    def set_last_update(self, text):
        """最終更新テキストを設定

        Args:
            text: 表示する最終更新テキスト
        """
        if self.last_update_label:
            self.last_update_label.setText(text)

    def get_status_label(self):
        """ステータスラベルを取得

        Returns:
            QLabel: ステータスラベル
        """
        return self.status_label

    def get_last_update_label(self):
        """最終更新ラベルを取得

        Returns:
            QLabel: 最終更新ラベル
        """
        return self.last_update_label
