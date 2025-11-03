"""単発発注編集ダイアログ

単発（1回限り）の発注の登録・編集を行います。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel,
                             QDateEdit, QTextEdit, QFileDialog, QMessageBox,
                             QRadioButton, QButtonGroup, QWidget)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.program_edit_dialog import ProgramEditDialog
from order_management.ui.partner_master_widget import PartnerEditDialog
from partner_manager import PartnerManager


class SpotContractEditDialog(QDialog):
    """単発発注編集ダイアログ"""

    def __init__(self, parent=None, contract_id=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.pm = PartnerManager()
        self.contract_id = contract_id
        self.pdf_file_path = ""
        self.pdf_dir = "order_pdfs"

        self.setWindowTitle("単発発注編集" if contract_id else "新規単発発注")
        self.setMinimumWidth(600)

        self.init_ui()

        if contract_id:
            self.load_contract_data()

    def init_ui(self):
        """UIの初期化"""
        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # 発注種別選択
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["契約書", "発注書", "メール発注"])
        self.order_type_combo.setCurrentText("発注書")
        self.order_type_combo.currentTextChanged.connect(self.on_order_type_changed)
        form_layout.addRow("発注種別:", self.order_type_combo)

        # 発注ステータス
        self.order_status_combo = QComboBox()
        self.order_status_combo.addItems(["未完了", "完了"])
        form_layout.addRow("発注ステータス:", self.order_status_combo)

        # === 案件名の選択方式 ===
        project_name_group = QWidget()
        project_name_layout = QVBoxLayout()
        project_name_layout.setContentsMargins(0, 0, 0, 0)

        # ラジオボタングループ
        self.project_name_type_group = QButtonGroup()

        # 番組から選択
        self.rb_program = QRadioButton("番組から選択:")
        self.rb_program.setChecked(True)
        self.project_name_type_group.addButton(self.rb_program, 0)
        self.rb_program.toggled.connect(self.on_project_name_type_changed)

        program_layout = QHBoxLayout()
        program_layout.setContentsMargins(20, 0, 0, 0)
        self.program_combo = QComboBox()
        self.program_combo.setEditable(True)
        self.program_combo.setInsertPolicy(QComboBox.NoInsert)
        self.program_combo.setMinimumWidth(300)
        self.program_combo.completer().setCompletionMode(self.program_combo.completer().PopupCompletion)
        self.program_combo.completer().setFilterMode(Qt.MatchContains)
        self.load_programs()
        program_layout.addWidget(self.program_combo, 1)

        add_program_btn = create_button("新規番組追加", self.add_new_program)
        add_program_btn.setMinimumWidth(120)
        program_layout.addWidget(add_program_btn, 0)

        # 自由入力
        self.rb_custom = QRadioButton("自由入力:")
        self.project_name_type_group.addButton(self.rb_custom, 1)
        self.rb_custom.toggled.connect(self.on_project_name_type_changed)

        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(20, 0, 0, 0)
        self.custom_project_name = QLineEdit()
        self.custom_project_name.setPlaceholderText("例: 2024年10月特番")
        self.custom_project_name.setEnabled(False)
        custom_layout.addWidget(self.custom_project_name)

        project_name_layout.addWidget(self.rb_program)
        project_name_layout.addLayout(program_layout)
        project_name_layout.addWidget(self.rb_custom)
        project_name_layout.addLayout(custom_layout)

        project_name_group.setLayout(project_name_layout)
        form_layout.addRow("案件名:", project_name_group)

        # 費用項目（自由入力）
        self.item_name = QLineEdit()
        self.item_name.setPlaceholderText("例: 山田太郎出演料、制作費")
        form_layout.addRow("費用項目:", self.item_name)

        # 取引先選択
        partner_layout = QHBoxLayout()
        self.partner_combo = QComboBox()
        self.partner_combo.setEditable(True)
        self.partner_combo.setInsertPolicy(QComboBox.NoInsert)
        self.partner_combo.setMinimumWidth(300)
        self.partner_combo.completer().setCompletionMode(self.partner_combo.completer().PopupCompletion)
        self.partner_combo.completer().setFilterMode(Qt.MatchContains)
        self.load_partners()
        partner_layout.addWidget(self.partner_combo, 1)

        add_partner_btn = create_button("新規取引先追加", self.add_new_partner)
        add_partner_btn.setMinimumWidth(140)
        partner_layout.addWidget(add_partner_btn, 0)

        form_layout.addRow("取引先名:", partner_layout)

        # 実施日
        self.implementation_date = QDateEdit()
        self.implementation_date.setCalendarPopup(True)
        self.implementation_date.setDate(QDate.currentDate())
        form_layout.addRow("実施日:", self.implementation_date)

        # 金額
        self.amount = QLineEdit()
        self.amount.setPlaceholderText("例: 50000")
        form_layout.addRow("金額（円）:", self.amount)

        # === PDF関連フィールド（契約書・発注書用） ===
        self.pdf_status_label = QLabel("PDFステータス:")
        self.pdf_status = QComboBox()
        self.pdf_status.addItems(["未配布", "配布済", "受領確認済"])
        form_layout.addRow(self.pdf_status_label, self.pdf_status)

        # PDFファイル
        self.pdf_file_label = QLabel("PDFファイル:")
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("(未選択)")
        pdf_layout.addWidget(self.pdf_label)
        pdf_btn = create_button("ファイル選択", self.select_pdf)
        pdf_layout.addWidget(pdf_btn)
        self.pdf_widget = QWidget()
        self.pdf_widget.setLayout(pdf_layout)
        form_layout.addRow(self.pdf_file_label, self.pdf_widget)

        # PDF配布日
        self.distributed_date_label = QLabel("PDF配布日:")
        self.distributed_date = QDateEdit()
        self.distributed_date.setCalendarPopup(True)
        self.distributed_date.setDate(QDate.currentDate())
        form_layout.addRow(self.distributed_date_label, self.distributed_date)

        # 確認者
        self.confirmed_by_label = QLabel("確認者:")
        self.confirmed_by = QLineEdit()
        form_layout.addRow(self.confirmed_by_label, self.confirmed_by)

        # === メール発注関連フィールド ===
        self.email_subject_label = QLabel("メール件名:")
        self.email_subject = QLineEdit()
        form_layout.addRow(self.email_subject_label, self.email_subject)

        self.email_body_label = QLabel("メール本文:")
        self.email_body = QTextEdit()
        self.email_body.setMaximumHeight(100)
        form_layout.addRow(self.email_body_label, self.email_body)

        self.email_sent_date_label = QLabel("メール送信日:")
        self.email_sent_date = QDateEdit()
        self.email_sent_date.setCalendarPopup(True)
        self.email_sent_date.setDate(QDate.currentDate())
        form_layout.addRow(self.email_sent_date_label, self.email_sent_date)

        self.email_to_label = QLabel("メール送信先:")
        self.email_to = QLineEdit()
        form_layout.addRow(self.email_to_label, self.email_to)

        # 備考
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form_layout.addRow("備考:", self.notes)

        layout.addLayout(form_layout)

        # 発注種別に応じてフィールドの表示/非表示を初期化
        self.on_order_type_changed(self.order_type_combo.currentText())

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = create_button("保存", self.save)
        save_btn.setMinimumWidth(100)
        button_layout.addWidget(save_btn)

        cancel_btn = create_button("キャンセル", self.reject)
        cancel_btn.setMinimumWidth(100)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # ラベルへの参照を保存（Qt5互換性のため）
        self.pdf_widgets = [self.pdf_status_label, self.pdf_status,
                           self.pdf_file_label, self.pdf_widget,
                           self.distributed_date_label, self.distributed_date,
                           self.confirmed_by_label, self.confirmed_by]

        self.email_widgets = [self.email_subject_label, self.email_subject,
                             self.email_body_label, self.email_body,
                             self.email_sent_date_label, self.email_sent_date,
                             self.email_to_label, self.email_to]

    def on_project_name_type_changed(self):
        """案件名の選択方式が変更されたときの処理"""
        is_program = self.rb_program.isChecked()
        self.program_combo.setEnabled(is_program)
        self.custom_project_name.setEnabled(not is_program)

    def on_order_type_changed(self, order_type):
        """発注種別が変更されたときの処理"""
        # PDF関連フィールドの表示/非表示
        show_pdf = order_type in ["契約書", "発注書"]
        for widget in self.pdf_widgets:
            widget.setVisible(show_pdf)

        # メール関連フィールドの表示/非表示
        show_email = order_type == "メール発注"
        for widget in self.email_widgets:
            widget.setVisible(show_email)

    def load_programs(self):
        """番組一覧を読み込み"""
        programs = self.db.get_programs()
        self.program_dict = {}

        for program in programs:
            display_text = f"{program[1]} (ID: {program[0]})"
            self.program_combo.addItem(display_text, program[0])
            self.program_dict[display_text] = program[0]

    def load_partners(self):
        """取引先一覧を読み込み"""
        partners = self.db.get_partners()
        self.partner_dict = {}

        for partner in partners:
            display_text = f"{partner[1]}"
            if partner[2]:  # code
                display_text += f" ({partner[2]})"
            self.partner_combo.addItem(display_text, partner[0])
            self.partner_dict[display_text] = partner[0]

    def load_contract_data(self):
        """発注書データを読み込み"""
        contract = self.db.get_order_contract_by_id(self.contract_id)
        if not contract:
            QMessageBox.warning(self, "エラー", "発注書データが見つかりません。")
            return

        # インデックス対応表:
        # 0:id, 1:program_id, 2:program_name, 3:partner_id, 4:partner_name,
        # 5:contract_start_date, 6:contract_end_date, 7:contract_period_type,
        # 8:pdf_status, 9:pdf_distributed_date, 10:confirmed_by,
        # 11:pdf_file_path, 12:notes, 13:created_at, 14:updated_at,
        # 15:order_type, 16:order_status, 17:email_subject, 18:email_body,
        # 19:email_sent_date, 20:email_to, 21:payment_type, 22:unit_price,
        # 23:payment_timing, 24:project_id, 25:project_name, 26:item_name,
        # 27:contract_type, 28:project_name_type, 29:custom_project_name,
        # 30:implementation_date, 31:spot_amount

        # 案件名の設定
        project_name_type = contract[28] if len(contract) > 28 else 'program'
        if project_name_type == 'custom':
            self.rb_custom.setChecked(True)
            custom_name = contract[29] if len(contract) > 29 else ""
            self.custom_project_name.setText(custom_name or "")
        else:
            self.rb_program.setChecked(True)
            program_id = contract[1]
            if program_id:
                for i in range(self.program_combo.count()):
                    if self.program_combo.itemData(i) == program_id:
                        self.program_combo.setCurrentIndex(i)
                        break

        # 費用項目
        self.item_name.setText(contract[26] or "")

        # 取引先
        partner_id = contract[3]
        if partner_id:
            for i in range(self.partner_combo.count()):
                if self.partner_combo.itemData(i) == partner_id:
                    self.partner_combo.setCurrentIndex(i)
                    break

        # 実施日
        if contract[30]:
            self.implementation_date.setDate(QDate.fromString(contract[30], "yyyy-MM-dd"))

        # 金額
        if contract[31]:
            self.amount.setText(str(contract[31]))

        # 発注種別
        order_type = contract[15] or "発注書"
        index = self.order_type_combo.findText(order_type)
        if index >= 0:
            self.order_type_combo.setCurrentIndex(index)

        # 発注ステータス
        order_status = contract[16] or "未完了"
        index = self.order_status_combo.findText(order_status)
        if index >= 0:
            self.order_status_combo.setCurrentIndex(index)

        # PDFステータス
        pdf_status = contract[8] or "未配布"
        index = self.pdf_status.findText(pdf_status)
        if index >= 0:
            self.pdf_status.setCurrentIndex(index)

        # PDFファイルパス
        if contract[11]:
            self.pdf_file_path = contract[11]
            self.pdf_label.setText(os.path.basename(contract[11]))

        # PDF配布日
        if contract[9]:
            self.distributed_date.setDate(QDate.fromString(contract[9], "yyyy-MM-dd"))

        # 確認者
        self.confirmed_by.setText(contract[10] or "")

        # メール件名
        self.email_subject.setText(contract[17] or "")

        # メール本文
        self.email_body.setPlainText(contract[18] or "")

        # メール送信日
        if contract[19]:
            self.email_sent_date.setDate(QDate.fromString(contract[19], "yyyy-MM-dd"))

        # メール送信先
        self.email_to.setText(contract[20] or "")

        # 備考
        self.notes.setPlainText(contract[12] or "")

    def select_pdf(self):
        """PDFファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "PDFファイルを選択", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.pdf_file_path = file_path
            self.pdf_label.setText(os.path.basename(file_path))

    def save(self):
        """保存"""
        # バリデーション
        if self.rb_program.isChecked():
            if self.program_combo.currentIndex() < 0:
                QMessageBox.warning(self, "警告", "番組を選択してください。")
                return
        else:
            if not self.custom_project_name.text().strip():
                QMessageBox.warning(self, "警告", "案件名を入力してください。")
                return

        if not self.item_name.text().strip():
            QMessageBox.warning(self, "警告", "費用項目を入力してください。")
            return

        if self.partner_combo.currentIndex() < 0:
            QMessageBox.warning(self, "警告", "取引先を選択してください。")
            return

        if not self.amount.text().strip():
            QMessageBox.warning(self, "警告", "金額を入力してください。")
            return

        # PDFファイルを保存
        saved_pdf_path = ""
        if self.pdf_file_path and os.path.exists(self.pdf_file_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"単発発注_{timestamp}.pdf"
            saved_pdf_path = os.path.join(self.pdf_dir, filename)

            try:
                if not os.path.exists(self.pdf_dir):
                    os.makedirs(self.pdf_dir)
                shutil.copy2(self.pdf_file_path, saved_pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"PDFファイルの保存に失敗しました:\n{str(e)}")
                return

        # データを作成
        partner_id = self.partner_combo.currentData()
        if partner_id is None:
            partner_key = self.partner_combo.currentText()
            partner_id = self.partner_dict.get(partner_key)
            if partner_id is None:
                QMessageBox.warning(self, "警告", "取引先が正しく選択されていません。")
                return

        contract_data = {
            'contract_type': 'spot',
            'partner_id': partner_id,
            'item_name': self.item_name.text().strip(),
            'implementation_date': self.implementation_date.date().toString("yyyy-MM-dd"),
            'spot_amount': float(self.amount.text()),
            'order_type': self.order_type_combo.currentText(),
            'order_status': self.order_status_combo.currentText(),
            'pdf_status': self.pdf_status.currentText(),
            'pdf_file_path': saved_pdf_path if saved_pdf_path else (
                self.pdf_file_path if self.contract_id else ""
            ),
            'pdf_distributed_date': self.distributed_date.date().toString("yyyy-MM-dd"),
            'confirmed_by': self.confirmed_by.text(),
            'email_subject': self.email_subject.text(),
            'email_body': self.email_body.toPlainText(),
            'email_sent_date': self.email_sent_date.date().toString("yyyy-MM-dd"),
            'email_to': self.email_to.text(),
            'notes': self.notes.toPlainText(),
        }

        # 案件名の設定
        if self.rb_program.isChecked():
            program_id = self.program_combo.currentData()
            if program_id is None:
                program_key = self.program_combo.currentText()
                program_id = self.program_dict.get(program_key)
            contract_data['program_id'] = program_id
            contract_data['project_name_type'] = 'program'
        else:
            contract_data['project_name_type'] = 'custom'
            contract_data['custom_project_name'] = self.custom_project_name.text().strip()

        if self.contract_id:
            contract_data['id'] = self.contract_id

        try:
            self.db.save_order_contract(contract_data)
            QMessageBox.information(self, "成功", "単発発注を保存しました。")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"単発発注の保存に失敗しました:\n{str(e)}")

    def add_new_program(self):
        """新規番組を追加"""
        dialog = ProgramEditDialog(self)
        if dialog.exec_():
            current_count = self.program_combo.count()
            self.program_combo.clear()
            self.load_programs()
            if self.program_combo.count() > current_count:
                self.program_combo.setCurrentIndex(self.program_combo.count() - 1)

    def add_new_partner(self):
        """新規取引先を追加"""
        dialog = PartnerEditDialog(self)
        if dialog.exec_():
            current_count = self.partner_combo.count()
            self.partner_combo.clear()
            self.load_partners()
            if self.partner_combo.count() > current_count:
                self.partner_combo.setCurrentIndex(self.partner_combo.count() - 1)
