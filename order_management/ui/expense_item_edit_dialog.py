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
from order_management.ui.ui_helpers import create_button


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

        # 新規契約作成ボタン
        new_contract_btn = create_button("➕ 新規契約", self.create_new_contract)
        new_contract_btn.setMinimumWidth(110)
        contract_layout.addWidget(new_contract_btn)

        form_layout.addRow("契約:", contract_layout)

        # 番組選択
        self.production_combo = QComboBox()
        self.production_combo.addItem("(未選択)", None)
        self.refresh_productions()
        self.production_combo.currentIndexChanged.connect(self._on_production_changed)
        production_label = QLabel("<b>番組・イベント *:</b>")
        form_layout.addRow(production_label, self.production_combo)

        # コーナー選択
        self.corner_combo = QComboBox()
        self.corner_combo.addItem("(なし)", None)
        form_layout.addRow("コーナー:", self.corner_combo)

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
        amount_layout = QHBoxLayout()
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setSuffix(" 円")
        self.amount_spin.setGroupSeparatorShown(True)
        amount_layout.addWidget(self.amount_spin)

        self.amount_pending_checkbox = QCheckBox("金額未定")
        self.amount_pending_checkbox.stateChanged.connect(self._on_amount_pending_changed)
        amount_layout.addWidget(self.amount_pending_checkbox)

        form_layout.addRow("金額:", amount_layout)

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
        """契約リストを更新（契約機能は削除されました）"""
        # 契約機能は削除されたため、空の実装
        pass

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

    def refresh_corners(self, production_id=None):
        """コーナーリストを更新"""
        # 既存のアイテムをクリア
        self.corner_combo.clear()
        self.corner_combo.addItem("(なし)", None)

        if production_id:
            corners = self.db.get_corners_by_production(production_id)
            for corner in corners:
                corner_id = corner[0]
                corner_name = corner[1]
                self.corner_combo.addItem(corner_name, corner_id)

    def _on_contract_selected(self, index):
        """契約が選択されたときの処理（契約機能は削除されました）"""
        # 契約機能は削除されたため、空の実装
        pass

    def _load_data(self):
        """データを読み込み（新スキーマ対応）"""
        if not self.expense_data:
            return

        # データ構造（新スキーマ）:
        # (id, production_id, partner_id, cast_id, item_name, work_type, amount,
        #  implementation_date, order_number, order_date, status, invoice_received_date,
        #  expected_payment_date, expected_payment_amount, payment_scheduled_date,
        #  actual_payment_date, payment_status, ..., notes, created_at, updated_at,
        #  template_id, generation_month)

        # 番組を設定
        production_id = self.expense_data[1]
        if production_id:
            # この番組がコーナーかどうかチェック
            conn = self.db._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT parent_production_id FROM productions WHERE id = ?", (production_id,))
                result = cursor.fetchone()
                parent_id = result[0] if result else None

                if parent_id:
                    # コーナーの場合、親番組を選択してコーナー一覧を表示
                    idx = self.production_combo.findData(parent_id)
                    if idx >= 0:
                        self.production_combo.setCurrentIndex(idx)
                    self.refresh_corners(parent_id)
                    # コーナーを選択
                    idx = self.corner_combo.findData(production_id)
                    if idx >= 0:
                        self.corner_combo.setCurrentIndex(idx)
                else:
                    # 通常の番組の場合
                    idx = self.production_combo.findData(production_id)
                    if idx >= 0:
                        self.production_combo.setCurrentIndex(idx)
                    self.refresh_corners(production_id)
            finally:
                conn.close()

        # 取引先を設定
        partner_id = self.expense_data[2]
        if partner_id:
            idx = self.partner_combo.findData(partner_id)
            if idx >= 0:
                self.partner_combo.setCurrentIndex(idx)

        # 項目名
        self.item_name_edit.setText(self.expense_data[4] or "")

        # 業務種別
        work_type = self.expense_data[5] or "制作"
        idx = self.work_type_combo.findText(work_type)
        if idx >= 0:
            self.work_type_combo.setCurrentIndex(idx)

        # 金額
        self.amount_spin.setValue(self.expense_data[6] or 0)

        # 実施日
        impl_date_str = self.expense_data[7]
        if impl_date_str:
            try:
                year, month, day = impl_date_str.split('-')
                self.impl_date_edit.setDate(QDate(int(year), int(month), int(day)))
            except:
                pass

        # 支払予定日
        payment_date_str = self.expense_data[12]
        if payment_date_str:
            try:
                year, month, day = payment_date_str.split('-')
                self.payment_date_edit.setDate(QDate(int(year), int(month), int(day)))
            except:
                pass

        # ステータス
        status = self.expense_data[10] or "発注予定"
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

        # 支払ステータス
        payment_status = self.expense_data[16] or "未払い"
        idx = self.payment_status_combo.findText(payment_status)
        if idx >= 0:
            self.payment_status_combo.setCurrentIndex(idx)

        # 備考
        notes = self.expense_data[32] or ""
        self.notes_edit.setPlainText(notes)

        # 金額未定フラグ
        amount_pending = self.expense_data[37] if len(self.expense_data) > 37 else 0
        self.amount_pending_checkbox.setChecked(amount_pending == 1)
        if amount_pending == 1:
            self.amount_spin.setEnabled(False)

    def _on_amount_pending_changed(self, state):
        """金額未定チェックボックス変更時の処理"""
        is_pending = (state == 2)  # Qt.Checked
        self.amount_spin.setEnabled(not is_pending)
        if is_pending:
            self.amount_spin.setValue(0)

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.item_name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "項目名を入力してください")
            return

        # 金額未定の場合はバリデーションスキップ
        if not self.amount_pending_checkbox.isChecked():
            if self.amount_spin.value() <= 0:
                QMessageBox.warning(self, "入力エラー", "金額を入力してください")
                return

        self.accept()

    def get_expense_data(self):
        """入力されたデータを取得"""
        is_pending = self.amount_pending_checkbox.isChecked()
        data = {
            'production_id': self.production_combo.currentData(),
            'partner_id': self.partner_combo.currentData(),
            'corner_id': self.corner_combo.currentData(),
            'item_name': self.item_name_edit.text().strip(),
            'work_type': self.work_type_combo.currentText(),
            'amount': 0 if is_pending else self.amount_spin.value(),
            'amount_pending': 1 if is_pending else 0,
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
        """番組変更時の確認ダイアログとコーナー一覧の更新"""
        new_production_id = self.production_combo.currentData()

        # コーナー一覧を更新
        self.refresh_corners(new_production_id)

        # 新規作成時または元の番組がない場合はチェック不要
        if not self.original_production_id:
            return

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
                        # コーナー一覧を元に戻す
                        self.refresh_corners(self.original_production_id)
                        break

    def create_new_contract(self):
        """新規契約作成（契約機能は削除されました）"""
        # 契約機能は削除されたため、空の実装
        pass

    # 契約機能は削除されました（将来的に費用テンプレート機能に置き換え予定）
