"""マスター管理タブ

取引先マスター、出演者マスターなどの
マスターデータ管理機能をサブタブとしてまとめたタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from order_management.ui.partner_master_widget import PartnerMasterWidget
from order_management.ui.cast_master_widget import CastMasterWidget


class MasterManagementTab(QWidget):
    """マスター管理タブ

    以下のサブタブを持つ親タブ：
    - 取引先マスター
    - 出演者マスター
    """

    def __init__(self, parent_tab_control=None, main_window=None):
        super().__init__()
        self.parent_tab_control = parent_tab_control
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        self.sub_tab_control = QTabWidget()

        # Sub-tab 1: 取引先マスター
        self.partner_widget = PartnerMasterWidget()
        self.sub_tab_control.addTab(self.partner_widget, "取引先マスター")

        # Sub-tab 2: 出演者マスター
        self.cast_widget = CastMasterWidget()
        self.sub_tab_control.addTab(self.cast_widget, "出演者マスター")

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sub_tab_control)
        self.setLayout(layout)
