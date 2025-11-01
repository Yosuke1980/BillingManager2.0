"""発注書編集ダイアログ

発注書の登録・編集を行います。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel,
                             QDateEdit, QTextEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.program_edit_dialog import ProgramEditDialog
from order_management.ui.partner_master_widget import PartnerEditDialog


class OrderContractEditDialog(QDialog):
    """発注書編集ダイアログ"""

    def __init__(self, parent=None, contract_id=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.contract_id = contract_id
        self.pdf_file_path = ""
        self.pdf_dir = "order_pdfs"

        self.setWindowTitle("発注書編集" if contract_id else "新規発注書")
        self.setMinimumWidth(600)

        self.init_ui()

        if contract_id:
            self.load_contract_data()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # 番組選択（検索可能）
        program_layout = QHBoxLayout()
        self.program_combo = QComboBox()
        self.program_combo.setEditable(True)  # 編集可能に
        self.program_combo.setInsertPolicy(QComboBox.NoInsert)  # 入力しても追加しない
        self.program_combo.completer().setCompletionMode(self.program_combo.completer().PopupCompletion)
        self.program_combo.completer().setFilterMode(Qt.MatchContains)  # 部分一致
        self.load_programs()
        program_layout.addWidget(self.program_combo)

        add_program_btn = create_button("新規番組追加", self.add_new_program)
        program_layout.addWidget(add_program_btn)

        form_layout.addRow("番組名:", program_layout)

        # 取引先選択（検索可能）
        partner_layout = QHBoxLayout()
        self.partner_combo = QComboBox()
        self.partner_combo.setEditable(True)  # 編集可能に
        self.partner_combo.setInsertPolicy(QComboBox.NoInsert)  # 入力しても追加しない
        self.partner_combo.completer().setCompletionMode(self.partner_combo.completer().PopupCompletion)
        self.partner_combo.completer().setFilterMode(Qt.MatchContains)  # 部分一致
        self.load_partners()
        partner_layout.addWidget(self.partner_combo)

        add_partner_btn = create_button("新規取引先追加", self.add_new_partner)
        partner_layout.addWidget(add_partner_btn)

        form_layout.addRow("取引先名:", partner_layout)

        # 委託開始日
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.dateChanged.connect(self.on_start_date_changed)
        form_layout.addRow("委託開始日:", self.start_date)

        # 委託終了日
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addMonths(6))
        form_layout.addRow("委託終了日:", self.end_date)

        # 契約期間種別
        self.period_type = QComboBox()
        self.period_type.addItems(["3ヶ月", "半年", "1年"])
        self.period_type.setCurrentText("半年")
        self.period_type.currentTextChanged.connect(self.on_period_type_changed)
        form_layout.addRow("契約期間:", self.period_type)

        # PDFステータス
        self.pdf_status = QComboBox()
        self.pdf_status.addItems(["未配布", "配布済", "受領確認済"])
        form_layout.addRow("PDFステータス:", self.pdf_status)

        # PDFファイル
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("(未選択)")
        pdf_layout.addWidget(self.pdf_label)
        pdf_btn = create_button("ファイル選択", self.select_pdf)
        pdf_layout.addWidget(pdf_btn)
        form_layout.addRow("PDFファイル:", pdf_layout)

        # PDF配布日
        self.distributed_date = QDateEdit()
        self.distributed_date.setCalendarPopup(True)
        self.distributed_date.setDate(QDate.currentDate())
        form_layout.addRow("PDF配布日:", self.distributed_date)

        # 確認者
        self.confirmed_by = QLineEdit()
        form_layout.addRow("配布確認者:", self.confirmed_by)

        # 備考
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form_layout.addRow("備考:", self.notes)

        layout.addLayout(form_layout)

        # ボタン
        button_layout = QHBoxLayout()
        save_btn = create_button("保存", self.save)
        button_layout.addWidget(save_btn)

        cancel_btn = create_button("キャンセル", self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_programs(self):
        """番組一覧を読み込み"""
        programs = self.db.get_programs()
        self.program_dict = {}

        for program in programs:
            # program: (id, name, description, start_date, end_date, broadcast_time, broadcast_days, status)
            display_text = f"{program[1]} (ID: {program[0]})"
            self.program_combo.addItem(display_text)
            self.program_dict[display_text] = program[0]

    def load_partners(self):
        """取引先一覧を読み込み"""
        partners = self.db.get_partners()
        self.partner_dict = {}

        for partner in partners:
            # partner: (id, name, code, contact_person, email, phone, address, partner_type, notes)
            display_text = f"{partner[1]}"
            if partner[2]:  # code
                display_text += f" ({partner[2]})"
            self.partner_combo.addItem(display_text)
            self.partner_dict[display_text] = partner[0]

    def load_contract_data(self):
        """発注書データを読み込み"""
        contract = self.db.get_order_contract_by_id(self.contract_id)

        if contract:
            # contract: (id, program_id, program_name, partner_id, partner_name,
            #            contract_start_date, contract_end_date, contract_period_type,
            #            pdf_status, pdf_distributed_date, confirmed_by,
            #            pdf_file_path, notes, created_at, updated_at)

            # 番組選択
            for i in range(self.program_combo.count()):
                if self.program_dict[self.program_combo.itemText(i)] == contract[1]:
                    self.program_combo.setCurrentIndex(i)
                    break

            # 取引先選択
            for i in range(self.partner_combo.count()):
                if self.partner_dict[self.partner_combo.itemText(i)] == contract[3]:
                    self.partner_combo.setCurrentIndex(i)
                    break

            # 委託開始日
            if contract[5]:
                self.start_date.setDate(QDate.fromString(contract[5], "yyyy-MM-dd"))

            # 委託終了日
            if contract[6]:
                self.end_date.setDate(QDate.fromString(contract[6], "yyyy-MM-dd"))

            # 契約期間種別
            if contract[7]:
                self.period_type.setCurrentText(contract[7])

            # PDFステータス
            if contract[8]:
                self.pdf_status.setCurrentText(contract[8])

            # PDF配布日
            if contract[9]:
                self.distributed_date.setDate(QDate.fromString(contract[9], "yyyy-MM-dd"))

            # 確認者
            if contract[10]:
                self.confirmed_by.setText(contract[10])

            # PDFファイルパス
            if contract[11]:
                self.pdf_file_path = contract[11]
                self.pdf_label.setText(os.path.basename(self.pdf_file_path))

            # 備考
            if contract[12]:
                self.notes.setPlainText(contract[12])

    def on_start_date_changed(self, date):
        """開始日変更時に終了日を自動設定"""
        period_type = self.period_type.currentText()
        months = {"3ヶ月": 3, "半年": 6, "1年": 12}

        if period_type in months:
            new_end_date = date.addMonths(months[period_type])
            self.end_date.setDate(new_end_date)

    def on_period_type_changed(self, period_type):
        """契約期間種別変更時に終了日を自動設定"""
        months = {"3ヶ月": 3, "半年": 6, "1年": 12}

        if period_type in months:
            start_date = self.start_date.date()
            new_end_date = start_date.addMonths(months[period_type])
            self.end_date.setDate(new_end_date)

    def select_pdf(self):
        """PDFファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "PDFファイルを選択",
            "",
            "PDFファイル (*.pdf);;すべてのファイル (*.*)"
        )

        if file_path:
            self.pdf_file_path = file_path
            self.pdf_label.setText(os.path.basename(file_path))

    def save(self):
        """保存"""
        # バリデーション
        if self.program_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "番組を選択してください。")
            return

        if self.partner_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "取引先を選択してください。")
            return

        # PDFファイルを保存
        saved_pdf_path = ""
        if self.pdf_file_path and os.path.exists(self.pdf_file_path):
            # ファイル名を生成
            program_text = self.program_combo.currentText().split(" (ID:")[0]
            partner_text = self.partner_combo.currentText().split(" (")[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"発注書_{partner_text}_{program_text}_{timestamp}.pdf"

            saved_pdf_path = os.path.join(self.pdf_dir, filename)

            try:
                # ディレクトリが存在しない場合は作成
                if not os.path.exists(self.pdf_dir):
                    os.makedirs(self.pdf_dir)

                shutil.copy2(self.pdf_file_path, saved_pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"PDFファイルの保存に失敗しました:\n{str(e)}")
                return

        # 発注書データを作成
        program_key = self.program_combo.currentText()
        partner_key = self.partner_combo.currentText()

        contract_data = {
            'program_id': self.program_dict[program_key],
            'partner_id': self.partner_dict[partner_key],
            'contract_start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'contract_end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'contract_period_type': self.period_type.currentText(),
            'pdf_status': self.pdf_status.currentText(),
            'pdf_file_path': saved_pdf_path if saved_pdf_path else (
                self.pdf_file_path if self.contract_id else ""
            ),
            'pdf_distributed_date': self.distributed_date.date().toString("yyyy-MM-dd"),
            'confirmed_by': self.confirmed_by.text(),
            'notes': self.notes.toPlainText()
        }

        if self.contract_id:
            contract_data['id'] = self.contract_id

        try:
            self.db.save_order_contract(contract_data)
            QMessageBox.information(self, "成功", "発注書を保存しました。")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"発注書の保存に失敗しました:\n{str(e)}")

    def add_new_program(self):
        """新規番組を追加"""
        dialog = ProgramEditDialog(self)
        if dialog.exec_():
            # 番組一覧を再読み込み
            current_count = self.program_combo.count()
            self.program_combo.clear()
            self.load_programs()

            # 新しく追加された番組を自動選択
            if self.program_combo.count() > current_count:
                self.program_combo.setCurrentIndex(self.program_combo.count() - 1)

    def add_new_partner(self):
        """新規取引先を追加"""
        dialog = PartnerEditDialog(self)
        if dialog.exec_():
            # 取引先一覧を再読み込み
            current_count = self.partner_combo.count()
            self.partner_combo.clear()
            self.load_partners()

            # 新しく追加された取引先を自動選択
            if self.partner_combo.count() > current_count:
                self.partner_combo.setCurrentIndex(self.partner_combo.count() - 1)
