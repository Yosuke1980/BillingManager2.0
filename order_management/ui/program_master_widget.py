"""番組マスターウィジェット

番組マスターの一覧表示・編集を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB
from order_management.ui.program_edit_dialog import ProgramEditDialog


class ProgramMasterWidget(QWidget):
    """番組マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_programs()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フィルターとボタン
        top_layout = QHBoxLayout()

        # 検索
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("番組名で検索...")
        self.search_edit.textChanged.connect(self.load_programs)
        top_layout.addWidget(search_label)
        top_layout.addWidget(self.search_edit)

        # ステータスフィルター
        status_label = QLabel("ステータス:")
        self.status_filter = QComboBox()
        self.status_filter.addItem("全て", "")
        self.status_filter.addItem("放送中", "放送中")
        self.status_filter.addItem("終了", "終了")
        self.status_filter.currentIndexChanged.connect(self.load_programs)
        top_layout.addWidget(status_label)
        top_layout.addWidget(self.status_filter)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")

        self.add_button.clicked.connect(self.add_program)
        self.edit_button.clicked.connect(self.edit_program)
        self.delete_button.clicked.connect(self.delete_program)

        top_layout.addWidget(self.add_button)
        top_layout.addWidget(self.edit_button)
        top_layout.addWidget(self.delete_button)

        layout.addLayout(top_layout)

        # 統計情報
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "番組名", "開始日", "終了日", "放送時間", "放送曜日", "ステータス"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_program)

        # ID列を非表示
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_programs(self):
        """番組一覧を読み込み"""
        search_term = self.search_edit.text()
        status = self.status_filter.currentData()
        programs = self.db.get_programs(search_term, status)

        self.table.setRowCount(len(programs))

        for row, program in enumerate(programs):
            # program: (id, name, description, start_date, end_date,
            #           broadcast_time, broadcast_days, status)
            program_id = program[0]
            name = program[1] or ""
            start_date = program[3] or ""
            end_date = program[4] or ""
            broadcast_time = program[5] or ""
            broadcast_days = program[6] or ""
            status_text = program[7] or ""

            self.table.setItem(row, 0, self._create_readonly_item(str(program_id)))
            self.table.setItem(row, 1, self._create_readonly_item(name))
            self.table.setItem(row, 2, self._create_readonly_item(start_date))
            self.table.setItem(row, 3, self._create_readonly_item(end_date))
            self.table.setItem(row, 4, self._create_readonly_item(broadcast_time))
            self.table.setItem(row, 5, self._create_readonly_item(broadcast_days))
            self.table.setItem(row, 6, self._create_readonly_item(status_text))

        self.table.resizeColumnsToContents()

        # 統計情報を更新
        self._update_stats()

    def _create_readonly_item(self, text):
        """読み取り専用のテーブルアイテムを作成"""
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def _update_stats(self):
        """統計情報を更新"""
        total = self.table.rowCount()

        # ステータス別集計
        broadcasting = 0
        ended = 0
        for row in range(total):
            status_item = self.table.item(row, 6)
            if status_item:
                status = status_item.text()
                if status == "放送中":
                    broadcasting += 1
                elif status == "終了":
                    ended += 1

        stats_text = f"登録番組数: {total}件 (放送中: {broadcasting}件 / 終了: {ended}件)"
        self.stats_label.setText(stats_text)

    def add_program(self):
        """新規番組追加"""
        dialog = ProgramEditDialog(self)
        if dialog.exec_():
            self.load_programs()

    def edit_program(self):
        """番組編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する番組を選択してください")
            return

        program_id = int(self.table.item(current_row, 0).text())
        program = self.db.get_program_by_id(program_id)

        if not program:
            QMessageBox.warning(self, "エラー", "番組情報の取得に失敗しました")
            return

        dialog = ProgramEditDialog(self, program)
        if dialog.exec_():
            self.load_programs()

    def delete_program(self):
        """番組削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する番組を選択してください")
            return

        program_id = int(self.table.item(current_row, 0).text())
        program_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"番組「{program_name}」を削除してもよろしいですか?\n\n"
            f"※関連する出演者・制作会社情報も削除されます。\n"
            f"※関連する案件が存在する場合は削除できません。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_program(program_id)
                self.load_programs()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{e}")
