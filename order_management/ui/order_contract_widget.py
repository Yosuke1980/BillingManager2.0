"""発注書管理ウィジェット

レギュラー番組の発注書管理機能を提供します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QMessageBox, QFileDialog, QHeaderView, QMenu, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime, timedelta
import os
import shutil
import csv
import codecs

from order_management.database_manager import OrderManagementDB
from order_management.ui.order_contract_edit_dialog import OrderContractEditDialog
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

        # ===== Phase 2: ダッシュボード統計パネル =====
        dashboard_group = QGroupBox("📊 発注状況サマリー")
        dashboard_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        dashboard_layout = QGridLayout()

        self.urgent_label = QLabel("🚨 緊急対応必要: 0件")
        self.urgent_label.setStyleSheet("font-size: 13px; color: #d32f2f;")
        dashboard_layout.addWidget(self.urgent_label, 0, 0)

        self.warning_label = QLabel("⚠️ 注意が必要: 0件")
        self.warning_label.setStyleSheet("font-size: 13px; color: #f57c00;")
        dashboard_layout.addWidget(self.warning_label, 0, 1)

        self.pending_label = QLabel("📝 発注未完了: 0件")
        self.pending_label.setStyleSheet("font-size: 13px;")
        dashboard_layout.addWidget(self.pending_label, 1, 0)

        self.completed_label = QLabel("✅ 正常稼働中: 0件")
        self.completed_label.setStyleSheet("font-size: 13px; color: #388e3c;")
        dashboard_layout.addWidget(self.completed_label, 1, 1)

        self.completion_label = QLabel("完了率: 0%")
        self.completion_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        dashboard_layout.addWidget(self.completion_label, 2, 0, 1, 2)

        dashboard_group.setLayout(dashboard_layout)
        layout.addWidget(dashboard_group)

        # ===== Phase 2.2: カラー凡例 =====
        legend_layout = QHBoxLayout()
        legend_label = QLabel("色の意味: ")
        legend_layout.addWidget(legend_label)

        red_label = QLabel("■ 赤=緊急対応")
        red_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        legend_layout.addWidget(red_label)

        yellow_label = QLabel("■ 黄=注意")
        yellow_label.setStyleSheet("color: #f57c00; font-weight: bold;")
        legend_layout.addWidget(yellow_label)

        green_label = QLabel("■ 緑=完了")
        green_label.setStyleSheet("color: #388e3c; font-weight: bold;")
        legend_layout.addWidget(green_label)

        gray_label = QLabel("■ グレー=通常")
        gray_label.setStyleSheet("color: #757575; font-weight: bold;")
        legend_layout.addWidget(gray_label)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

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
        self.order_status_filter.addItems(["すべて", "未完了", "完了"])
        self.order_status_filter.currentTextChanged.connect(self.load_contracts)
        filter_layout.addWidget(self.order_status_filter)

        expiring_btn = create_button("期限切れ間近 (30日以内)", self.show_expiring_contracts)
        filter_layout.addWidget(expiring_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "発注ステータス", "発注種別", "番組名", "費用項目", "金額",
            "支払タイプ", "取引先名", "開始日", "終了日", "備考"
        ])

        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 費用項目
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # 取引先名

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

        button_layout.addSpacing(20)

        # CSV出力・読み込みボタン
        export_csv_btn = create_button("CSV出力", self.export_to_csv)
        button_layout.addWidget(export_csv_btn)

        import_csv_btn = create_button("CSV読込", self.import_from_csv)
        button_layout.addWidget(import_csv_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_contracts(self):
        """発注書一覧を読み込み（Phase 1: 色分けとステータス詳細化）"""
        search_term = self.search_input.text()
        order_type_filter = self.order_type_filter.currentText()
        order_status_filter = self.order_status_filter.currentText()

        if order_type_filter == "すべて":
            order_type_filter = None
        if order_status_filter == "すべて":
            order_status_filter = None

        # 新しい階層対応メソッドを使用
        try:
            contracts = self.db.get_order_contracts_with_project_info(search_term)
        except AttributeError:
            # 古いメソッドにフォールバック
            contracts = self.db.get_order_contracts(search_term, None, order_type_filter, order_status_filter)

        # フィルタ適用
        if order_type_filter:
            contracts = [c for c in contracts if c[10] == order_type_filter]
        if order_status_filter:
            contracts = [c for c in contracts if c[11] == order_status_filter]

        self.table.setRowCount(len(contracts))

        # 統計用カウンタ
        urgent_count = 0    # 🚨 期限切れまたは期限間近
        warning_count = 0   # ⚠️ 30日以内
        pending_count = 0   # 📝 未完了
        completed_count = 0 # ✅ 完了

        for row, contract in enumerate(contracts):
            # 新しいフォーマット:
            # contract: (id, program_id, program_name, project_id, project_name,
            #            partner_id, partner_name, item_name, contract_start_date,
            #            contract_end_date, order_type, order_status, pdf_status,
            #            notes, created_at, updated_at, payment_type, unit_price...)

            order_status = contract[11] or "未"
            end_date_str = contract[9]

            # Phase 1.3: 期限チェック
            days_until_expiry = None
            is_expired = False
            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    days_until_expiry = (end_date - datetime.now()).days
                    is_expired = days_until_expiry < 0
                except:
                    pass

            # Phase 1.1: 行の背景色を決定
            row_color = None
            if is_expired or (days_until_expiry is not None and 0 <= days_until_expiry <= 7):
                # 🔴 赤: 期限切れまたは7日以内
                row_color = QColor(255, 220, 220)
                urgent_count += 1
            elif days_until_expiry is not None and 8 <= days_until_expiry <= 30:
                # 🟡 黄: 8-30日以内
                row_color = QColor(255, 255, 200)
                warning_count += 1
            elif order_status in ["完了", "済"]:
                # 🟢 緑: 完了
                row_color = QColor(220, 255, 220)
                completed_count += 1
            elif order_status in ["未", "未完了"]:
                # 📝 未完了
                row_color = QColor(245, 245, 245)
                pending_count += 1
            else:
                row_color = QColor(245, 245, 245)

            # データを取得
            item_name = contract[7] if len(contract) > 7 else ""
            payment_type = contract[16] if len(contract) > 16 else ""
            unit_price = contract[17] if len(contract) > 17 else 0

            # 金額のフォーマット
            amount_text = f"¥{int(unit_price):,}" if unit_price else ""

            # 新しい列構成に合わせてデータを設定
            status_item = QTableWidgetItem(order_status)
            status_item.setData(Qt.UserRole, contract[0])  # IDを保存
            self.table.setItem(row, 0, status_item)  # 発注ステータス
            self.table.setItem(row, 1, QTableWidgetItem(contract[10] or "発注書"))  # 発注種別
            self.table.setItem(row, 2, QTableWidgetItem(contract[2] or ""))  # 番組名
            self.table.setItem(row, 3, QTableWidgetItem(item_name))  # 費用項目
            self.table.setItem(row, 4, QTableWidgetItem(amount_text))  # 金額
            self.table.setItem(row, 5, QTableWidgetItem(payment_type or ""))  # 支払タイプ
            self.table.setItem(row, 6, QTableWidgetItem(contract[6] or ""))  # 取引先名
            self.table.setItem(row, 7, QTableWidgetItem(contract[8] or ""))  # 開始日

            # 終了日に期限情報を追加
            deadline_text = self._format_deadline(end_date_str, days_until_expiry, is_expired)
            self.table.setItem(row, 8, QTableWidgetItem(deadline_text))  # 終了日

            self.table.setItem(row, 9, QTableWidgetItem(contract[13] or ""))  # 備考

            # Phase 1.1: 行全体に背景色を適用
            if row_color:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(row_color)

        # 全ての列を表示（非表示なし）

        # Phase 2: ダッシュボードを更新
        self._update_dashboard(urgent_count, warning_count, pending_count, completed_count, len(contracts))

    def _get_detailed_status(self, order_status, pdf_status):
        """Phase 1.2: ステータスを詳細化"""
        if order_status in ["完了", "済"]:
            if pdf_status == "受領確認済":
                return "✅ 完了"
            elif pdf_status == "配布済":
                return "📄 配布済"
            else:
                return "⚠️ 発注済・未配布"
        else:
            return "❌ 未発注"

    def _format_deadline(self, date_str, days_until, is_expired):
        """Phase 1.3: 期限情報をフォーマット"""
        if not date_str:
            return "-"

        if is_expired:
            return f"🚨 {date_str} (期限切れ)"
        elif days_until is not None and days_until <= 30:
            return f"⚠️ {date_str} (あと{days_until}日)"
        else:
            return date_str

    def _update_dashboard(self, urgent, warning, pending, completed, total):
        """Phase 2: ダッシュボードを更新"""
        self.urgent_label.setText(f"🚨 緊急対応必要: {urgent}件 (期限切れ・赤表示)")
        self.warning_label.setText(f"⚠️ 注意が必要: {warning}件 (30日以内・黄表示)")
        self.pending_label.setText(f"📝 発注未完了: {pending}件")
        self.completed_label.setText(f"✅ 正常稼働中: {completed}件 (緑表示)")

        if total > 0:
            completion_rate = int((completed / total) * 100)
            bar_length = 20
            filled = int((completion_rate / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            self.completion_label.setText(f"完了率: [{bar}] {completion_rate}% ({completed}/{total}件)")
        else:
            self.completion_label.setText("完了率: データなし")

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
            category: 発注種別（互換性のため残す）
        """
        # 新しい発注書編集ダイアログを使用
        dialog = OrderContractEditDialog(self)
        if dialog.exec_():
            self.load_contracts()

    def edit_contract(self):
        """発注書編集"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "編集する発注書を選択してください。")
            return

        # UserRoleからIDを取得
        contract_id = self.table.item(selected_row, 0).data(Qt.UserRole)

        # 新しい発注書編集ダイアログを使用
        dialog = OrderContractEditDialog(self, contract_id=contract_id)
        if dialog.exec_():
            self.load_contracts()

    def delete_contract(self):
        """発注書削除"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "警告", "削除する発注書を選択してください。")
            return

        # UserRoleからIDを取得
        contract_id = self.table.item(selected_row, 0).data(Qt.UserRole)
        program_name = self.table.item(selected_row, 2).text()  # 番組名は2列目

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

    def export_to_csv(self):
        """発注データをCSVに出力"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                "発注管理.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # 現在のフィルタ条件で発注データを取得
            search_term = self.search_input.text()
            status_filter = self.status_filter.currentText()
            order_type_filter = self.order_type_filter.currentText()
            order_status_filter = self.order_status_filter.currentText()

            # フィルタ条件に応じた値を設定
            pdf_status = None if status_filter == "すべて" else status_filter
            order_type = None if order_type_filter == "すべて" else order_type_filter
            order_status = None if order_status_filter == "すべて" else order_status_filter

            # データ取得（旧形式を使用）
            contracts = self.db.get_order_contracts(search_term, pdf_status, order_type, order_status)

            # CSV出力（UTF-8 with BOM）
            with codecs.open(file_path, 'w', 'utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow([
                    'ID', '番組名', '取引先名', '委託開始日', '委託終了日',
                    '発注種別', '発注ステータス', 'PDFステータス', '備考'
                ])

                # データ行
                for contract in contracts:
                    # contract: (id, program_id, program_name, partner_id, partner_name,
                    #            contract_start_date, contract_end_date, contract_period_type,
                    #            pdf_status, pdf_distributed_date, confirmed_by,
                    #            pdf_file_path, notes, order_type, order_status, ...)
                    writer.writerow([
                        contract[0],  # ID
                        contract[2] or '',  # 番組名
                        contract[4] or '',  # 取引先名
                        contract[5] or '',  # 委託開始日
                        contract[6] or '',  # 委託終了日
                        contract[13] or '発注書',  # 発注種別
                        contract[14] or '未',  # 発注ステータス
                        contract[8] or '未配布',  # PDFステータス
                        contract[12] or ''  # 備考
                    ])

            QMessageBox.information(
                self,
                "CSV出力完了",
                f"{len(contracts)}件の発注データをCSVに出力しました。\n\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{e}")

    def import_from_csv(self):
        """CSVから発注データを読み込み"""
        try:
            # ファイル選択ダイアログ
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "CSV読み込み",
                "",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # CSV読み込み
            csv_data = []
            with codecs.open(file_path, 'r', 'utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    csv_data.append(row)

            if not csv_data:
                QMessageBox.warning(self, "警告", "CSVファイルにデータがありません")
                return

            # 上書き/追記の選択ダイアログを表示
            reply = QMessageBox.question(
                self,
                'インポート方法の選択',
                f'{len(csv_data)}件のデータを読み込みます。\n\n'
                '既存のデータをどうしますか？\n\n'
                '「はい」: 上書き（既存データを削除して新規データのみ）\n'
                '「いいえ」: 追記（既存データを保持してIDがあれば更新、なければ追加）\n\n'
                '※番組名と取引先名が存在する必要があります',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )

            if reply == QMessageBox.Cancel:
                return

            overwrite = (reply == QMessageBox.Yes)

            # データベースにインポート
            result = self.db.import_order_contracts_from_csv(csv_data, overwrite)

            # 結果を表示
            message = f"CSV読み込み完了\n\n"
            message += f"成功: {result['success']}件\n"
            message += f"  - 新規追加: {result['inserted']}件\n"
            message += f"  - 更新: {result['updated']}件\n"
            message += f"スキップ: {result['skipped']}件\n"

            if result['errors']:
                message += f"\nエラー詳細:\n"
                for error in result['errors'][:10]:  # 最初の10件のみ表示
                    message += f"  - {error['row']}行目: {error['reason']}\n"
                if len(result['errors']) > 10:
                    message += f"  ... 他{len(result['errors']) - 10}件のエラー\n"

            QMessageBox.information(self, "CSV読み込み完了", message)

            # データを再読み込み
            self.load_contracts()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV読み込みに失敗しました:\n{e}")
