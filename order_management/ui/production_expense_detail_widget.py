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
        self.production_table.setColumnCount(7)
        self.production_table.setHorizontalHeaderLabels([
            "番組名", "種別", "総費用額", "月額平均", "項目数", "未払い", "支払済"
        ])

        # 列幅の設定
        header = self.production_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 種別
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 総費用額
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 月額平均
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 項目数
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 未払い
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 支払済

        self.production_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.production_table.setSelectionMode(QTableWidget.SingleSelection)
        self.production_table.itemSelectionChanged.connect(self.on_production_selected)

        layout.addWidget(self.production_table)

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
        self.detail_table.setColumnCount(9)
        self.detail_table.setHorizontalHeaderLabels([
            "ID", "取引先", "項目名", "金額", "実施日",
            "支払予定日", "支払状態", "状態", "備考"
        ])

        # 列幅の設定
        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 取引先
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 項目名
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 金額
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 実施日
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 支払予定日
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 支払状態
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 状態
        header.setSectionResizeMode(8, QHeaderView.Stretch)  # 備考

        self.detail_table.setAlternatingRowColors(True)

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

            # テーブルにデータを設定
            name_item = QTableWidgetItem(production_name)
            name_item.setData(Qt.UserRole, production_id)
            self.production_table.setItem(row, 0, name_item)

            self.production_table.setItem(row, 1, QTableWidgetItem(production_type))
            self.production_table.setItem(row, 2, QTableWidgetItem(f"¥{int(total_amount):,}"))

            # レギュラー番組は月額平均を強調、イベントは総額を強調
            if production_type == "レギュラー" or production_type == "コーナー":
                self.production_table.setItem(row, 3, QTableWidgetItem(f"¥{int(monthly_average):,}/月"))
            elif production_type == "イベント" or production_type == "特番":
                self.production_table.setItem(row, 3, QTableWidgetItem(f"({month_count}ヶ月)"))
            else:
                self.production_table.setItem(row, 3, QTableWidgetItem(f"¥{int(monthly_average):,}"))

            self.production_table.setItem(row, 4, QTableWidgetItem(str(item_count)))
            self.production_table.setItem(row, 5, QTableWidgetItem(f"{unpaid_count}件"))
            self.production_table.setItem(row, 6, QTableWidgetItem(f"{paid_count}件"))

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

        if production_data:
            # データ構造: (production_id, production_name, production_type, item_count, total_amount,
            #            unpaid_count, unpaid_amount, paid_count, paid_amount, pending_count,
            #            month_count, monthly_average)
            production_name = production_data[1]
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

        # 費用項目詳細を取得
        details = self.db.get_production_expense_details(production_id)

        self.detail_table.setRowCount(len(details))

        for row, detail in enumerate(details):
            # データ構造: (id, partner_name, item_name, amount, implementation_date,
            #            expected_payment_date, payment_status, status, notes, amount_pending, work_type)
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

            # 金額のフォーマット
            if amount_pending == 1:
                amount_text = "未定"
            else:
                amount_text = f"¥{int(amount):,}"

            # テーブルにデータを設定
            self.detail_table.setItem(row, 0, QTableWidgetItem(str(item_id)))
            self.detail_table.setItem(row, 1, QTableWidgetItem(partner_name))
            self.detail_table.setItem(row, 2, QTableWidgetItem(item_name))
            self.detail_table.setItem(row, 3, QTableWidgetItem(amount_text))
            self.detail_table.setItem(row, 4, QTableWidgetItem(implementation_date))
            self.detail_table.setItem(row, 5, QTableWidgetItem(expected_payment_date))
            self.detail_table.setItem(row, 6, QTableWidgetItem(payment_status))
            self.detail_table.setItem(row, 7, QTableWidgetItem(status))
            self.detail_table.setItem(row, 8, QTableWidgetItem(notes))

            # 支払い状態に応じて行の色を変更
            if payment_status == "支払済":
                row_color = QColor(220, 255, 220)  # 緑
            elif amount_pending == 1:
                row_color = QColor(255, 243, 224)  # 薄いオレンジ
            else:
                row_color = None

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
