"""統合取引先マスターウィジェット

統合取引先マスター(partners)の一覧表示・編集を行うウィジェットです。
Phase 6で実装。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QDialog, QLabel, QLineEdit,
    QTextEdit, QDialogButtonBox, QFormLayout, QComboBox
)
from PyQt5.QtCore import Qt
from partner_manager import PartnerManager
from order_management.models import PARTNER_TYPES


class PartnerMasterWidget(QWidget):
    """統合取引先マスター管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pm = PartnerManager()
        self._setup_ui()
        self.load_partners()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フィルターとボタン
        top_layout = QHBoxLayout()

        # 取引先区分フィルター
        filter_label = QLabel("取引先区分:")
        self.type_filter = QComboBox()
        self.type_filter.addItem("全て", "")
        for ptype in PARTNER_TYPES:
            self.type_filter.addItem(ptype, ptype)
        self.type_filter.currentIndexChanged.connect(self.load_partners)

        top_layout.addWidget(filter_label)
        top_layout.addWidget(self.type_filter)
        top_layout.addStretch()

        # ボタン
        self.add_button = QPushButton("新規追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")

        self.add_button.clicked.connect(self.add_partner)
        self.edit_button.clicked.connect(self.edit_partner)
        self.delete_button.clicked.connect(self.delete_partner)

        top_layout.addWidget(self.add_button)
        top_layout.addWidget(self.edit_button)
        top_layout.addWidget(self.delete_button)

        layout.addLayout(top_layout)

        # 統計情報
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "取引先名", "コード", "担当者", "メールアドレス",
            "電話番号", "取引先区分", "備考"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_partner)

        # ID列を非表示
        self.table.setColumnHidden(0, True)

        layout.addWidget(self.table)

    def load_partners(self):
        """取引先一覧を読み込み"""
        partner_type = self.type_filter.currentData()
        partners = self.pm.get_partners(partner_type=partner_type)

        self.table.setRowCount(len(partners))

        for row, partner in enumerate(partners):
            # partner: (id, name, code, contact_person, email, phone, address, partner_type, notes)
            for col in range(8):
                if col == 6:  # addressは表示しない
                    continue
                display_col = col if col < 6 else col - 1
                value = partner[col] if col < len(partner) else ""
                item = QTableWidgetItem(str(value) if value else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, display_col, item)

        self.table.resizeColumnsToContents()

        # 統計情報を更新
        self._update_stats()

    def _update_stats(self):
        """統計情報を更新"""
        counts = self.pm.get_partner_count_by_type()
        stats_text = f"合計: {counts['合計']}件 " \
                    f"(発注先: {counts['発注先']}件, " \
                    f"支払先: {counts['支払先']}件, " \
                    f"両方: {counts['両方']}件)"
        self.stats_label.setText(stats_text)

    def add_partner(self):
        """新規取引先追加"""
        dialog = PartnerEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            partner_data = dialog.get_data()
            try:
                # 重複チェック
                if self.pm.check_duplicate_name(partner_data['name']):
                    QMessageBox.warning(self, "警告", "同じ名前の取引先が既に存在します")
                    return

                if partner_data['code'] and self.pm.check_duplicate_code(partner_data['code']):
                    QMessageBox.warning(self, "警告", "同じコードの取引先が既に存在します")
                    return

                self.pm.save_partner(partner_data, is_new=True)
                self.load_partners()
                QMessageBox.information(self, "成功", "取引先を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")

    def edit_partner(self):
        """取引先編集"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "編集する取引先を選択してください")
            return

        partner_id = int(self.table.item(current_row, 0).text())
        partner = self.pm.get_partner_by_id(partner_id)

        dialog = PartnerEditDialog(self, partner)
        if dialog.exec_() == QDialog.Accepted:
            partner_data = dialog.get_data()
            partner_data['id'] = partner_id
            try:
                # 重複チェック（自分自身を除外）
                if self.pm.check_duplicate_name(partner_data['name'], exclude_id=partner_id):
                    QMessageBox.warning(self, "警告", "同じ名前の取引先が既に存在します")
                    return

                if partner_data['code'] and self.pm.check_duplicate_code(partner_data['code'], exclude_id=partner_id):
                    QMessageBox.warning(self, "警告", "同じコードの取引先が既に存在します")
                    return

                self.pm.save_partner(partner_data, is_new=False)
                self.load_partners()
                QMessageBox.information(self, "成功", "取引先を更新しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"更新に失敗しました: {e}")

    def delete_partner(self):
        """取引先削除"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "削除する取引先を選択してください")
            return

        partner_id = int(self.table.item(current_row, 0).text())
        partner_name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"{partner_name} を削除してもよろしいですか?\n"
            "関連する費用項目がある場合は削除できません。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.pm.delete_partner(partner_id)
                self.load_partners()
                QMessageBox.information(self, "成功", "取引先を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {e}")


class PartnerEditDialog(QDialog):
    """取引先編集ダイアログ"""

    def __init__(self, parent=None, partner_data=None):
        super().__init__(parent)
        self.partner_data = partner_data
        self.setWindowTitle("取引先編集" if partner_data else "取引先追加")
        self.setMinimumWidth(500)
        self._setup_ui()

        if partner_data:
            self._load_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: 株式会社サンプル")

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("例: SUP001（省略可）")

        self.contact_edit = QLineEdit()
        self.contact_edit.setPlaceholderText("例: 山田太郎")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("例: example@company.com")

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("例: 03-1234-5678")

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("例: 東京都渋谷区...")

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("備考があれば入力...")

        form_layout.addRow("取引先名 *:", self.name_edit)
        form_layout.addRow("取引先コード:", self.code_edit)
        form_layout.addRow("担当者:", self.contact_edit)
        form_layout.addRow("メールアドレス:", self.email_edit)
        form_layout.addRow("電話番号:", self.phone_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("備考:", self.notes_edit)

        layout.addLayout(form_layout)

        # 注意書き
        note_label = QLabel("* は必須項目です")
        note_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(note_label)

        # ボタン
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """データを読み込み"""
        if self.partner_data:
            # partner_data: (id, name, code, contact_person, email, phone, address, partner_type, notes)
            self.name_edit.setText(self.partner_data[1] or "")
            self.code_edit.setText(self.partner_data[2] or "")
            self.contact_edit.setText(self.partner_data[3] or "")
            self.email_edit.setText(self.partner_data[4] or "")
            self.phone_edit.setText(self.partner_data[5] or "")
            self.address_edit.setText(self.partner_data[6] or "")
            self.notes_edit.setText(self.partner_data[8] or "")

    def validate_and_accept(self):
        """バリデーション後に受け入れ"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "取引先名を入力してください")
            return

        self.accept()

    def get_data(self) -> dict:
        """入力データを取得"""
        return {
            'name': self.name_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'partner_type': '両方',  # 常に「両方」に設定
            'contact_person': self.contact_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
        }
