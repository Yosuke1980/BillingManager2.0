"""発注先マスターウィジェット

発注先マスターの一覧表示・編集を行うウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QLabel, QLineEdit,
    QTextEdit, QDialogButtonBox, QFormLayout
)
from PyQt5.QtCore import Qt
from order_management.database_manager import OrderManagementDB


class SupplierMasterWidget(QWidget):
    """発注先マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_suppliers()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")

        self.add_button.clicked.connect(self.add_supplier)
        self.edit_button.clicked.connect(self.edit_supplier)
        self.delete_button.clicked.connect(self.delete_supplier)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "発注先名", "担当者", "メールアドレス", "電話番号", "備考"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_supplier)

        layout.addWidget(self.table)

    def load_suppliers(self):
        """発注先一覧を読み込み"""
        suppliers = self.db.get_suppliers()
        self.table.setRowCount(len(suppliers))

        for row, supplier in enumerate(suppliers):
            for col, value in enumerate(supplier):
                item = QTableWidgetItem(str(value) if value else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

        self.table.resizeColumnsToContents()

    def add_supplier(self):
        """新規発注先追加"""
        dialog = SupplierEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            supplier_data = dialog.get_data()
            try:
                self.db.save_supplier(supplier_data, is_new=True)
                self.load_suppliers()
                QMessageBox.information(self, "成功", "発注先を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")

    def edit_supplier(self):
        """発注先編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する発注先を選択してください")
            return

        supplier_id = int(self.table.item(current_row, 0).text())
        supplier = self.db.get_supplier_by_id(supplier_id)

        dialog = SupplierEditDialog(self, supplier)
        if dialog.exec_() == QDialog.Accepted:
            supplier_data = dialog.get_data()
            supplier_data['id'] = supplier_id
            try:
                self.db.save_supplier(supplier_data, is_new=False)
                self.load_suppliers()
                QMessageBox.information(self, "成功", "発注先を更新しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"更新に失敗しました: {e}")

    def delete_supplier(self):
        """発注先削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する発注先を選択してください")
            return

        supplier_id = int(self.table.item(current_row, 0).text())
        supplier_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"{supplier_name} を削除してもよろしいですか?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_supplier(supplier_id)
                self.load_suppliers()
                QMessageBox.information(self, "成功", "発注先を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {e}")


class SupplierEditDialog(QDialog):
    """発注先編集ダイアログ"""

    def __init__(self, parent=None, supplier_data=None):
        super().__init__(parent)
        self.supplier_data = supplier_data
        self.setWindowTitle("発注先編集" if supplier_data else "発注先追加")
        self.setMinimumWidth(500)
        self._setup_ui()

        if supplier_data:
            self._load_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.contact_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)

        form_layout.addRow("発注先名:", self.name_edit)
        form_layout.addRow("担当者:", self.contact_edit)
        form_layout.addRow("メールアドレス:", self.email_edit)
        form_layout.addRow("電話番号:", self.phone_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """データを読み込み"""
        if self.supplier_data:
            self.name_edit.setText(self.supplier_data[1] or "")
            self.contact_edit.setText(self.supplier_data[2] or "")
            self.email_edit.setText(self.supplier_data[3] or "")
            self.phone_edit.setText(self.supplier_data[4] or "")
            self.address_edit.setText(self.supplier_data[5] or "")
            self.notes_edit.setText(self.supplier_data[6] or "")

    def get_data(self) -> dict:
        """入力データを取得"""
        return {
            'name': self.name_edit.text(),
            'contact_person': self.contact_edit.text(),
            'email': self.email_edit.text(),
            'phone': self.phone_edit.text(),
            'address': self.address_edit.text(),
            'notes': self.notes_edit.toPlainText(),
        }
