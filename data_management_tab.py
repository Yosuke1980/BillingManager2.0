"""データ管理タブ

費用管理、費用マスター、発注チェック、発注・支払照合などの
データ整理・管理機能をサブタブとしてまとめたタブです。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from expense_tab import ExpenseTab
from master_tab import MasterTab
from order_check_tab import OrderCheckTab
from order_payment_reconciliation_tab import OrderPaymentReconciliationTab


class DataManagementTab(QWidget):
    """データ管理タブ

    以下のサブタブを持つ親タブ：
    - 費用管理
    - 費用マスター
    - 発注チェック
    - 発注・支払照合
    """

    def __init__(self, parent_tab_control, main_window):
        super().__init__()
        self.parent_tab_control = parent_tab_control
        self.main_window = main_window

        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        # サブタブウィジェット作成
        self.sub_tab_control = QTabWidget()

        # サブタブ1: 費用管理
        self.expense_tab = ExpenseTab(self.parent_tab_control, self.main_window)
        self.sub_tab_control.addTab(self.expense_tab, "費用管理")

        # サブタブ2: 費用マスター
        self.master_tab = MasterTab(self.parent_tab_control, self.main_window)
        self.sub_tab_control.addTab(self.master_tab, "費用マスター")

        # サブタブ3: 発注チェック
        self.order_check_tab = OrderCheckTab()
        self.sub_tab_control.addTab(self.order_check_tab, "発注チェック")

        # サブタブ4: 発注・支払照合
        self.reconciliation_tab = OrderPaymentReconciliationTab()
        self.sub_tab_control.addTab(self.reconciliation_tab, "発注・支払照合")

        # レイアウト設定
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 余白なし
        layout.addWidget(self.sub_tab_control)
        self.setLayout(layout)
