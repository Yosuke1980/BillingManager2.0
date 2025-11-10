"""費用項目管理ウィジェット

費用項目（expense_items）の一覧表示と管理機能を提供します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QMessageBox, QHeaderView, QGroupBox, QGridLayout,
                             QDialog, QFileDialog, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from datetime import datetime
import csv
import codecs

from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_button
from order_management.ui.expense_item_edit_dialog import ExpenseItemEditDialog


class ExpenseItemsWidget(QWidget):
    """費用項目管理ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()

        self.init_ui()
        self.load_expense_items()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # ===== ダッシュボード統計パネル =====
        dashboard_group = QGroupBox("📊 費用項目サマリー")
        dashboard_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        dashboard_layout = QGridLayout()

        self.total_label = QLabel("総件数: 0件")
        self.total_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        dashboard_layout.addWidget(self.total_label, 0, 0)

        self.amount_label = QLabel("総額: ¥0")
        self.amount_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        dashboard_layout.addWidget(self.amount_label, 0, 1)

        self.unpaid_label = QLabel("未払い: 0件")
        self.unpaid_label.setStyleSheet("font-size: 13px; color: #d32f2f;")
        dashboard_layout.addWidget(self.unpaid_label, 1, 0)

        self.paid_label = QLabel("支払済: 0件")
        self.paid_label.setStyleSheet("font-size: 13px; color: #388e3c;")
        dashboard_layout.addWidget(self.paid_label, 1, 1)

        self.pending_label = QLabel("金額未定: 0件")
        self.pending_label.setStyleSheet("font-size: 13px; color: #f57c00;")
        dashboard_layout.addWidget(self.pending_label, 1, 2)

        self.overdue_label = QLabel("⚠️ 期限超過: 0件")
        self.overdue_label.setStyleSheet("font-size: 13px; color: #d32f2f; font-weight: bold;")
        self.overdue_label.setCursor(Qt.PointingHandCursor)
        self.overdue_label.mousePressEvent = self._show_overdue_items
        dashboard_layout.addWidget(self.overdue_label, 2, 0)

        dashboard_group.setLayout(dashboard_layout)
        layout.addWidget(dashboard_group)

        # ===== 検索・フィルタエリア =====
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("検索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("番組名、取引先名、項目名で検索")
        self.search_input.textChanged.connect(self.load_expense_items)
        filter_layout.addWidget(self.search_input)

        filter_layout.addWidget(QLabel("支払状態:"))
        self.payment_status_filter = QComboBox()
        self.payment_status_filter.addItems(["すべて", "未払い", "支払済"])
        self.payment_status_filter.currentTextChanged.connect(self.load_expense_items)
        filter_layout.addWidget(self.payment_status_filter)

        filter_layout.addWidget(QLabel("状態:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["すべて", "発注予定", "発注済", "請求書受領", "支払完了"])
        self.status_filter.currentTextChanged.connect(self.load_expense_items)
        filter_layout.addWidget(self.status_filter)

        filter_layout.addWidget(QLabel("支払月:"))
        self.payment_month_filter = QComboBox()
        self.payment_month_filter.addItem("すべて", None)
        self._populate_payment_months()
        self.payment_month_filter.currentTextChanged.connect(self.load_expense_items)
        filter_layout.addWidget(self.payment_month_filter)

        self.show_archived_checkbox = QCheckBox("アーカイブ済みを表示")
        self.show_archived_checkbox.stateChanged.connect(self.load_expense_items)
        filter_layout.addWidget(self.show_archived_checkbox)

        layout.addLayout(filter_layout)

        # ===== テーブル =====
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "ID", "番組名", "取引先名", "項目名", "業務種別", "金額",
            "実施日", "支払予定日", "状態", "支払状態",
            "契約ID", "備考"
        ])

        # 列幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 取引先名
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 項目名
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 業務種別
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 実施日
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 支払予定日
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # 状態
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # 支払状態
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # 契約ID
        header.setSectionResizeMode(11, QHeaderView.Stretch)  # 備考

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)  # 複数選択を許可
        self.table.doubleClicked.connect(self.edit_expense_item)

        layout.addWidget(self.table)

        # ===== ボタンエリア =====
        button_layout = QHBoxLayout()

        self.add_button = create_button("➕ 新規追加", self.add_expense_item)
        button_layout.addWidget(self.add_button)

        self.edit_button = create_button("✏️ 編集", self.edit_expense_item)
        button_layout.addWidget(self.edit_button)

        self.delete_button = create_button("🗑️ 削除", self.delete_expense_item)
        button_layout.addWidget(self.delete_button)

        self.change_production_button = create_button("📋 番組を変更", self.change_production_bulk)
        button_layout.addWidget(self.change_production_button)

        self.archive_button = create_button("📦 アーカイブ実行", self.archive_old_items)
        button_layout.addWidget(self.archive_button)

        button_layout.addStretch()

        self.export_csv_button = create_button("📤 CSV出力", self.export_to_csv)
        button_layout.addWidget(self.export_csv_button)

        self.import_csv_button = create_button("📥 CSV読込", self.import_from_csv)
        button_layout.addWidget(self.import_csv_button)

        self.refresh_button = create_button("🔄 更新", self.load_expense_items)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _populate_payment_months(self):
        """支払月のリストを作成"""
        # 特殊フィルタを最初に追加
        self.payment_month_filter.addItem("当月＋未払い", "current_unpaid")

        # データベースから支払予定日の年月を取得
        try:
            months = self.db.get_payment_months()
            for month in months:
                # month: "2025-08" 形式
                if month:
                    # "2025年8月" 形式に変換
                    year, month_num = month.split('-')
                    display_text = f"{year}年{int(month_num)}月"
                    self.payment_month_filter.addItem(display_text, month)
        except Exception as e:
            print(f"支払月リスト作成エラー: {e}")

        # デフォルトを「当月＋未払い」に設定
        self.payment_month_filter.setCurrentIndex(0)

    def load_expense_items(self):
        """費用項目を読み込んで表示"""
        search_term = self.search_input.text()
        payment_status = self.payment_status_filter.currentText()
        status = self.status_filter.currentText()
        payment_month = self.payment_month_filter.currentData()
        show_archived = self.show_archived_checkbox.isChecked()

        if payment_status == "すべて":
            payment_status = None
        if status == "すべて":
            status = None

        # データベースから費用項目を取得
        expense_items = self.db.get_expense_items_with_details(
            search_term=search_term,
            payment_status=payment_status,
            status=status,
            payment_month=payment_month,
            show_archived=show_archived
        )

        self.table.setRowCount(len(expense_items))

        # 統計用カウンタ
        total_amount = 0
        unpaid_count = 0
        paid_count = 0
        pending_count = 0
        overdue_count = 0

        for row, item in enumerate(expense_items):
            # データ構造: (id, production_id, production_name, partner_id, partner_name,
            #            item_name, amount, implementation_date, expected_payment_date,
            #            status, payment_status, contract_id, notes, work_type,
            #            order_number, order_date, invoice_received_date, actual_payment_date,
            #            invoice_number, withholding_tax, consumption_tax, payment_amount,
            #            invoice_file_path, payment_method, approver, approval_date, amount_pending)

            item_id = item[0]
            production_name = item[2] or ""
            partner_name = item[4] or ""
            item_name = item[5] or ""
            amount = item[6] or 0
            implementation_date = item[7] or ""
            expected_payment_date = item[8] or ""
            item_status = item[9] or "発注予定"
            payment_status = item[10] or "未払い"
            contract_id = item[11]
            notes = item[12] or ""
            work_type = item[13] or "制作"
            amount_pending = item[26] if len(item) > 26 else 0

            # 統計更新
            if amount_pending == 1:
                pending_count += 1
            else:
                total_amount += amount

            if payment_status == "支払済":
                paid_count += 1
            else:
                unpaid_count += 1
                # 期限超過チェック
                if expected_payment_date:
                    try:
                        payment_date = datetime.strptime(expected_payment_date, '%Y-%m-%d')
                        if payment_date.date() < datetime.now().date():
                            overdue_count += 1
                    except:
                        pass

            # 金額のフォーマット
            if amount_pending == 1:
                amount_text = "未定"
            else:
                amount_text = f"¥{int(amount):,}"

            # 行の背景色を決定（優先順位: 期限超過 > 支払済 > 金額未定 > 支払間近）
            row_color = None

            # 最優先: 期限超過（未払い＋支払予定日が過去）
            if payment_status == "未払い" and expected_payment_date:
                try:
                    payment_date = datetime.strptime(expected_payment_date, '%Y-%m-%d')
                    if payment_date.date() < datetime.now().date():
                        row_color = QColor(255, 200, 200)  # 濃い赤（期限超過）
                except:
                    pass

            # 支払済み
            if not row_color and payment_status == "支払済":
                row_color = QColor(220, 255, 220)  # 緑

            # 金額未定
            if not row_color and amount_pending == 1:
                row_color = QColor(255, 243, 224)  # 薄いオレンジ（金額未定）

            # 支払間近（7日以内）
            if not row_color and payment_status == "未払い" and expected_payment_date:
                try:
                    payment_date = datetime.strptime(expected_payment_date, '%Y-%m-%d')
                    days_until = (payment_date.date() - datetime.now().date()).days
                    if 0 <= days_until <= 7:
                        row_color = QColor(255, 255, 200)  # 黄（間近）
                except:
                    pass

            # テーブルにデータを設定
            id_item = QTableWidgetItem(str(item_id))
            id_item.setData(Qt.UserRole, item_id)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(production_name))
            self.table.setItem(row, 2, QTableWidgetItem(partner_name))
            self.table.setItem(row, 3, QTableWidgetItem(item_name))
            self.table.setItem(row, 4, QTableWidgetItem(work_type))
            self.table.setItem(row, 5, QTableWidgetItem(amount_text))
            self.table.setItem(row, 6, QTableWidgetItem(implementation_date))
            self.table.setItem(row, 7, QTableWidgetItem(expected_payment_date))
            self.table.setItem(row, 8, QTableWidgetItem(item_status))
            self.table.setItem(row, 9, QTableWidgetItem(payment_status))
            self.table.setItem(row, 10, QTableWidgetItem(str(contract_id) if contract_id else ""))
            self.table.setItem(row, 11, QTableWidgetItem(notes))

            # 行全体に背景色を適用
            if row_color:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(row_color)

        # ダッシュボードを更新
        self._update_dashboard(len(expense_items), total_amount, unpaid_count, paid_count, pending_count, overdue_count)

    def _update_dashboard(self, total_count, total_amount, unpaid_count, paid_count, pending_count, overdue_count):
        """ダッシュボードの統計を更新"""
        self.total_label.setText(f"総件数: {total_count}件")
        self.amount_label.setText(f"総額: ¥{int(total_amount):,}")
        self.unpaid_label.setText(f"未払い: {unpaid_count}件")
        self.paid_label.setText(f"支払済: {paid_count}件")
        self.pending_label.setText(f"金額未定: {pending_count}件")
        self.overdue_label.setText(f"⚠️ 期限超過: {overdue_count}件")

    def _show_overdue_items(self, event):
        """期限超過項目のみを表示"""
        # 支払状態を「未払い」に設定
        self.payment_status_filter.setCurrentText("未払い")
        # 支払月を「すべて」に設定
        idx = self.payment_month_filter.findData(None)
        if idx >= 0:
            self.payment_month_filter.setCurrentIndex(idx)
        # load_expense_itemsは自動的に呼ばれる

    def archive_old_items(self):
        """1年以上前の支払済み項目をアーカイブ"""
        try:
            count = self.db.get_archive_candidate_count(12)
            if count == 0:
                QMessageBox.information(self, "アーカイブ",
                    "アーカイブ対象の項目はありません。\n\n"
                    "（1年以上前の支払済み項目が対象です）")
                return

            reply = QMessageBox.question(self, "アーカイブ確認",
                f"1年以上前の支払済み項目（{count}件）をアーカイブしますか？\n\n"
                f"アーカイブした項目は通常表示されなくなりますが、\n"
                f"「アーカイブ済みを表示」をチェックすると閲覧できます。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                archived_count = self.db.archive_old_expense_items(12)
                QMessageBox.information(self, "アーカイブ完了",
                    f"✓ {archived_count}件の項目をアーカイブしました。")
                self.load_expense_items()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"アーカイブに失敗しました:\n{e}")

    def add_expense_item(self):
        """費用項目を追加"""
        dialog = ExpenseItemEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            expense_data = dialog.get_expense_data()
            try:
                self.db.save_expense_item(expense_data)
                QMessageBox.information(self, "成功", "費用項目を追加しました。")
                self.load_expense_items()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"費用項目の追加に失敗しました:\n{e}")

    def edit_expense_item(self):
        """選択された費用項目を編集"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "編集する費用項目を選択してください。")
            return

        row = selected_rows[0].row()
        expense_id = self.table.item(row, 0).data(Qt.UserRole)

        dialog = ExpenseItemEditDialog(self, expense_id=expense_id)
        if dialog.exec_() == QDialog.Accepted:
            expense_data = dialog.get_expense_data()
            try:
                self.db.save_expense_item(expense_data)
                QMessageBox.information(self, "成功", "費用項目を更新しました。")
                self.load_expense_items()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"費用項目の更新に失敗しました:\n{e}")

    def delete_expense_item(self):
        """選択された費用項目を削除（複数選択対応）"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "削除する費用項目を選択してください。")
            return

        # 選択された費用項目のIDと名前を取得
        items_to_delete = []
        for index in selected_rows:
            row = index.row()
            item_id = self.table.item(row, 0).data(Qt.UserRole)
            item_name = self.table.item(row, 3).text()
            partner_name = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            items_to_delete.append((item_id, item_name, partner_name))

        # 確認メッセージ
        if len(items_to_delete) == 1:
            _, item_name, partner_name = items_to_delete[0]
            message = f"費用項目「{item_name}」({partner_name})を削除してもよろしいですか？"
        else:
            message = f"{len(items_to_delete)}件の費用項目を削除してもよろしいですか?\n\n"
            message += "削除対象:\n"
            for _, item_name, partner_name in items_to_delete[:5]:  # 最初の5件のみ表示
                message += f"  • {item_name} ({partner_name})\n"
            if len(items_to_delete) > 5:
                message += f"  ...他{len(items_to_delete) - 5}件"

        reply = QMessageBox.question(
            self, "確認", message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success_count = 0
            error_messages = []

            for item_id, item_name, partner_name in items_to_delete:
                try:
                    self.db.delete_expense_item(item_id)
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"{item_name} ({partner_name}): {str(e)}")

            # 結果を表示
            if success_count > 0:
                self.load_expense_items()

            if error_messages:
                error_text = "\n".join(error_messages)
                QMessageBox.warning(
                    self, "削除結果",
                    f"{success_count}件削除しました。\n\n以下の削除に失敗しました:\n{error_text}"
                )
            elif success_count > 0:
                QMessageBox.information(
                    self, "成功",
                    f"{success_count}件の費用項目を削除しました。"
                )

    def change_production_bulk(self):
        """選択された費用項目の番組を一括変更"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "番組を変更する費用項目を選択してください。")
            return

        # 選択された費用項目の情報を取得
        items_to_change = []
        for index in selected_rows:
            row = index.row()
            item_id = self.table.item(row, 0).data(Qt.UserRole)
            item_name = self.table.item(row, 3).text()
            current_production = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            items_to_change.append((item_id, item_name, current_production))

        # 番組選択ダイアログを表示
        production_id = self._show_production_selection_dialog(items_to_change)
        if production_id is None:
            return  # キャンセルされた

        # 確認メッセージ
        if len(items_to_change) == 1:
            message = f"費用項目「{items_to_change[0][1]}」の番組を変更しますか？"
        else:
            message = f"{len(items_to_change)}件の費用項目の番組を変更しますか？\n\n"
            message += "変更対象:\n"
            for _, item_name, current_prod in items_to_change[:5]:
                message += f"  • {item_name} (現在: {current_prod})\n"
            if len(items_to_change) > 5:
                message += f"  ...他{len(items_to_change) - 5}件"

        reply = QMessageBox.question(
            self, "確認", message,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                expense_ids = [item[0] for item in items_to_change]
                updated_count = self.db.update_expense_items_production(expense_ids, production_id)

                QMessageBox.information(
                    self, "成功",
                    f"{updated_count}件の費用項目の番組を変更しました。"
                )
                self.load_expense_items()
            except Exception as e:
                QMessageBox.critical(
                    self, "エラー",
                    f"番組の変更に失敗しました:\n{e}"
                )

    def _show_production_selection_dialog(self, items_to_change):
        """番組選択ダイアログを表示

        Args:
            items_to_change: 変更対象の費用項目リスト [(id, name, current_production), ...]

        Returns:
            int or None: 選択された番組ID、キャンセル時はNone
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("番組・イベントを選択")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        # 説明ラベル
        if len(items_to_change) == 1:
            info_text = f"費用項目「{items_to_change[0][1]}」の番組を変更します。"
        else:
            info_text = f"{len(items_to_change)}件の費用項目の番組を変更します。"

        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)

        # 番組選択コンボボックス
        form_layout = QFormLayout()
        production_combo = QComboBox()
        production_combo.setMinimumWidth(400)

        # 番組リストを取得
        productions = self.db.get_all_productions()
        for prod in productions:
            # prod: (id, name, type, ...)
            display_text = f"{prod[1]}"
            if prod[2]:  # type
                display_text += f" ({prod[2]})"
            production_combo.addItem(display_text, prod[0])

        form_layout.addRow("変更先の番組:", production_combo)
        layout.addLayout(form_layout)

        # ボタン
        from PyQt5.QtWidgets import QDialogButtonBox
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        # ダイアログを表示
        if dialog.exec_() == QDialog.Accepted:
            return production_combo.currentData()
        return None

    def export_to_csv(self):
        """費用項目データをCSVに出力"""
        try:
            # ファイル保存ダイアログ
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                "費用項目.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            # 現在表示されている全ての費用項目データを取得
            expense_items = self.db.get_expense_items_with_details()

            # CSV出力（UTF-8 with BOM）
            with codecs.open(file_path, 'w', 'utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー行
                writer.writerow([
                    'ID', '契約ID', '番組名', '取引先名', '項目名', '業務種別',
                    '金額', '実施日', '発注番号', '発注日', '状態',
                    '請求書受領日', '支払予定日', '実際支払日', '請求書番号',
                    '支払状態', '源泉徴収額', '消費税額', '支払金額',
                    '請求書ファイルパス', '支払方法', '承認者', '承認日', '備考'
                ])

                # データ行
                for item in expense_items:
                    # item structure based on get_expense_items_with_details:
                    # (id, production_id, production_name, partner_id, partner_name,
                    #  item_name, amount, implementation_date, expected_payment_date,
                    #  status, payment_status, contract_id, notes, work_type,
                    #  order_number, order_date, invoice_received_date, actual_payment_date,
                    #  invoice_number, withholding_tax, consumption_tax, payment_amount,
                    #  invoice_file_path, payment_method, approver, approval_date)

                    writer.writerow([
                        item[0] or '',   # ID
                        item[11] or '',  # 契約ID
                        item[2] or '',   # 番組名
                        item[4] or '',   # 取引先名
                        item[5] or '',   # 項目名
                        item[13] or '',  # 業務種別
                        item[6] or '',   # 金額
                        item[7] or '',   # 実施日
                        item[14] or '',  # 発注番号
                        item[15] or '',  # 発注日
                        item[9] or '',   # 状態
                        item[16] or '',  # 請求書受領日
                        item[8] or '',   # 支払予定日
                        item[17] or '',  # 実際支払日
                        item[18] or '',  # 請求書番号
                        item[10] or '',  # 支払状態
                        item[19] or '',  # 源泉徴収額
                        item[20] or '',  # 消費税額
                        item[21] or '',  # 支払金額
                        item[22] or '',  # 請求書ファイルパス
                        item[23] or '',  # 支払方法
                        item[24] or '',  # 承認者
                        item[25] or '',  # 承認日
                        item[12] or ''   # 備考
                    ])

            QMessageBox.information(
                self,
                "CSV出力完了",
                f"{len(expense_items)}件の費用項目データをCSVに出力しました。\n\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{e}")

    def import_from_csv(self):
        """CSVから費用項目データを読み込み"""
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
                '「いいえ」: 追記（既存データを保持してIDがあれば更新、なければ追加）',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )

            if reply == QMessageBox.Cancel:
                return

            overwrite = (reply == QMessageBox.Yes)

            # データベースにインポート
            result = self.db.import_expense_items_from_csv(csv_data, overwrite)

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
            self.load_expense_items()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV読み込みに失敗しました:\n{e}")
