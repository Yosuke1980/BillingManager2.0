"""案件一覧ウィジェット

案件の一覧表示と管理を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QSplitter, QLabel, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from order_management.database_manager import OrderManagementDB
from order_management.ui.project_edit_dialog import ProjectEditDialog
from order_management.ui.expense_edit_dialog import ExpenseEditDialog
from order_management.config import OrderConfig
from order_management.gmail_manager import GmailManager
from order_management.email_template import EmailTemplate
from order_management.order_number_generator import OrderNumberGenerator


class ProjectListWidget(QWidget):
    """案件一覧ウィジェット"""

    project_selected = pyqtSignal(int)  # 案件選択シグナル

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.current_project_id = None
        self._setup_ui()
        self.load_projects()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フィルター部分
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("タイプ:"))

        self.type_filter = QComboBox()
        self.type_filter.addItem("全て", "")
        self.type_filter.addItem("レギュラー", "レギュラー")
        self.type_filter.addItem("単発", "単発")
        self.type_filter.currentIndexChanged.connect(self.load_projects)

        filter_layout.addWidget(self.type_filter)
        filter_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規案件")
        self.edit_button = QPushButton("編集")
        self.duplicate_button = QPushButton("複製")
        self.delete_button = QPushButton("削除")
        self.add_expense_button = QPushButton("費用項目追加")

        self.add_button.clicked.connect(self.add_project)
        self.edit_button.clicked.connect(self.edit_project)
        self.duplicate_button.clicked.connect(self.duplicate_project)
        self.delete_button.clicked.connect(self.delete_project)
        self.add_expense_button.clicked.connect(self.add_expense)

        filter_layout.addWidget(self.add_button)
        filter_layout.addWidget(self.edit_button)
        filter_layout.addWidget(self.duplicate_button)
        filter_layout.addWidget(self.delete_button)
        filter_layout.addWidget(self.add_expense_button)

        layout.addLayout(filter_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "実施日", "案件名", "タイプ", "予算", "実績", "残予算"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self.edit_project)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        # ID列を非表示
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_projects(self):
        """案件一覧を読み込み"""
        project_type = self.type_filter.currentData()
        projects = self.db.get_projects(project_type=project_type)

        self.table.setRowCount(len(projects))

        for row, project in enumerate(projects):
            project_id = project[0]
            project_type_str = project[3] or ""

            # サマリー情報を取得
            summary = self.db.get_project_summary(project_id)

            # 日付表示を案件タイプに応じて変更
            if project_type_str == "レギュラー":
                # レギュラー案件の場合、詳細情報を取得して開始日〜終了日を表示
                detail = self.db.get_project_by_id(project_id)
                if detail:
                    start_date = detail[6] or ""
                    end_date = detail[7] or ""
                    if start_date and end_date:
                        date_display = f"{start_date} ～ {end_date}"
                    elif start_date:
                        date_display = start_date
                    else:
                        date_display = ""
                else:
                    date_display = ""
            else:
                # 単発案件の場合、実施日を表示
                date_display = project[2] or ""

            # テーブルに設定
            self.table.setItem(row, 0, QTableWidgetItem(str(project[0])))  # ID
            self.table.setItem(row, 1, QTableWidgetItem(date_display))  # 日付
            self.table.setItem(row, 2, QTableWidgetItem(project[1] or ""))  # 案件名
            self.table.setItem(row, 3, QTableWidgetItem(project_type_str))  # タイプ

            # 予算・実績・残予算
            budget_item = QTableWidgetItem(f"{summary['budget']:,.0f}")
            actual_item = QTableWidgetItem(f"{summary['actual']:,.0f}")
            remaining_item = QTableWidgetItem(f"{summary['remaining']:,.0f}")

            budget_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            actual_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            remaining_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # 予算超過時は赤字
            if summary['remaining'] < 0:
                remaining_item.setForeground(Qt.red)

            self.table.setItem(row, 4, budget_item)
            self.table.setItem(row, 5, actual_item)
            self.table.setItem(row, 6, remaining_item)

            # 行全体を読み取り専用に
            for col in range(7):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.table.resizeColumnsToContents()

    def on_selection_changed(self):
        """選択変更時の処理"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            project_id = int(self.table.item(current_row, 0).text())
            self.current_project_id = project_id
            self.project_selected.emit(project_id)

    def add_project(self):
        """新規案件追加"""
        dialog = ProjectEditDialog(self)
        if dialog.exec_():
            project_data = dialog.get_data()
            try:
                self.db.save_project(project_data, is_new=True)
                self.load_projects()
                QMessageBox.information(self, "成功", "案件を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")

    def edit_project(self):
        """案件編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する案件を選択してください")
            return

        project_id = int(self.table.item(current_row, 0).text())
        project = self.db.get_project_by_id(project_id)

        dialog = ProjectEditDialog(self, project)
        if dialog.exec_():
            project_data = dialog.get_data()
            project_data['id'] = project_id
            try:
                self.db.save_project(project_data, is_new=False)
                self.load_projects()
                QMessageBox.information(self, "成功", "案件を更新しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"更新に失敗しました: {e}")

    def delete_project(self):
        """案件削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する案件を選択してください")
            return

        project_id = int(self.table.item(current_row, 0).text())
        project_name = self.table.item(current_row, 2).text()

        reply = QMessageBox.question(
            self, "確認",
            f"{project_name} を削除してもよろしいですか?\n関連する費用項目もすべて削除されます。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_project(project_id)
                self.load_projects()
                self.project_selected.emit(0)  # 選択解除
                QMessageBox.information(self, "成功", "案件を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {e}")

    def duplicate_project(self):
        """案件を複製"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "複製する案件を選択してください")
            return

        project_id = int(self.table.item(current_row, 0).text())
        project_name = self.table.item(current_row, 2).text()

        reply = QMessageBox.question(
            self, "確認",
            f"{project_name} を複製してもよろしいですか?\n関連する費用項目もすべて複製されます。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                new_project_id = self.db.duplicate_project(project_id)
                self.load_projects()
                QMessageBox.information(self, "成功", f"案件を複製しました（新ID: {new_project_id}）")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"複製に失敗しました: {e}")

    def add_expense(self):
        """費用項目追加"""
        if not self.current_project_id:
            QMessageBox.warning(self, "警告", "先に案件を選択してください")
            return

        dialog = ExpenseEditDialog(self, self.current_project_id)
        if dialog.exec_():
            expense_data = dialog.get_data()
            try:
                self.db.save_expense_order(expense_data, is_new=True)
                self.load_projects()  # 実績を更新するため
                self.project_selected.emit(self.current_project_id)  # ツリービュー更新
                QMessageBox.information(self, "成功", "費用項目を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")
