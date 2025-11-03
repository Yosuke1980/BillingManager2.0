"""配布ステータス更新ダイアログ

PDF配布ステータスを更新します。
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QComboBox,
                             QPushButton, QDateEdit, QLineEdit, QHBoxLayout,
                             QMessageBox)
from PyQt5.QtCore import QDate

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button


class StatusUpdateDialog(QDialog):
    """配布ステータス更新ダイアログ"""

    def __init__(self, parent=None, contract_id=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.contract_id = contract_id

        self.setWindowTitle("配布ステータス更新")
        self.setMinimumWidth(400)

        self.init_ui()
        self.load_contract_data()

    def init_ui(self):
        """UIの初期化"""
        # ダイアログ全体の背景色を設定
        self.setStyleSheet("QDialog { background-color: white; }")

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # 発注ステータス
        self.order_status = QComboBox()
        self.order_status.addItems(["未", "済"])
        form_layout.addRow("発注ステータス:", self.order_status)

        # PDFステータス
        self.pdf_status = QComboBox()
        self.pdf_status.addItems(["未配布", "配布済", "受領確認済"])
        form_layout.addRow("PDFステータス:", self.pdf_status)

        # 配布日
        self.distributed_date = QDateEdit()
        self.distributed_date.setCalendarPopup(True)
        self.distributed_date.setDate(QDate.currentDate())
        form_layout.addRow("配布日:", self.distributed_date)

        # 確認者
        self.confirmed_by = QLineEdit()
        form_layout.addRow("確認者:", self.confirmed_by)

        layout.addLayout(form_layout)

        # ボタン
        button_layout = QHBoxLayout()

        update_btn = create_button("更新", self.update)
        button_layout.addWidget(update_btn)

        cancel_btn = create_button("キャンセル", self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_contract_data(self):
        """発注書データを読み込み"""
        contract = self.db.get_order_contract_by_id(self.contract_id)

        if contract:
            # contract[15]: order_status
            if contract[15]:
                self.order_status.setCurrentText(contract[15])

            # contract[8]: pdf_status
            if contract[8]:
                self.pdf_status.setCurrentText(contract[8])

            # contract[9]: pdf_distributed_date
            if contract[9]:
                self.distributed_date.setDate(QDate.fromString(contract[9], "yyyy-MM-dd"))

            # contract[10]: confirmed_by
            if contract[10]:
                self.confirmed_by.setText(contract[10])

    def update(self):
        """ステータスを更新"""
        try:
            # 発注ステータスとPDFステータスを両方更新
            contract = self.db.get_order_contract_by_id(self.contract_id)
            if contract:
                contract_data = {
                    'id': self.contract_id,
                    'program_id': contract[1],
                    'partner_id': contract[3],
                    'contract_start_date': contract[5],
                    'contract_end_date': contract[6],
                    'contract_period_type': contract[7],
                    'order_type': contract[14],
                    'order_status': self.order_status.currentText(),  # 更新
                    'pdf_status': self.pdf_status.currentText(),  # 更新
                    'pdf_file_path': contract[11],
                    'pdf_distributed_date': self.distributed_date.date().toString("yyyy-MM-dd"),  # 更新
                    'confirmed_by': self.confirmed_by.text(),  # 更新
                    'email_subject': contract[16] if len(contract) > 16 else '',
                    'email_body': contract[17] if len(contract) > 17 else '',
                    'email_sent_date': contract[18] if len(contract) > 18 else '',
                    'email_to': contract[19] if len(contract) > 19 else '',
                    'notes': contract[12]
                }
                self.db.save_order_contract(contract_data)
                QMessageBox.information(self, "成功", "ステータスを更新しました。")
                self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ステータスの更新に失敗しました:\n{str(e)}")
