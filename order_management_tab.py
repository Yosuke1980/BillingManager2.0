"""発注管理タブ

発注管理機能のメインタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt5.QtCore import Qt
from order_management.ui.supplier_master_widget import SupplierMasterWidget


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

        # 案件一覧タブ（後で実装）
        projects_widget = QWidget()
        projects_layout = QVBoxLayout(projects_widget)
        projects_layout.addWidget(QLabel("案件一覧機能は実装中です"))
        projects_layout.addStretch()

        # 発注先マスタータブ
        self.supplier_widget = SupplierMasterWidget()

        # 設定タブ（後で実装）
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.addWidget(QLabel("設定機能は実装中です"))
        settings_layout.addStretch()

        self.sub_tabs.addTab(projects_widget, "案件一覧")
        self.sub_tabs.addTab(self.supplier_widget, "発注先マスター")
        self.sub_tabs.addTab(settings_widget, "設定")

        layout.addWidget(self.sub_tabs)
