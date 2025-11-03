"""発注書管理ウィジェット

レギュラー番組の発注書管理機能を提供します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QMessageBox, QFileDialog, QHeaderView, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime, timedelta
import os
import shutil

from order_management.database_manager import OrderManagementDB
from order_management.ui.unified_order_dialog import UnifiedOrderDialog
from order_management.ui.ui_helpers import create_button


class OrderContractWidget(QWidget):
    """発注書管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.pdf_dir = "order_pdfs"  # PDFファイル保存ディレクトリ

        # PDFディレクトリ作成
        if not os.path.exists(self.pdf_dir):
            os.makedirs(self.pdf_dir)

        self.init_ui()
        self.load_contracts()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # フィルタエリア
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("検索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("番組名、取引先名で検索")
        self.search_input.textChanged.connect(self.load_contracts)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("発注種別:"))
        self.order_type_filter = QComboBox()
        self.order_type_filter.addItems(["すべて", "契約書", "発注書", "メール発注"])
        self.order_type_filter.currentTextChanged.connect(self.load_contracts)
        filter_layout.addWidget(self.order_type_filter)

        filter_layout.addWidget(QLabel("発注ステータス:"))
        self.order_status_filter = QComboBox()
        self.order_status_filter.addItems(["すべて", "未", "済"])
        self.order_status_filter.currentTextChanged.connect(self.load_contracts)
        filter_layout.addWidget(self.order_status_filter)

        filter_layout.addWidget(QLabel("PDFステータス:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["すべて", "未配布", "配布済", "受領確認済"])
        self.status_filter.currentTextChanged.connect(self.load_contracts)
        filter_layout.addWidget(self.status_filter)

        expiring_btn = create_button("期限切れ間近 (30日以内)", self.show_expiring_contracts)
        filter_layout.addWidget(expiring_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "ID", "発注種別", "発注ステータス", "番組名", "案件名", "取引先名", "委託開始日", "委託終了日",
            "契約期間", "PDFステータス", "配布日", "確認者", "PDFパス", "備考"
        ])

        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 案件名
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # 取引先名

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self.edit_contract)
        layout.addWidget(self.table)

        # ボタンエリア
        button_layout = QHBoxLayout()

        # 新規追加ボタン（ドロップダウン付き）
        add_btn = QPushButton("新規追加 ▼")
        add_menu = QMenu()
        add_regular_cast_action = add_menu.addAction("レギュラー出演契約書")
        add_regular_production_action = add_menu.addAction("レギュラー制作発注書")
        add_spot_cast_action = add_menu.addAction("単発出演発注書")
        add_spot_production_action = add_menu.addAction("単発制作発注書")

        add_regular_cast_action.triggered.connect(lambda: self.add_contract("レギュラー出演契約書"))
        add_regular_production_action.triggered.connect(lambda: self.add_contract("レギュラー制作発注書"))
        add_spot_cast_action.triggered.connect(lambda: self.add_contract("単発出演発注書"))
        add_spot_production_action.triggered.connect(lambda: self.add_contract("単発制作発注書"))

        add_btn.setMenu(add_menu)
        button_layout.addWidget(add_btn)

        edit_btn = create_button("編集", self.edit_contract)
        button_layout.addWidget(edit_btn)

        delete_btn = create_button("削除", self.delete_contract)
        button_layout.addWidget(delete_btn)

        button_layout.addSpacing(20)

        pdf_btn = create_button("PDFを開く", self.open_pdf)
        button_layout.addWidget(pdf_btn)

        status_btn = create_button("配布ステータス更新", self.update_status)
        button_layout.addWidget(status_btn)

        sync_btn = create_button("番組マスタと同期", self.sync_to_program)
        button_layout.addWidget(sync_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_contracts(self):
        """発注書一覧を読み込み"""
        search_term = self.search_input.text()
        status_filter = self.status_filter.currentText()
        order_type_filter = self.order_type_filter.currentText()
        order_status_filter = self.order_status_filter.currentText()

        if status_filter == "すべて":
            status_filter = None
        if order_type_filter == "すべて":
            order_type_filter = None
        if order_status_filter == "すべて":
            order_status_filter = None

        # 新しい階層対応メソッドを使用
        try:
            contracts = self.db.get_order_contracts_with_project_info(search_term)
        except AttributeError:
            # 古いメソッドにフォールバック
            contracts = self.db.get_order_contracts(search_term, status_filter, order_type_filter, order_status_filter)

        self.table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            # 新しいフォーマット:
            # contract: (id, program_id, program_name, project_id, project_name,
            #            partner_id, partner_name, item_name, contract_start_date,
            #            contract_end_date, order_type, order_status, pdf_status,
            #            notes, created_at, updated_at)

            self.table.setItem(row, 0, QTableWidgetItem(str(contract[0])))  # ID
            self.table.setItem(row, 1, QTableWidgetItem(contract[10] or "発注書"))  # 発注種別
            self.table.setItem(row, 2, QTableWidgetItem(contract[11] or "未"))  # 発注ステータス
            self.table.setItem(row, 3, QTableWidgetItem(contract[2] or ""))  # 番組名
            self.table.setItem(row, 4, QTableWidgetItem(contract[4] or "-"))  # 案件名
            self.table.setItem(row, 5, QTableWidgetItem(contract[6] or ""))  # 取引先名
            self.table.setItem(row, 6, QTableWidgetItem(contract[8] or ""))  # 委託開始日
            self.table.setItem(row, 7, QTableWidgetItem(contract[9] or ""))  # 委託終了日
            self.table.setItem(row, 8, QTableWidgetItem("-"))  # 契約期間（簡略化）
            self.table.setItem(row, 9, QTableWidgetItem(contract[12] or ""))  # PDFステータス
            self.table.setItem(row, 10, QTableWidgetItem("-"))  # 配布日（簡略化）
            self.table.setItem(row, 11, QTableWidgetItem("-"))  # 確認者（簡略化）
            self.table.setItem(row, 12, QTableWidgetItem("-"))  # PDFパス（簡略化）
            self.table.setItem(row, 13, QTableWidgetItem(contract[13] or ""))  # 備考

            # 期限切れ間近の行を赤色でハイライト
            if contract[9]:  # contract_end_date (新しいインデックス)
                try:
                    end_date = datetime.strptime(contract[9], '%Y-%m-%d')
                    days_until_expiry = (end_date - datetime.now()).days

                    if 0 <= days_until_expiry <= 30:
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            if item:
                                item.setBackground(QColor(255, 204, 204))  # 薄い赤
                except:
                    pass

        # IDカラムとPDFパスカラムを非表示
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(12, True)  # PDFパスも非表示

    def show_expiring_contracts(self):
        """期限切れ間近の発注書を表示"""
        contracts = self.db.get_expiring_contracts(days_before=30)

        if not contracts:
            QMessageBox.information(self, "期限切れ間近", "期限切れ間近の発注書はありません。")
            return

        # フィルタをクリアして期限切れ間近を表示
        self.search_input.clear()
        self.status_filter.setCurrentText("すべて")

        self.table.setRowCount(len(contracts))

        for row, contract in enumerate(contracts):
            self.table.setItem(row, 0, QTableWidgetItem(str(contract[0])))
            self.table.setItem(row, 1, QTableWidgetItem(contract[2] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(contract[4] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(contract[5] or ""))
            self.table.setItem(row, 4, QTableWidgetItem(contract[6] or ""))
            self.table.setItem(row, 5, QTableWidgetItem(contract[7] or ""))
            self.table.setItem(row, 6, QTableWidgetItem(contract[8] or ""))
            self.table.setItem(row, 7, QTableWidgetItem(contract[9] or ""))
            self.table.setItem(row, 8, QTableWidgetItem(contract[10] or ""))

            # すべての行を赤色でハイライト
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 204, 204))

    def add_contract(self, category="レギュラー制作発注書"):
        """新規発注書追加

        Args:
            category: 発注種別（レギュラー出演契約書/レギュラー制作発注書/単発出演発注書/単発制作発注書）
        """
        dialog = UnifiedOrderDialog(self, category=category)
        if dialog.exec_():
            self.load_contracts()

    def edit_contract(self):
        """発注書編集"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "編集する発注書を選択してください。")
            return

        contract_id = int(self.table.item(selected_row, 0).text())

        # 発注書の種類を取得して適切なダイアログを開く
        contract = self.db.get_order_contract_by_id(contract_id)
        if contract and len(contract) > 32:
            # order_categoryはインデックス32（最後から2番目）
            order_category = contract[32] if contract[32] else "レギュラー制作発注書"
        else:
            order_category = "レギュラー制作発注書"

        dialog = UnifiedOrderDialog(self, contract_id=contract_id, category=order_category)
        if dialog.exec_():
            self.load_contracts()

    def delete_contract(self):
        """発注書削除"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "削除する発注書を選択してください。")
            return

        contract_id = int(self.table.item(selected_row, 0).text())
        program_name = self.table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, "確認",
            f"発注書「{program_name}」を削除してもよろしいですか?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_order_contract(contract_id)
                QMessageBox.information(self, "成功", "発注書を削除しました。")
                self.load_contracts()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"発注書の削除に失敗しました:\n{str(e)}")

    def open_pdf(self):
        """PDFファイルを開く"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "PDFを開く発注書を選択してください。")
            return

        pdf_path = self.table.item(selected_row, 9).text()

        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "警告", "PDFファイルが見つかりません。")
            return

        # PDFを開く
        try:
            os.system(f'open "{pdf_path}"')
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"PDFを開けませんでした:\n{str(e)}")

    def update_status(self):
        """配布ステータス更新"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "ステータスを更新する発注書を選択してください。")
            return

        contract_id = int(self.table.item(selected_row, 0).text())

        from order_management.ui.status_update_dialog import StatusUpdateDialog
        dialog = StatusUpdateDialog(self, contract_id)
        if dialog.exec_():
            self.load_contracts()

    def sync_to_program(self):
        """番組マスタと同期"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "同期する発注書を選択してください。")
            return

        contract_id = int(self.table.item(selected_row, 0).text())
        program_name = self.table.item(selected_row, 1).text()
        start_date = self.table.item(selected_row, 3).text()
        end_date = self.table.item(selected_row, 4).text()

        reply = QMessageBox.question(
            self, "確認",
            f"発注書「{program_name}」の委託期間 ({start_date} ～ {end_date}) を\n"
            f"番組マスタに同期してもよろしいですか?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if self.db.sync_contract_to_program(contract_id):
                    QMessageBox.information(self, "成功", "番組マスタと同期しました。")
                else:
                    QMessageBox.warning(self, "警告", "同期に失敗しました。")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"同期に失敗しました:\n{str(e)}")
