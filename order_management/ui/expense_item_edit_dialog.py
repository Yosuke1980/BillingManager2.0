"""費用項目編集ダイアログ（新スキーマ対応）

expense_items テーブルの費用項目を作成・編集します。
契約との紐付け機能を含みます。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QLabel, QPushButton, QHBoxLayout, QCheckBox
)
from PyQt5.QtCore import QDate
from order_management.database_manager import OrderManagementDB
from order_management.ui.custom_date_edit import ImprovedDateEdit


class ExpenseItemEditDialog(QDialog):
    """費用項目編集ダイアログ（新スキーマ対応）"""

    def __init__(self, parent=None, expense_id=None):
        super().__init__(parent)
        self.expense_id = expense_id
        self.db = OrderManagementDB()
        self.expense_data = None
        self.original_production_id = None  # 元の番組IDを記録

        # expense_idが指定されている場合はデータを取得
        if expense_id:
            self.expense_data = self.db.get_expense_item_by_id(expense_id)
            if self.expense_data and len(self.expense_data) > 2:
                self.original_production_id = self.expense_data[2]  # production_id

        self.setWindowTitle("費用項目編集" if expense_id else "費用項目追加")
        self.setMinimumWidth(600)
        self._setup_ui()

        if self.expense_data:
            self._load_data()

    def _setup_ui(self):
        """UIセットアップ"""
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # 契約選択（オプション）
        contract_layout = QHBoxLayout()
        self.contract_combo = QComboBox()
        self.contract_combo.addItem("(契約なし)", None)
        self.refresh_contracts()
        self.contract_combo.currentIndexChanged.connect(self._on_contract_selected)
        contract_layout.addWidget(self.contract_combo)

        self.link_contract_checkbox = QCheckBox("契約から自動入力")
        self.link_contract_checkbox.setChecked(True)
        contract_layout.addWidget(self.link_contract_checkbox)

        form_layout.addRow("契約:", contract_layout)

        # 番組選択
        self.production_combo = QComboBox()
        self.production_combo.addItem("(未選択)", None)
        self.refresh_productions()
        self.production_combo.currentIndexChanged.connect(self._on_production_changed)
        production_label = QLabel("<b>番組・イベント *:</b>")
        form_layout.addRow(production_label, self.production_combo)

        # 取引先選択
        self.partner_combo = QComboBox()
        self.partner_combo.addItem("(未選択)", None)
        self.refresh_partners()
        form_layout.addRow("取引先:", self.partner_combo)

        # 項目名
        self.item_name_edit = QLineEdit()
        self.item_name_edit.setPlaceholderText("例: 出演料、制作費")
        form_layout.addRow("項目名:", self.item_name_edit)

        # 業務種別
        self.work_type_combo = QComboBox()
        self.work_type_combo.addItems(["制作", "出演"])
        form_layout.addRow("業務種別:", self.work_type_combo)

        # 金額
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setSuffix(" 円")
        self.amount_spin.setGroupSeparatorShown(True)
        form_layout.addRow("金額:", self.amount_spin)

        # 実施日
        self.impl_date_edit = ImprovedDateEdit()
        self.impl_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("実施日:", self.impl_date_edit)

        # 支払予定日
        self.payment_date_edit = ImprovedDateEdit()
        self.payment_date_edit.setDate(QDate.currentDate().addMonths(1))
        form_layout.addRow("支払予定日:", self.payment_date_edit)

        # ステータス
        self.status_combo = QComboBox()
        self.status_combo.addItems(["発注予定", "発注済", "請求書受領", "支払完了"])
        form_layout.addRow("状態:", self.status_combo)

        # 支払ステータス
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["未払い", "支払済"])
        form_layout.addRow("支払状態:", self.payment_status_combo)

        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("備考やメモを入力")
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def refresh_contracts(self):
        """契約リストを更新"""
        contracts = self.db.get_active_contracts()
        for contract in contracts:
            (contract_id, production_name, partner_name, item_name,
             unit_price, spot_amount, start_date, end_date) = contract

            # 表示テキスト作成
            amount = spot_amount if spot_amount else unit_price
            display_text = f"{production_name or '(番組なし)'} - {partner_name or '(取引先なし)'} - {item_name or ''}"
            if amount:
                display_text += f" (¥{int(amount):,})"

            self.contract_combo.addItem(display_text, contract_id)

    def refresh_productions(self):
        """番組リストを更新"""
        productions = self.db.get_productions()
        for production in productions:
            self.production_combo.addItem(production[1], production[0])

    def refresh_partners(self):
        """取引先リストを更新"""
        partners = self.db.get_partners()
        for partner in partners:
            partner_id = partner[0]
            partner_name = partner[1]
            partner_code = partner[2] or ""

            display_text = f"{partner_name}"
            if partner_code:
                display_text += f" ({partner_code})"

            self.partner_combo.addItem(display_text, partner_id)

    def _on_contract_selected(self, index):
        """契約が選択されたときの処理"""
        if not self.link_contract_checkbox.isChecked():
            return

        contract_id = self.contract_combo.currentData()
        if not contract_id:
            return

        # 契約情報を取得
        conn = self.db._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT production_id, partner_id, item_name, unit_price, spot_amount, work_type
                FROM contracts
                WHERE id = ?
            """, (contract_id,))
            contract = cursor.fetchone()

            if contract:
                production_id, partner_id, item_name, unit_price, spot_amount, work_type = contract

                # 番組を設定
                if production_id:
                    idx = self.production_combo.findData(production_id)
                    if idx >= 0:
                        self.production_combo.setCurrentIndex(idx)

                # 取引先を設定
                if partner_id:
                    idx = self.partner_combo.findData(partner_id)
                    if idx >= 0:
                        self.partner_combo.setCurrentIndex(idx)

                # 項目名を設定
                if item_name:
                    self.item_name_edit.setText(item_name)

                # 業務種別を設定
                if work_type:
                    idx = self.work_type_combo.findText(work_type)
                    if idx >= 0:
                        self.work_type_combo.setCurrentIndex(idx)

                # 金額を設定
                amount = spot_amount if spot_amount else unit_price
                if amount:
                    self.amount_spin.setValue(amount)
        finally:
            conn.close()

    def _load_data(self):
        """データを読み込み"""
        if not self.expense_data:
            return

        # データ構造: (id, contract_id, production_id, partner_id, item_name,
        #            amount, implementation_date, order_number, order_date,
        #            status, invoice_received_date, expected_payment_date, ...)

        # 契約を設定
        contract_id = self.expense_data[1]
        if contract_id:
            idx = self.contract_combo.findData(contract_id)
            if idx >= 0:
                self.contract_combo.setCurrentIndex(idx)

        # 番組を設定
        production_id = self.expense_data[2]
        if production_id:
            idx = self.production_combo.findData(production_id)
            if idx >= 0:
                self.production_combo.setCurrentIndex(idx)

        # 取引先を設定
        partner_id = self.expense_data[3]
        if partner_id:
            idx = self.partner_combo.findData(partner_id)
            if idx >= 0:
                self.partner_combo.setCurrentIndex(idx)

        # 項目名
        self.item_name_edit.setText(self.expense_data[4] or "")

        # 金額
        self.amount_spin.setValue(self.expense_data[5] or 0)

        # 実施日
        impl_date_str = self.expense_data[6]
        if impl_date_str:
            try:
                year, month, day = impl_date_str.split('-')
                self.impl_date_edit.setDate(QDate(int(year), int(month), int(day)))
            except:
                pass

        # 支払予定日
        payment_date_str = self.expense_data[11]
        if payment_date_str:
            try:
                year, month, day = payment_date_str.split('-')
                self.payment_date_edit.setDate(QDate(int(year), int(month), int(day)))
            except:
                pass

        # ステータス
        status = self.expense_data[9] or "発注予定"
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        # 支払ステータス
        payment_status = self.expense_data[15] or "未払い"
        idx = self.payment_status_combo.findText(payment_status)
        if idx >= 0:
            self.payment_status_combo.setCurrentIndex(idx)

        # 備考
        notes = self.expense_data[23] or ""
        self.notes_edit.setPlainText(notes)

        # 業務種別
        work_type = self.expense_data[26] if len(self.expense_data) > 26 else "制作"
        idx = self.work_type_combo.findText(work_type or "制作")
        if idx >= 0:
            self.work_type_combo.setCurrentIndex(idx)

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.item_name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return

        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "入力エラー", "金額を入力してください")
            return

        self.accept()

    def get_expense_data(self):
        """入力されたデータを取得"""
        data = {
            'contract_id': self.contract_combo.currentData(),
            'production_id': self.production_combo.currentData(),
            'partner_id': self.partner_combo.currentData(),
            'item_name': self.item_name_edit.text().strip(),
            'work_type': self.work_type_combo.currentText(),
            'amount': self.amount_spin.value(),
            'implementation_date': self.impl_date_edit.date().toString('yyyy-MM-dd'),
            'expected_payment_date': self.payment_date_edit.date().toString('yyyy-MM-dd'),
            'status': self.status_combo.currentText(),
            'payment_status': self.payment_status_combo.currentText(),
            'notes': self.notes_edit.toPlainText().strip()
        }

        if self.expense_id:
            data['id'] = self.expense_id

        return data

    def _on_production_changed(self, index):
        """番組変更時の確認ダイアログ"""
        # 新規作成時または元の番組がない場合はチェック不要
        if not self.original_production_id:
            return

        new_production_id = self.production_combo.currentData()

        # 番組が変更されている場合のみ確認
        if new_production_id and new_production_id != self.original_production_id:
            # 元の番組名を取得
            original_production_name = None
            for i in range(self.production_combo.count()):
                if self.production_combo.itemData(i) == self.original_production_id:
                    original_production_name = self.production_combo.itemText(i)
                    break

            new_production_name = self.production_combo.currentText()

            reply = QMessageBox.question(
                self, "番組変更の確認",
                f"番組を変更しますか？\n\n"
                f"変更前: {original_production_name}\n"
                f"変更後: {new_production_name}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                # 元の番組に戻す
                for i in range(self.production_combo.count()):
                    if self.production_combo.itemData(i) == self.original_production_id:
                        self.production_combo.blockSignals(True)  # シグナルを一時的にブロック
                        self.production_combo.setCurrentIndex(i)
                        self.production_combo.blockSignals(False)
                        break
