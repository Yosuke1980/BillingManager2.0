"""アラートウィジェット

アラート情報を表示するウィジェットです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from order_management.alert_manager import AlertManager


class AlertWidget(QWidget):
    """アラート表示ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.alert_manager = AlertManager()
        self._setup_ui()

    def _setup_ui(self):
        """UIセットアップ"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # 初期状態では非表示
        self.setVisible(False)

    def update_alerts(self):
        """アラートを更新"""
        # 既存のウィジェットをクリア
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # アラート取得
        alerts = self.alert_manager.get_all_alerts()
        invoice_waiting = alerts['invoice_waiting']
        draft_unsent = alerts['draft_unsent']

        # アラートがない場合は非表示
        if not invoice_waiting and not draft_unsent:
            self.setVisible(False)
            return

        # アラートがある場合は表示
        self.setVisible(True)

        # フレーム作成
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffc107;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        frame_layout = QVBoxLayout(frame)

        # 請求書未着アラート
        if invoice_waiting:
            title = QLabel(f"⚠️ 請求書未着: {len(invoice_waiting)}件")
            title.setStyleSheet("font-weight: bold; color: #856404; font-size: 14px;")
            frame_layout.addWidget(title)

            for alert in invoice_waiting[:5]:  # 最大5件表示
                text = f"• {alert['project_date']} {alert['project_name']} - {alert['item_name']}"
                if alert['supplier_name']:
                    text += f" ({alert['supplier_name']})"

                label = QLabel(text)
                label.setStyleSheet("color: #856404; padding-left: 10px;")
                frame_layout.addWidget(label)

            if len(invoice_waiting) > 5:
                more_label = QLabel(f"... 他{len(invoice_waiting) - 5}件")
                more_label.setStyleSheet("color: #856404; padding-left: 10px; font-style: italic;")
                frame_layout.addWidget(more_label)

        # 下書き未送信アラート
        if draft_unsent:
            if invoice_waiting:
                frame_layout.addSpacing(10)

            title = QLabel(f"📧 下書き未送信: {len(draft_unsent)}件")
            title.setStyleSheet("font-weight: bold; color: #004085; font-size: 14px;")
            frame_layout.addWidget(title)

            for alert in draft_unsent[:5]:  # 最大5件表示
                text = f"• {alert['project_date']} {alert['project_name']} - {alert['item_name']}"
                if alert['supplier_name']:
                    text += f" ({alert['supplier_name']})"

                label = QLabel(text)
                label.setStyleSheet("color: #004085; padding-left: 10px;")
                frame_layout.addWidget(label)

            if len(draft_unsent) > 5:
                more_label = QLabel(f"... 他{len(draft_unsent) - 5}件")
                more_label.setStyleSheet("color: #004085; padding-left: 10px; font-style: italic;")
                frame_layout.addWidget(more_label)

        self.layout.addWidget(frame)
