"""マスター管理タブ

案件一覧、取引先マスター、出演者マスター、番組マスター、設定などの
マスターデータ管理機能をサブタブとしてまとめたタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from order_management.ui.production_timeline_widget import ProductionTimelineWidget
from order_management.ui.partner_master_widget import PartnerMasterWidget
from order_management.ui.cast_master_widget import CastMasterWidget
from order_management.ui.production_master_widget import ProductionMasterWidget
from order_management.ui.settings_widget import SettingsWidget


class MasterManagementTab(QWidget):
    """マスター管理タブ

    以下のサブタブを持つ親タブ：
    - タイムライン
    - 取引先マスター
    - 出演者マスター
    - 番組・イベント管理
    - 設定
    """

    def __init__(self, parent_tab_control=None, main_window=None):
        super().__init__()
        self.parent_tab_control = parent_tab_control
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        self.sub_tab_control = QTabWidget()

        # Sub-tab 1: タイムライン
        self.timeline_widget = ProductionTimelineWidget()
        self.sub_tab_control.addTab(self.timeline_widget, "タイムライン")

        # Sub-tab 2: 取引先マスター
        self.partner_widget = PartnerMasterWidget()
        self.sub_tab_control.addTab(self.partner_widget, "取引先マスター")

        # Sub-tab 3: 出演者マスター
        self.cast_widget = CastMasterWidget()
        self.sub_tab_control.addTab(self.cast_widget, "出演者マスター")

        # Sub-tab 4: 番組・イベント管理
        self.production_widget = ProductionMasterWidget()
        self.sub_tab_control.addTab(self.production_widget, "番組・イベント管理")

        # Sub-tab 5: 設定
        self.settings_widget = SettingsWidget()
        self.sub_tab_control.addTab(self.settings_widget, "設定")

        # タブ切り替え時のイベント
        self.sub_tab_control.currentChanged.connect(self.on_tab_changed)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sub_tab_control)
        self.setLayout(layout)

    def on_tab_changed(self, index):
        """タブ切り替え時の処理"""
        if index == 0:  # タイムラインタブ
            self.timeline_widget.load_timeline()
        elif index == 3:  # 番組・イベント管理タブ
            self.production_widget.load_productions()
