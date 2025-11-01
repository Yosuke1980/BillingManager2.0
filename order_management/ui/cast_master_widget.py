"""出演者マスターウィジェット"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QMessageBox, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.cast_edit_dialog import CastEditDialog
from order_management.ui.ui_helpers import create_readonly_table_item


class CastMasterWidget(QWidget):
    """出演者マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_casts()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 上部レイアウト
        top_layout = QHBoxLayout()

        # 検索
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("出演者名、所属事務所で検索...")
        self.search_edit.textChanged.connect(self.load_casts)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_edit)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")

        self.add_button.clicked.connect(self.add_cast)
        self.edit_button.clicked.connect(self.edit_cast)
        self.delete_button.clicked.connect(self.delete_cast)

        top_layout.addWidget(self.add_button)
        top_layout.addWidget(self.edit_button)
        top_layout.addWidget(self.delete_button)

        layout.addLayout(top_layout)

        # 統計情報
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "出演者名", "所属事務所", "所属コード", "備考"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_cast)
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_casts(self):
        """出演者一覧を読み込み"""
        search_term = self.search_edit.text()
        casts = self.db.get_casts(search_term)

        self.table.setRowCount(len(casts))

        for row, cast in enumerate(casts):
            # cast: (id, name, partner_name, partner_code, notes)
            self.table.setItem(row, 0, create_readonly_table_item(str(cast[0])))
            self.table.setItem(row, 1, create_readonly_table_item(cast[1] or ""))
            self.table.setItem(row, 2, create_readonly_table_item(cast[2] or ""))
            self.table.setItem(row, 3, create_readonly_table_item(cast[3] or ""))
            self.table.setItem(row, 4, create_readonly_table_item(cast[4] or ""))

        self.table.resizeColumnsToContents()
        self.stats_label.setText(f"登録出演者数: {len(casts)}件")

    def add_cast(self):
        """新規出演者追加"""
        dialog = CastEditDialog(self)
        if dialog.exec_():
            self.load_casts()

    def edit_cast(self):
        """出演者編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する出演者を選択してください")
            return

        cast_id = int(self.table.item(current_row, 0).text())
        cast = self.db.get_cast_by_id(cast_id)

        if not cast:
            QMessageBox.warning(self, "エラー", "出演者情報の取得に失敗しました")
            return

        dialog = CastEditDialog(self, cast)
        if dialog.exec_():
            self.load_casts()

    def delete_cast(self):
        """出演者削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する出演者を選択してください")
            return

        cast_id = int(self.table.item(current_row, 0).text())
        cast_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"出演者「{cast_name}」を削除してもよろしいですか?\n※関連する番組が存在する場合は削除できません。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_cast(cast_id)
                self.load_casts()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{e}")
