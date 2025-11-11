"""番組別費用詳細ウィジェット

番組・イベントごとの費用集計と詳細情報を表示します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                             QComboBox, QGroupBox, QGridLayout, QHeaderView, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from order_management.database_manager import OrderManagementDB


class ProductionExpenseDetailWidget(QWidget):
    """番組別費用詳細ウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.current_production_id = None

        self.init_ui()
        self.load_production_list()

    def init_ui(self):
        """UIの初期化"""
        layout = QHBoxLayout()

        # スプリッター（左右分割）
        splitter = QSplitter(Qt.Horizontal)

        # 左側: 番組一覧
        left_widget = self._create_production_list_panel()
        splitter.addWidget(left_widget)

        # 右側: 選択した番組の詳細
        right_widget = self._create_detail_panel()
        splitter.addWidget(right_widget)

        # 初期サイズ比率を設定（左:右 = 1:2）
        splitter.setSizes([300, 600])

        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_production_list_panel(self):
        """番組一覧パネルを作成"""
        widget = QWidget()
        layout = QVBoxLayout()

        # タイトル
        title_label = QLabel("📊 番組・イベント一覧")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)

        # 検索・フィルタエリア
        filter_layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("番組名で検索")
        self.search_input.textChanged.connect(self.load_production_list)
        search_layout.addWidget(self.search_input)
        filter_layout.addLayout(search_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("種別:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["全て", "レギュラー", "イベント", "特番", "コーナー"])
        self.type_filter.currentTextChanged.connect(self.load_production_list)
        type_layout.addWidget(self.type_filter)
        filter_layout.addLayout(type_layout)

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("並び替え:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["総費用額順", "月額平均順", "未払い件数順", "費用項目数順"])
        self.sort_combo.currentTextChanged.connect(self.load_production_list)
        sort_layout.addWidget(self.sort_combo)
        filter_layout.addLayout(sort_layout)

        layout.addLayout(filter_layout)

        # 番組一覧テーブル
        self.production_table = QTableWidget()
        self.production_table.setColumnCount(5)
        self.production_table.setHorizontalHeaderLabels([
            "番組名", "種別", "総費用額", "未払い", "支払済"
        ])

        # 列幅の設定
        header = self.production_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 種別
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 総費用額
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 未払い
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 支払済

        self.production_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.production_table.setSelectionMode(QTableWidget.SingleSelection)
        self.production_table.itemSelectionChanged.connect(self.on_production_selected)
        self.production_table.itemDoubleClicked.connect(self.on_production_double_clicked)

        layout.addWidget(self.production_table)

        # 更新ボタン
        refresh_button_layout = QHBoxLayout()
        refresh_button = QPushButton("🔄 一覧を更新")
        refresh_button.setToolTip("他のタブで追加した番組を反映します")
        refresh_button.clicked.connect(self.load_production_list)
        refresh_button_layout.addWidget(refresh_button)
        refresh_button_layout.addStretch()
        layout.addLayout(refresh_button_layout)

        widget.setLayout(layout)
        return widget

    def _create_detail_panel(self):
        """詳細パネルを作成"""
        widget = QWidget()
        layout = QVBoxLayout()

        # サマリーパネル
        self.summary_group = self._create_summary_panel()
        layout.addWidget(self.summary_group)

        # 月別集計ボタン
        button_layout = QHBoxLayout()
        self.monthly_button = QPushButton("📈 月別集計を表示")
        self.monthly_button.clicked.connect(self.show_monthly_summary)
        self.monthly_button.setEnabled(False)
        button_layout.addWidget(self.monthly_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 費用項目一覧テーブル
        detail_label = QLabel("💰 費用項目一覧")
        detail_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 5px;")
        layout.addWidget(detail_label)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels([
            "実施日", "項目名", "コーナー", "金額", "取引先", "支払予定日", "支払状態"
        ])

        # 列幅の設定
        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 実施日
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 項目名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # コーナー
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 取引先
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 支払予定日
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 支払状態

        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.itemDoubleClicked.connect(self.on_expense_item_double_clicked)

        layout.addWidget(self.detail_table)

        widget.setLayout(layout)
        return widget

    def _create_summary_panel(self):
        """サマリーパネルを作成"""
        group = QGroupBox("📋 概要")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QGridLayout()

        self.production_name_label = QLabel("（番組を選択してください）")
        self.production_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.production_name_label, 0, 0, 1, 4)

        self.total_amount_label = QLabel("総費用額: ¥0")
        self.total_amount_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self.total_amount_label, 1, 0)

        self.item_count_label = QLabel("費用項目数: 0件")
        layout.addWidget(self.item_count_label, 1, 1)

        self.unpaid_label = QLabel("未払い: 0件 (¥0)")
        self.unpaid_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(self.unpaid_label, 2, 0)

        self.paid_label = QLabel("支払済: 0件 (¥0)")
        self.paid_label.setStyleSheet("color: #388e3c;")
        layout.addWidget(self.paid_label, 2, 1)

        self.pending_label = QLabel("金額未定: 0件")
        self.pending_label.setStyleSheet("color: #f57c00;")
        layout.addWidget(self.pending_label, 2, 2)

        group.setLayout(layout)
        return group

    def load_production_list(self):
        """番組一覧を読み込み"""
        search_term = self.search_input.text()
        sort_text = self.sort_combo.currentText()
        type_text = self.type_filter.currentText()

        # ソート基準を決定
        if sort_text == "未払い件数順":
            sort_by = 'unpaid_count'
        elif sort_text == "費用項目数順":
            sort_by = 'item_count'
        elif sort_text == "月額平均順":
            sort_by = 'monthly_average'
        else:
            sort_by = 'total_amount'

        # 番組タイプフィルタ
        production_type_filter = None if type_text == "全て" else type_text

        # データ取得
        productions = self.db.get_production_expense_summary(search_term, sort_by, production_type_filter)

        self.production_table.setRowCount(len(productions))

        for row, prod in enumerate(productions):
            # データ構造: (production_id, production_name, production_type, item_count, total_amount,
            #            unpaid_count, unpaid_amount, paid_count, paid_amount, pending_count,
            #            month_count, monthly_average)
            production_id = prod[0]
            production_name = prod[1]
            production_type = prod[2] or "未設定"
            item_count = prod[3]
            total_amount = prod[4] or 0
            unpaid_count = prod[5]
            paid_count = prod[7]
            month_count = prod[10]
            monthly_average = prod[11] or 0

            # テーブルにデータを設定（列順: 番組名、種別、総費用額、未払い、支払済）
            name_item = QTableWidgetItem(production_name)
            name_item.setData(Qt.UserRole, production_id)
            self.production_table.setItem(row, 0, name_item)

            self.production_table.setItem(row, 1, QTableWidgetItem(production_type))
            self.production_table.setItem(row, 2, QTableWidgetItem(f"¥{int(total_amount):,}"))
            self.production_table.setItem(row, 3, QTableWidgetItem(f"{unpaid_count}件"))
            self.production_table.setItem(row, 4, QTableWidgetItem(f"{paid_count}件"))

            # 番組タイプに応じて行の色を変更
            if production_type == "レギュラー" or production_type == "コーナー":
                row_color = QColor(230, 240, 255) if unpaid_count > 0 else None  # 青系
            elif production_type == "イベント" or production_type == "特番":
                row_color = QColor(255, 250, 230) if unpaid_count > 0 else None  # 黄系
            else:
                row_color = QColor(255, 243, 224) if unpaid_count > 0 else None  # オレンジ系

            if row_color:
                for col in range(self.production_table.columnCount()):
                    item = self.production_table.item(row, col)
                    if item:
                        item.setBackground(row_color)

    def on_production_selected(self):
        """番組が選択されたときの処理"""
        selected_items = self.production_table.selectedItems()
        if not selected_items:
            return

        # 選択された番組のIDを取得
        production_id = selected_items[0].data(Qt.UserRole)
        self.current_production_id = production_id

        # 詳細を読み込み
        self.load_production_detail(production_id)

        # 月別集計ボタンを有効化
        self.monthly_button.setEnabled(True)

    def load_production_detail(self, production_id):
        """番組の詳細を読み込み"""
        # サマリー情報を取得
        productions = self.db.get_production_expense_summary()
        production_data = next((p for p in productions if p[0] == production_id), None)

        if not production_data:
            return

        # データ構造: (production_id, production_name, production_type, item_count, total_amount,
        #            unpaid_count, unpaid_amount, paid_count, paid_amount, pending_count,
        #            month_count, monthly_average)
        production_name = production_data[1]
        production_type = production_data[2]
        item_count = production_data[3]
        total_amount = production_data[4] or 0
        unpaid_count = production_data[5]
        unpaid_amount = production_data[6] or 0
        paid_count = production_data[7]
        paid_amount = production_data[8] or 0
        pending_count = production_data[9]

        # サマリーを更新
        self.production_name_label.setText(f"番組: {production_name}")
        self.total_amount_label.setText(f"総費用額: ¥{int(total_amount):,}")
        self.item_count_label.setText(f"費用項目数: {item_count}件")
        self.unpaid_label.setText(f"未払い: {unpaid_count}件 (¥{int(unpaid_amount):,})")
        self.paid_label.setText(f"支払済: {paid_count}件 (¥{int(paid_amount):,})")
        self.pending_label.setText(f"金額未定: {pending_count}件")

        # レギュラー番組は月別表示、それ以外は全件表示
        if production_type == "レギュラー" or production_type == "コーナー":
            self.load_monthly_grouped_details(production_id)
        else:
            self.load_all_details(production_id)

    def load_monthly_grouped_details(self, production_id):
        """月別にグループ化して詳細を表示（レギュラー番組用）"""
        # 月別集計を取得
        monthly_summary = self.db.get_production_expense_monthly_summary(production_id)

        # テーブルをクリア
        self.detail_table.setRowCount(0)

        row_index = 0
        for month_data in monthly_summary:
            # データ構造: (month, item_count, total_amount, unpaid_count, paid_count)
            month = month_data[0]
            month_item_count = month_data[1]
            month_total = month_data[2] or 0
            month_unpaid_count = month_data[3]
            month_paid_count = month_data[4]

            # 月ヘッダー行を追加
            self.detail_table.insertRow(row_index)
            month_header = f"📅 {month} ({month_item_count}件 / ¥{int(month_total):,})"
            header_item = QTableWidgetItem(month_header)
            header_item.setBackground(QColor(230, 240, 255))  # 青系
            self.detail_table.setItem(row_index, 0, header_item)

            # ヘッダー行は全列を結合
            self.detail_table.setSpan(row_index, 0, 1, 7)
            row_index += 1

            # その月の費用項目を取得
            month_details = self.db.get_production_expense_details_by_month(production_id, month)

            for detail in month_details:
                self.detail_table.insertRow(row_index)
                self._populate_detail_row(row_index, detail)
                row_index += 1

        # 列幅を内容に合わせて自動調整
        self.detail_table.resizeColumnToContents(0)  # 実施日
        self.detail_table.resizeColumnToContents(5)  # 支払予定日

    def load_all_details(self, production_id):
        """全費用項目を表示（イベント・特番用）"""
        # 費用項目詳細を取得
        details = self.db.get_production_expense_details(production_id)

        self.detail_table.setRowCount(len(details))

        for row, detail in enumerate(details):
            self._populate_detail_row(row, detail)

        # 列幅を内容に合わせて自動調整
        self.detail_table.resizeColumnToContents(0)  # 実施日
        self.detail_table.resizeColumnToContents(5)  # 支払予定日

    def _populate_detail_row(self, row, detail):
        """詳細テーブルの1行にデータを設定する共通ヘルパーメソッド"""
        from datetime import datetime

        # データ構造: (id, partner_name, item_name, amount, implementation_date,
        #            expected_payment_date, payment_status, status, notes, amount_pending,
        #            work_type, corner_name, corner_id)
        item_id = detail[0]
        partner_name = detail[1] or ""
        item_name = detail[2] or ""
        amount = detail[3] or 0
        implementation_date = detail[4] or ""
        expected_payment_date = detail[5] or ""
        payment_status = detail[6] or "未払い"
        status = detail[7] or ""
        notes = detail[8] or ""
        amount_pending = detail[9] if len(detail) > 9 else 0
        corner_name = detail[11] if len(detail) > 11 else ""
        corner_id = detail[12] if len(detail) > 12 else None

        # 金額のフォーマット
        if amount_pending == 1:
            amount_text = "未定"
        else:
            amount_text = f"¥{int(amount):,}"

        # コーナー名の設定（corner_idがある場合のみ表示）
        corner_display = corner_name if corner_id else ""

        # 日付パースと期限チェック
        days_until = None
        if expected_payment_date:
            try:
                payment_date = datetime.strptime(expected_payment_date, '%Y-%m-%d')
                days_until = (payment_date.date() - datetime.now().date()).days
            except:
                pass

        # テーブルにデータを設定（列順: 実施日、項目名、コーナー、金額、取引先、支払予定日、支払状態）
        implementation_date_item = QTableWidgetItem(implementation_date)
        implementation_date_item.setData(Qt.UserRole, item_id)  # expense_item_idを保存
        self.detail_table.setItem(row, 0, implementation_date_item)
        self.detail_table.setItem(row, 1, QTableWidgetItem(item_name))
        self.detail_table.setItem(row, 2, QTableWidgetItem(corner_display))
        self.detail_table.setItem(row, 3, QTableWidgetItem(amount_text))
        self.detail_table.setItem(row, 4, QTableWidgetItem(partner_name))
        self.detail_table.setItem(row, 5, QTableWidgetItem(expected_payment_date))
        self.detail_table.setItem(row, 6, QTableWidgetItem(payment_status))

        # 行の背景色を決定（優先順位: 期限超過 > 支払済 > 金額未定 > 支払間近）
        row_color = None

        # 最優先: 期限超過（未払い＋支払予定日が過去）
        if payment_status == "未払い" and days_until is not None and days_until < 0:
            row_color = QColor(255, 200, 200)  # 濃い赤（期限超過）

        # 支払済み
        if not row_color and payment_status == "支払済":
            row_color = QColor(220, 255, 220)  # 緑

        # 金額未定
        if not row_color and amount_pending == 1:
            row_color = QColor(255, 243, 224)  # 薄いオレンジ（金額未定）

        # 支払間近（7日以内）
        if not row_color and payment_status == "未払い" and days_until is not None and 0 <= days_until <= 7:
            row_color = QColor(255, 255, 200)  # 黄（間近）

        if row_color:
            for col in range(self.detail_table.columnCount()):
                item = self.detail_table.item(row, col)
                if item:
                    item.setBackground(row_color)

    def show_monthly_summary(self):
        """月別集計を表示"""
        if not self.current_production_id:
            return

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem

        # ダイアログを作成
        dialog = QDialog(self)
        dialog.setWindowTitle("月別費用集計")
        dialog.resize(600, 400)

        layout = QVBoxLayout()

        # 月別集計テーブル
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "月", "費用項目数", "総費用額", "未払い", "支払済"
        ])

        # データ取得
        monthly_data = self.db.get_production_expense_monthly_summary(self.current_production_id)

        table.setRowCount(len(monthly_data))

        for row, data in enumerate(monthly_data):
            month = data[0]
            item_count = data[1]
            total_amount = data[2] or 0
            unpaid_count = data[3]
            paid_count = data[4]

            table.setItem(row, 0, QTableWidgetItem(month))
            table.setItem(row, 1, QTableWidgetItem(str(item_count)))
            table.setItem(row, 2, QTableWidgetItem(f"¥{int(total_amount):,}"))
            table.setItem(row, 3, QTableWidgetItem(f"{unpaid_count}件"))
            table.setItem(row, 4, QTableWidgetItem(f"{paid_count}件"))

        # 列幅の設定
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec_()

    def on_production_double_clicked(self, item):
        """番組一覧のダブルクリックイベント - 番組編集ダイアログを開く"""
        # 選択された番組のIDを取得
        row = item.row()
        production_id_item = self.production_table.item(row, 0)
        if production_id_item:
            production_id = production_id_item.data(Qt.UserRole)
            if production_id:
                # 番組編集ダイアログを開く
                from order_management.ui.production_edit_dialog import ProductionEditDialog

                # 番組情報を取得
                production = self.db.get_production_by_id(production_id)
                if production:
                    dialog = ProductionEditDialog(self, production)
                    if dialog.exec_():
                        # 編集後、リストを再読み込み
                        self.load_production_list()
                        # 同じ番組を再選択して詳細を更新
                        if self.current_production_id == production_id:
                            self.load_production_detail(production_id)

    def on_expense_item_double_clicked(self, item):
        """費用項目のダブルクリックイベント - 費用項目編集ダイアログを開く"""
        # 月別ヘッダー行の場合はスキップ
        row = item.row()
        first_col_item = self.detail_table.item(row, 0)

        # ヘッダー行かどうかをチェック（スパンされている場合）
        if self.detail_table.columnSpan(row, 0) > 1:
            return  # 月ヘッダー行なのでスキップ

        # 実施日セルからexpense_item_idを取得（UserRoleに保存されていると仮定）
        # もしUserRoleに保存されていない場合は、他の方法でIDを取得
        # ここでは簡易的にテーブルの最初の列（実施日）からテキストを使ってIDを推定する代わりに
        # _populate_detail_rowメソッドでIDをUserRoleに保存するように修正が必要

        # 暫定的に、detail_tableの各行の最初のセルにexpense_item_idを保存するように変更
        expense_item_id = first_col_item.data(Qt.UserRole) if first_col_item else None

        if expense_item_id:
            # 費用項目編集ダイアログを開く
            from order_management.ui.expense_item_edit_dialog import ExpenseItemEditDialog

            dialog = ExpenseItemEditDialog(self, expense_item_id)
            if dialog.exec_():
                # 編集後、番組一覧と詳細を再読み込み
                self.load_production_list()
                if self.current_production_id:
                    self.load_production_detail(self.current_production_id)
