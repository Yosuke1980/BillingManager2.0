"""発注管理タブ

発注管理機能のメインタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt
from order_management.ui.projects_main_widget import ProjectsMainWidget
from order_management.ui.partner_master_widget import PartnerMasterWidget
from order_management.ui.cast_master_widget import CastMasterWidget
from order_management.ui.program_master_widget import ProgramMasterWidget
from order_management.ui.order_contract_widget import OrderContractWidget
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

        # 案件一覧タブ
        self.projects_widget = ProjectsMainWidget()

        # 統合取引先マスタータブ
        self.partner_widget = PartnerMasterWidget()

        # 出演者マスタータブ
        self.cast_widget = CastMasterWidget()

        # 番組マスタータブ
        self.program_widget = ProgramMasterWidget()

        # 発注書管理タブ
        self.order_contract_widget = OrderContractWidget()

        # 設定タブ
        self.settings_widget = SettingsWidget()

        self.sub_tabs.addTab(self.projects_widget, "案件一覧")
        self.sub_tabs.addTab(self.partner_widget, "取引先マスター")
        self.sub_tabs.addTab(self.cast_widget, "出演者マスター")
        self.sub_tabs.addTab(self.program_widget, "番組マスター")
        self.sub_tabs.addTab(self.order_contract_widget, "発注書管理")
        self.sub_tabs.addTab(self.settings_widget, "設定")

        # タブ切り替え時にデータを更新
        self.sub_tabs.currentChanged.connect(self.on_tab_changed)

        layout.addWidget(self.sub_tabs)

    def on_tab_changed(self, index):
        """タブ切り替え時の処理"""
        if index == 0:  # 案件一覧タブ
            self.projects_widget.refresh_all()
