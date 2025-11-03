"""制作会社選択ダイアログ"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QPushButton
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_list_item


class ProducerSelectDialog(QDialog):
    """制作会社選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()

        self.setWindowTitle("制作会社選択")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_partners()

    def _setup_ui(self):
        """UIセットアップ"""
        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._load_partners)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # リスト
        self.partner_list = QListWidget()
        self.partner_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.partner_list)

        # ボタン
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("選択")
        self.cancel_button = QPushButton("キャンセル")
        self.select_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _load_partners(self):
        """取引先を読み込み"""
        search_term = self.search_edit.text()
        partners = self.db.get_partners(search_term)

        self.partner_list.clear()
        for partner in partners:
            partner_id = partner[0]
            partner_name = partner[1]
            partner_code = partner[2] or ""

            display_text = partner_name
            if partner_code:
                display_text += f" ({partner_code})"

            item = create_list_item(display_text, {'id': partner_id, 'name': partner_name})
            self.partner_list.addItem(item)

    def get_selected_partners(self):
        """選択された取引先を取得"""
        selected_items = self.partner_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items]
