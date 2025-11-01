"""発注書編集ダイアログ

発注書の登録・編集を行います。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QLabel,
                             QDateEdit, QTextEdit, QFileDialog, QMessageBox, QWidget)
from PyQt5.QtCore import QDate, Qt
from datetime import datetime, timedelta
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.program_edit_dialog import ProgramEditDialog
from order_management.ui.partner_master_widget import PartnerEditDialog
from partner_manager import PartnerManager


class OrderContractEditDialog(QDialog):
    """発注書編集ダイアログ"""

    def __init__(self, parent=None, contract_id=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.pm = PartnerManager()
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

        # 発注種別選択
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["契約書", "発注書", "メール発注"])
        self.order_type_combo.setCurrentText("発注書")
        self.order_type_combo.currentTextChanged.connect(self.on_order_type_changed)
        form_layout.addRow("発注種別:", self.order_type_combo)

        # 発注ステータス
        self.order_status_combo = QComboBox()
        self.order_status_combo.addItems(["未", "済"])
        form_layout.addRow("発注ステータス:", self.order_status_combo)

        # 番組選択（検索可能）
        program_layout = QHBoxLayout()
        self.program_combo = QComboBox()
        self.program_combo.setEditable(True)  # 編集可能に
        self.program_combo.setInsertPolicy(QComboBox.NoInsert)  # 入力しても追加しない
        self.program_combo.setMinimumWidth(300)  # 最小幅を設定
        self.program_combo.completer().setCompletionMode(self.program_combo.completer().PopupCompletion)
        self.program_combo.completer().setFilterMode(Qt.MatchContains)  # 部分一致
        self.load_programs()
        program_layout.addWidget(self.program_combo, 1)  # ストレッチファクター1で伸縮可能に

        add_program_btn = create_button("新規番組追加", self.add_new_program)
        add_program_btn.setMinimumWidth(120)  # ボタンの最小幅を設定
        program_layout.addWidget(add_program_btn, 0)  # ストレッチファクター0で固定サイズ

        form_layout.addRow("番組名:", program_layout)

        # 取引先選択（検索可能）
        partner_layout = QHBoxLayout()
        self.partner_combo = QComboBox()
        self.partner_combo.setEditable(True)  # 編集可能に
        self.partner_combo.setInsertPolicy(QComboBox.NoInsert)  # 入力しても追加しない
        self.partner_combo.setMinimumWidth(300)  # 最小幅を設定
        self.partner_combo.completer().setCompletionMode(self.partner_combo.completer().PopupCompletion)
        self.partner_combo.completer().setFilterMode(Qt.MatchContains)  # 部分一致
        self.load_partners()
        partner_layout.addWidget(self.partner_combo, 1)  # ストレッチファクター1で伸縮可能に

        add_partner_btn = create_button("新規取引先追加", self.add_new_partner)
        add_partner_btn.setMinimumWidth(140)  # ボタンの最小幅を設定
        partner_layout.addWidget(add_partner_btn, 0)  # ストレッチファクター0で固定サイズ

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

        # === レギュラー番組契約条件 ===
        # 支払タイプ
        self.payment_type = QComboBox()
        self.payment_type.addItems(["月額固定", "回数ベース"])
        self.payment_type.setCurrentText("月額固定")
        self.payment_type.currentTextChanged.connect(self.on_payment_type_changed)
        form_layout.addRow("支払タイプ:", self.payment_type)

        # 単価（回数ベースの場合のみ表示）
        self.unit_price_label = QLabel("単価（円/回）:")
        self.unit_price = QLineEdit()
        self.unit_price.setPlaceholderText("例: 50000")
        form_layout.addRow(self.unit_price_label, self.unit_price)

        # 支払タイミング
        self.payment_timing = QComboBox()
        self.payment_timing.addItems(["翌月末払い", "当月末払い"])
        self.payment_timing.setCurrentText("翌月末払い")
        form_layout.addRow("支払タイミング:", self.payment_timing)

        # === PDF関連フィールド（契約書・発注書用） ===
        # PDFステータス
        self.pdf_status = QComboBox()
        self.pdf_status.addItems(["未配布", "配布済", "受領確認済"])
        self.pdf_status_row = form_layout.rowCount()
        form_layout.addRow("PDFステータス:", self.pdf_status)

        # PDFファイル
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("(未選択)")
        pdf_layout.addWidget(self.pdf_label)
        pdf_btn = create_button("ファイル選択", self.select_pdf)
        pdf_layout.addWidget(pdf_btn)
        self.pdf_widget = QWidget()
        self.pdf_widget.setLayout(pdf_layout)
        self.pdf_file_row = form_layout.rowCount()
        form_layout.addRow("PDFファイル:", self.pdf_widget)

        # PDF配布日
        self.distributed_date = QDateEdit()
        self.distributed_date.setCalendarPopup(True)
        self.distributed_date.setDate(QDate.currentDate())
        self.distributed_date_row = form_layout.rowCount()
        form_layout.addRow("PDF配布日:", self.distributed_date)

        # 確認者
        self.confirmed_by = QLineEdit()
        self.confirmed_by_row = form_layout.rowCount()
        form_layout.addRow("配布確認者:", self.confirmed_by)

        # === メール関連フィールド（メール発注用） ===
        # メール件名
        self.email_subject = QLineEdit()
        self.email_subject.setPlaceholderText("例: 2025年度上期 番組制作委託のお願い")
        self.email_subject_row = form_layout.rowCount()
        form_layout.addRow("メール件名:", self.email_subject)

        # メール送信先
        self.email_to = QLineEdit()
        self.email_to.setPlaceholderText("例: partner@example.com")
        self.email_to_row = form_layout.rowCount()
        form_layout.addRow("送信先アドレス:", self.email_to)

        # メール送信日
        self.email_sent_date = QDateEdit()
        self.email_sent_date.setCalendarPopup(True)
        self.email_sent_date.setDate(QDate.currentDate())
        self.email_sent_date_row = form_layout.rowCount()
        form_layout.addRow("送信日:", self.email_sent_date)

        # メール本文
        self.email_body = QTextEdit()
        self.email_body.setMaximumHeight(150)
        self.email_body.setPlaceholderText("メール本文を入力...")
        self.email_body_row = form_layout.rowCount()
        form_layout.addRow("メール本文:", self.email_body)

        # 備考
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form_layout.addRow("備考:", self.notes)

        # フォームレイアウトを保存（後で行を表示/非表示にするため）
        self.form_layout = form_layout

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

        # 初期表示：発注書モードでメールフィールドを非表示
        self.on_order_type_changed("発注書")
        # 初期表示：月額固定モードで単価フィールドを非表示
        self.on_payment_type_changed("月額固定")

    def on_payment_type_changed(self, payment_type):
        """支払タイプが変更されたときに単価フィールドの表示を切り替える"""
        if payment_type == "回数ベース":
            # 単価フィールドを表示
            self.unit_price_label.setVisible(True)
            self.unit_price.setVisible(True)
        else:
            # 単価フィールドを非表示
            self.unit_price_label.setVisible(False)
            self.unit_price.setVisible(False)

    def on_order_type_changed(self, order_type):
        """発注種別が変更されたときにフィールドの表示を切り替える"""
        if order_type == "メール発注":
            # PDFフィールドを非表示、メールフィールドを表示
            self.form_layout.setRowVisible(self.pdf_status_row, False)
            self.form_layout.setRowVisible(self.pdf_file_row, False)
            self.form_layout.setRowVisible(self.distributed_date_row, False)
            self.form_layout.setRowVisible(self.confirmed_by_row, False)

            self.form_layout.setRowVisible(self.email_subject_row, True)
            self.form_layout.setRowVisible(self.email_to_row, True)
            self.form_layout.setRowVisible(self.email_sent_date_row, True)
            self.form_layout.setRowVisible(self.email_body_row, True)
        else:
            # 契約書 or 発注書: PDFフィールドを表示、メールフィールドを非表示
            self.form_layout.setRowVisible(self.pdf_status_row, True)
            self.form_layout.setRowVisible(self.pdf_file_row, True)
            self.form_layout.setRowVisible(self.distributed_date_row, True)
            self.form_layout.setRowVisible(self.confirmed_by_row, True)

            self.form_layout.setRowVisible(self.email_subject_row, False)
            self.form_layout.setRowVisible(self.email_to_row, False)
            self.form_layout.setRowVisible(self.email_sent_date_row, False)
            self.form_layout.setRowVisible(self.email_body_row, False)

    def load_programs(self):
        """番組一覧を読み込み"""
        programs = self.db.get_programs()
        self.program_dict = {}

        for program in programs:
            # program: (id, name, description, start_date, end_date, broadcast_time, broadcast_days, status)
            display_text = f"{program[1]} (ID: {program[0]})"
            self.program_combo.addItem(display_text, program[0])  # IDをデータとして保存
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
            self.partner_combo.addItem(display_text, partner[0])  # IDをデータとして保存
            self.partner_dict[display_text] = partner[0]

    def load_contract_data(self):
        """発注書データを読み込み"""
        contract = self.db.get_order_contract_by_id(self.contract_id)

        if contract:
            # contract: (id, program_id, program_name, partner_id, partner_name,
            #            contract_start_date, contract_end_date, contract_period_type,
            #            pdf_status, pdf_distributed_date, confirmed_by,
            #            pdf_file_path, notes, created_at, updated_at,
            #            order_type, order_status,
            #            email_subject, email_body, email_sent_date, email_to)

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

            # 発注種別（インデックス14）
            if contract[14]:
                self.order_type_combo.setCurrentText(contract[14])
                self.on_order_type_changed(contract[14])  # フィールド表示を更新

            # 発注ステータス（インデックス15）
            if contract[15]:
                self.order_status_combo.setCurrentText(contract[15])

            # メール件名（インデックス16）
            if contract[16]:
                self.email_subject.setText(contract[16])

            # メール本文（インデックス17）
            if contract[17]:
                self.email_body.setPlainText(contract[17])

            # メール送信日（インデックス18）
            if contract[18]:
                self.email_sent_date.setDate(QDate.fromString(contract[18], "yyyy-MM-dd"))

            # メール送信先（インデックス19）
            if contract[19]:
                self.email_to.setText(contract[19])

            # 支払タイプ（インデックス20）
            if contract[20]:
                self.payment_type.setCurrentText(contract[20])
                self.on_payment_type_changed(contract[20])  # フィールド表示を更新

            # 単価（インデックス21）
            if contract[21] is not None:
                self.unit_price.setText(str(int(contract[21])))

            # 支払タイミング（インデックス22）
            if contract[22]:
                self.payment_timing.setCurrentText(contract[22])

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
        # currentData()でIDを取得（より安全）
        program_id = self.program_combo.currentData()
        partner_id = self.partner_combo.currentData()

        # IDが取得できない場合は辞書から取得（フォールバック）
        if program_id is None:
            program_key = self.program_combo.currentText()
            program_id = self.program_dict.get(program_key)
            if program_id is None:
                QMessageBox.warning(self, "警告", "番組が正しく選択されていません。")
                return

        if partner_id is None:
            partner_key = self.partner_combo.currentText()
            partner_id = self.partner_dict.get(partner_key)
            if partner_id is None:
                QMessageBox.warning(self, "警告", "取引先が正しく選択されていません。")
                return

        contract_data = {
            'program_id': program_id,
            'partner_id': partner_id,
            'contract_start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'contract_end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'contract_period_type': self.period_type.currentText(),
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
            # レギュラー番組契約条件
            'payment_type': self.payment_type.currentText(),
            'unit_price': float(self.unit_price.text()) if self.unit_price.text() else None,
            'payment_timing': self.payment_timing.currentText()
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
        if dialog.exec_() == QDialog.Accepted:
            partner_data = dialog.get_data()
            try:
                # 重複チェック
                if self.pm.check_duplicate_name(partner_data['name']):
                    QMessageBox.warning(self, "警告", "同じ名前の取引先が既に存在します")
                    return

                # コードが空欄の場合は自動生成
                if not partner_data['code']:
                    import time
                    partner_data['code'] = f"P{int(time.time())}"  # タイムスタンプベースのユニークコード

                if partner_data['code'] and self.pm.check_duplicate_code(partner_data['code']):
                    QMessageBox.warning(self, "警告", "同じコードの取引先が既に存在します")
                    return

                # 取引先を保存
                self.pm.save_partner(partner_data, is_new=True)

                # 取引先一覧を再読み込み
                current_count = self.partner_combo.count()
                self.partner_combo.clear()
                self.load_partners()

                # 新しく追加された取引先を自動選択
                if self.partner_combo.count() > current_count:
                    self.partner_combo.setCurrentIndex(self.partner_combo.count() - 1)

                QMessageBox.information(self, "成功", "取引先を追加しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")
