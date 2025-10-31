"""費用項目編集ダイアログ

費用項目の作成・編集を行うダイアログです。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QDoubleSpinBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import QDate
from order_management.models import STATUS_LIST
from order_management.database_manager import OrderManagementDB


class ExpenseEditDialog(QDialog):
    """費用項目編集ダイアログ"""

    def __init__(self, parent=None, project_id=None, expense_data=None):
        super().__init__(parent)
        self.project_id = project_id
        self.expense_data = expense_data
        self.db = OrderManagementDB()

        self.setWindowTitle("費用項目編集" if expense_data else "費用項目追加")
        self.setMinimumWidth(600)
        self._setup_ui()

        if expense_data:
            self._load_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 項目名
        self.item_name_edit = QLineEdit()
        self.item_name_edit.setPlaceholderText("例: 伊藤出演料")

        # 金額
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setSuffix(" 円")
        self.amount_spin.setGroupSeparatorShown(True)

        # 発注先選択
        supplier_layout = QHBoxLayout()
        self.supplier_combo = QComboBox()
        self.refresh_suppliers()
        supplier_layout.addWidget(self.supplier_combo)

        # 発注先追加ボタン（将来の拡張用）
        # add_supplier_btn = QPushButton("+")
        # add_supplier_btn.setMaximumWidth(30)
        # supplier_layout.addWidget(add_supplier_btn)

        # 担当者
        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("例: 田中太郎")

        # ステータス
        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUS_LIST)

        # 実施日
        self.impl_date_edit = QDateEdit()
        self.impl_date_edit.setCalendarPopup(True)
        self.impl_date_edit.setDate(QDate.currentDate())
        self.impl_date_edit.setDisplayFormat("yyyy-MM-dd")

        # 支払予定日
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate().addMonths(1))
        self.payment_date_edit.setDisplayFormat("yyyy-MM-dd")

        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("備考やメモを入力")

        form_layout.addRow("項目名:", self.item_name_edit)
        form_layout.addRow("金額:", self.amount_spin)
        form_layout.addRow("発注先:", supplier_layout)
        form_layout.addRow("担当者:", self.contact_edit)
        form_layout.addRow("ステータス:", self.status_combo)
        form_layout.addRow("実施日:", self.impl_date_edit)
        form_layout.addRow("支払予定日:", self.payment_date_edit)
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def refresh_suppliers(self):
        """取引先リストを更新（統合取引先マスタから取得）"""
        self.supplier_combo.clear()
        self.supplier_combo.addItem("(未選択)", None)

        # partnersテーブルから全取引先を取得
        partners = self.db.get_partners()
        for partner in partners:
            partner_id = partner[0]
            partner_name = partner[1]
            partner_code = partner[2] or ""
            contact = partner[3] or ""

            # 表示テキスト: "取引先名 (コード) - 担当者"
            display_text = f"{partner_name}"
            if partner_code:
                display_text += f" ({partner_code})"
            if contact:
                display_text += f" - {contact}"

            self.supplier_combo.addItem(display_text, partner_id)

    def _load_data(self):
        """データを読み込み"""
        if self.expense_data:
            self.item_name_edit.setText(self.expense_data[2] or "")
            self.amount_spin.setValue(self.expense_data[3] or 0)

            # 発注先を設定
            supplier_id = self.expense_data[4]
            if supplier_id:
                index = self.supplier_combo.findData(supplier_id)
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)

            self.contact_edit.setText(self.expense_data[5] or "")

            # ステータスを設定
            status = self.expense_data[6]
            index = self.status_combo.findText(status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)

            # 実施日を設定
            impl_date_str = self.expense_data[8]
            if impl_date_str:
                try:
                    year, month, day = impl_date_str.split('-')
                    self.impl_date_edit.setDate(QDate(int(year), int(month), int(day)))
                except:
                    pass

            # 支払予定日を設定
            payment_date_str = self.expense_data[11]
            if payment_date_str:
                try:
                    year, month, day = payment_date_str.split('-')
                    self.payment_date_edit.setDate(QDate(int(year), int(month), int(day)))
                except:
                    pass

            # 備考
            self.notes_edit.setPlainText(self.expense_data[16] or "")

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.item_name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return

        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "入力エラー", "金額を入力してください")
            return

        self.accept()

    def get_data(self) -> dict:
        """入力データを取得"""
        supplier_id = self.supplier_combo.currentData()

        return {
            'project_id': self.project_id,
            'item_name': self.item_name_edit.text().strip(),
            'amount': self.amount_spin.value(),
            'supplier_id': supplier_id,
            'contact_person': self.contact_edit.text().strip(),
            'status': self.status_combo.currentText(),
            'implementation_date': self.impl_date_edit.date().toString("yyyy-MM-dd"),
            'payment_scheduled_date': self.payment_date_edit.date().toString("yyyy-MM-dd"),
            'notes': self.notes_edit.toPlainText(),
        }
