"""発注管理タブ

発注管理機能のメインタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore import Qt
from order_management.ui.supplier_master_widget import SupplierMasterWidget
from order_management.ui.settings_widget import SettingsWidget


class OrderManagementTab(QWidget):
    """発注管理タブ"""

    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # サブタブ
        self.sub_tabs = QTabWidget()

        # 案件一覧タブ（Phase 3で実装予定）
        projects_widget = QWidget()
        projects_layout = QVBoxLayout(projects_widget)
        info_label = QLabel(
            "案件一覧機能はPhase 3で実装予定です。\n\n"
            "現在利用可能な機能:\n"
            "• 発注先マスター: 発注先の登録・編集・削除\n"
            "• 設定: Gmail連携の設定"
        )
        info_label.setStyleSheet("color: #666; padding: 20px; font-size: 12px;")
        projects_layout.addWidget(info_label)
        projects_layout.addStretch()

        # 発注先マスタータブ
        self.supplier_widget = SupplierMasterWidget()

        # 設定タブ
        self.settings_widget = SettingsWidget()

        self.sub_tabs.addTab(projects_widget, "案件一覧")
        self.sub_tabs.addTab(self.supplier_widget, "発注先マスター")
        self.sub_tabs.addTab(self.settings_widget, "設定")

        layout.addWidget(self.sub_tabs)
