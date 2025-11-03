"""支払い・発注チェックタブ

発注マスターから月次支払予定を生成し、実績と照合して
不足している項目（発注書類、受領確認、支払実績）を一覧表示します。
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel,
                             QRadioButton, QButtonGroup, QLineEdit, QHeaderView,
                             QMessageBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database import DatabaseManager


class PaymentOrderCheckTab(QWidget):
    """支払い・発注チェックタブ"""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.check_data = []  # チェック結果データを保持
        self.init_ui()

        # 現在の月をデフォルトで設定
        current_month = datetime.now().strftime("%Y-%m")
        index = self.month_combo.findText(current_month)
        if index >= 0:
            self.month_combo.setCurrentIndex(index)

        self.load_data()

    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout()

        # === 上部: フィルタエリア ===
        filter_layout = QHBoxLayout()

        # 年月選択
        month_label = QLabel("対象月:")
        filter_layout.addWidget(month_label)

        self.month_combo = QComboBox()
        self.populate_month_combo()
        self.month_combo.currentTextChanged.connect(self.on_month_changed)
        filter_layout.addWidget(self.month_combo)

        filter_layout.addSpacing(20)

        # フィルタラジオボタン
        filter_label = QLabel("表示フィルタ:")
        filter_layout.addWidget(filter_label)

        self.filter_group = QButtonGroup()
        self.rb_all = QRadioButton("全て表示")
        self.rb_problem = QRadioButton("問題あり")
        self.rb_completed = QRadioButton("完了済み")

        self.rb_all.setChecked(True)
        self.filter_group.addButton(self.rb_all)
        self.filter_group.addButton(self.rb_problem)
        self.filter_group.addButton(self.rb_completed)

        self.rb_all.toggled.connect(self.apply_filter)
        self.rb_problem.toggled.connect(self.apply_filter)
        self.rb_completed.toggled.connect(self.apply_filter)

        filter_layout.addWidget(self.rb_all)
        filter_layout.addWidget(self.rb_problem)
        filter_layout.addWidget(self.rb_completed)

        filter_layout.addSpacing(20)

        # 検索ボックス
        search_label = QLabel("検索:")
        filter_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("取引先名または費用項目で検索")
        self.search_input.textChanged.connect(self.apply_filter)
        self.search_input.setMinimumWidth(250)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        # 再読み込みボタン
        reload_btn = QPushButton("🔄 再チェック")
        reload_btn.clicked.connect(self.load_data)
        reload_btn.setMinimumWidth(100)
        filter_layout.addWidget(reload_btn)

        layout.addLayout(filter_layout)

        # === 中央: テーブル ===
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "費用項目", "取引先", "番組名", "年月", "予定金額", "実績金額",
            "①発注", "②書面", "③受領", "④予定", "⑤支払", "状態"
        ])

        # カラム幅の設定
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 費用項目
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 取引先
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 番組名
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 年月
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 予定金額
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 実績金額
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # ①発注
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # ②書面
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # ③受領
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # ④予定
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # ⑤支払
        header.setSectionResizeMode(11, QHeaderView.ResizeToContents)  # 状態

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # 編集不可

        layout.addWidget(self.table)

        # === 下部: 統計情報 ===
        stats_layout = QHBoxLayout()

        self.stats_label = QLabel("全体: 0件 | 完了: 0件 | 問題あり: 0件")
        self.stats_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)

        stats_layout.addStretch()

        layout.addLayout(stats_layout)

        self.setLayout(layout)

    def populate_month_combo(self):
        """年月コンボボックスを作成（直近12ヶ月）"""
        current = datetime.now()

        for i in range(12):
            month = current - relativedelta(months=i)
            month_str = month.strftime("%Y-%m")
            self.month_combo.addItem(month_str)

    def on_month_changed(self, month_str):
        """年月が変更されたときのハンドラ"""
        if month_str:
            self.load_data()

    def load_data(self):
        """データを読み込み"""
        target_month = self.month_combo.currentText()
        if not target_month:
            return

        self.check_data = self.db.check_payments_against_schedule(target_month)
        self.apply_filter()
        self.update_statistics()

    def apply_filter(self):
        """フィルタを適用してテーブルを更新"""
        filter_type = None
        if self.rb_problem.isChecked():
            filter_type = "problem"
        elif self.rb_completed.isChecked():
            filter_type = "completed"

        search_term = self.search_input.text().lower()

        # フィルタリング
        filtered_data = []
        for item in self.check_data:
            # フィルタタイプチェック
            if filter_type == "problem" and item['status_color'] == "green":
                continue
            if filter_type == "completed" and item['status_color'] != "green":
                continue

            # 検索キーワードチェック
            if search_term:
                if (search_term not in item['partner_name'].lower() and
                    search_term not in item['item_name'].lower()):
                    continue

            filtered_data.append(item)

        # テーブル更新
        self.populate_table(filtered_data)

    def populate_table(self, data):
        """テーブルにデータを表示"""
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            # 費用項目
            self.table.setItem(row, 0, QTableWidgetItem(item['item_name']))

            # 取引先
            self.table.setItem(row, 1, QTableWidgetItem(item['partner_name']))

            # 番組名
            self.table.setItem(row, 2, QTableWidgetItem(item['program_name']))

            # 年月
            self.table.setItem(row, 3, QTableWidgetItem(item['year_month']))

            # 予定金額
            scheduled_amount = f"{int(item['scheduled_amount']):,}円" if item['scheduled_amount'] else "-"
            self.table.setItem(row, 4, QTableWidgetItem(scheduled_amount))

            # 実績金額
            actual_amount = f"{int(item['actual_amount']):,}円" if item['actual_amount'] else "-"
            self.table.setItem(row, 5, QTableWidgetItem(actual_amount))

            # ①発注
            has_order = item['has_order']
            order_item = QTableWidgetItem("✓" if has_order else "✗")
            order_item.setTextAlignment(Qt.AlignCenter)
            if has_order:
                order_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                order_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            order_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒
            self.table.setItem(row, 6, order_item)

            # ②書面（PDF配布済/メール送信済）
            receipt_ok = item['receipt_status'] == "✓"
            document_item = QTableWidgetItem("✓" if receipt_ok else "✗")
            document_item.setTextAlignment(Qt.AlignCenter)
            if receipt_ok:
                document_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                document_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            document_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒
            self.table.setItem(row, 7, document_item)

            # ③受領（現在は②と同じ）
            receipt_item = QTableWidgetItem("✓" if receipt_ok else "✗")
            receipt_item.setTextAlignment(Qt.AlignCenter)
            if receipt_ok:
                receipt_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                receipt_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            receipt_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒
            self.table.setItem(row, 8, receipt_item)

            # ④予定（発注あり=予定入）
            schedule_item = QTableWidgetItem("✓" if has_order else "✗")
            schedule_item.setTextAlignment(Qt.AlignCenter)
            if has_order:
                schedule_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                schedule_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            schedule_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒
            self.table.setItem(row, 9, schedule_item)

            # ⑤支払
            payment_ok = item['payment_status'] == "✓"
            payment_item = QTableWidgetItem("✓" if payment_ok else "✗")
            payment_item.setTextAlignment(Qt.AlignCenter)
            if payment_ok:
                payment_item.setBackground(QColor(200, 255, 200))  # 薄い緑
            else:
                payment_item.setBackground(QColor(255, 200, 200))  # 薄い赤
            payment_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黒
            self.table.setItem(row, 10, payment_item)

            # 状態（色で表示）
            status_color = item['status_color']
            if status_color == "red":
                status_text = "🔴"
            elif status_color == "yellow":
                status_text = "🟡"
            else:
                status_text = "🟢"

            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 11, status_item)

    def update_statistics(self):
        """統計情報を更新"""
        total = len(self.check_data)
        completed = sum(1 for item in self.check_data if item['status_color'] == "green")
        problem = total - completed

        self.stats_label.setText(
            f"全体: {total}件 | 完了: {completed}件 | 問題あり: {problem}件"
        )
