"""番組・イベントタイムラインウィジェット

番組・イベントを時系列に並べ、ツリー構造で費用項目を表示します。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QDateEdit, QComboBox, QFileDialog, QMessageBox,
    QHeaderView, QMenu, QAction
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QBrush
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import csv

from order_management.database_manager import OrderManagementDB
from order_management.ui.production_edit_dialog import ProductionEditDialog
from order_management.ui.expense_edit_dialog import ExpenseEditDialog


class ProductionTimelineWidget(QWidget):
    """番組・イベントタイムラインウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self._setup_ui()
        self.load_timeline()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ===== フィルターエリア =====
        filter_group_layout = QVBoxLayout()

        # 1行目: 期間フィルター
        date_filter_layout = QHBoxLayout()
        date_filter_layout.addWidget(QLabel("期間:"))

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-3))  # 3ヶ月前から
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_filter_layout.addWidget(self.start_date_edit)

        date_filter_layout.addWidget(QLabel("〜"))

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addMonths(3))  # 3ヶ月後まで
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        date_filter_layout.addWidget(self.end_date_edit)

        date_filter_layout.addStretch()
        filter_group_layout.addLayout(date_filter_layout)

        # 2行目: 種別・番組フィルター
        category_filter_layout = QHBoxLayout()
        category_filter_layout.addWidget(QLabel("種別:"))

        self.type_filter = QComboBox()
        self.type_filter.addItem("全て", "")
        self.type_filter.addItem("レギュラー番組", "レギュラー番組")
        self.type_filter.addItem("特別番組", "特別番組")
        self.type_filter.addItem("イベント", "イベント")
        self.type_filter.addItem("公開放送", "公開放送")
        self.type_filter.addItem("公開収録", "公開収録")
        self.type_filter.addItem("特別企画", "特別企画")
        category_filter_layout.addWidget(self.type_filter)

        category_filter_layout.addWidget(QLabel("  番組:"))

        self.program_filter = QComboBox()
        self._load_programs()
        category_filter_layout.addWidget(self.program_filter)

        category_filter_layout.addStretch()
        filter_group_layout.addLayout(category_filter_layout)

        # 3行目: アクションボタン
        action_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("更新")
        self.refresh_btn.clicked.connect(self.load_timeline)
        action_layout.addWidget(self.refresh_btn)

        self.csv_export_btn = QPushButton("CSV出力")
        self.csv_export_btn.clicked.connect(self.export_to_csv)
        action_layout.addWidget(self.csv_export_btn)

        self.print_btn = QPushButton("印刷")
        self.print_btn.clicked.connect(self.print_timeline)
        action_layout.addWidget(self.print_btn)

        self.expand_all_btn = QPushButton("全て展開")
        self.expand_all_btn.clicked.connect(self.expand_all)
        action_layout.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("全て折りたたみ")
        self.collapse_all_btn.clicked.connect(self.collapse_all)
        action_layout.addWidget(self.collapse_all_btn)

        action_layout.addStretch()
        filter_group_layout.addLayout(action_layout)

        layout.addLayout(filter_group_layout)

        # ===== ツリーウィジェット =====
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            "実施日/支払予定日", "番組・イベント名/項目名", "種別", "金額（円）", "ステータス"
        ])

        # カラム幅設定
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        # ソート有効化
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.AscendingOrder)  # デフォルトは古い順

        # ダブルクリックイベント
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        # 右クリックメニュー
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.tree)

        # ===== ステータスバー =====
        self.status_label = QLabel("番組・イベント: 0件 | 総実績: 0円")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

    def _load_programs(self):
        """番組一覧を読み込み"""
        self.program_filter.clear()
        self.program_filter.addItem("全て", None)

        productions = self.db.get_productions()
        for production in productions:
            # production: (id, name, description, production_type, start_date, end_date,
            #             start_time, end_time, broadcast_time, broadcast_days, status,
            #             parent_production_id)
            display_text = production[1]
            if production[3]:  # production_type
                display_text += f" ({production[3]})"
            self.program_filter.addItem(display_text, production[0])

    def _expand_regular_production_by_month(self, production, start_date_str, end_date_str):
        """レギュラー番組を月ごとに展開

        Args:
            production: 制作物データ
            start_date_str: フィルター開始日 (YYYY-MM-DD)
            end_date_str: フィルター終了日 (YYYY-MM-DD)

        Returns:
            List[(year_month, production, broadcast_count)]: 月ごとの展開リスト
        """
        production_id = production[0]
        production_start = production[4]  # start_date
        production_end = production[5]    # end_date
        broadcast_days_str = production[9]  # broadcast_days (例: "月,水,金")

        if not broadcast_days_str:
            # 放送曜日が設定されていない場合は展開しない
            return [(start_date_str[:7], production, 0)]

        # 放送曜日をパース
        broadcast_days = [day.strip() for day in broadcast_days_str.split(',')]
        day_map = {'月': 0, '火': 1, '水': 2, '木': 3, '金': 4, '土': 5, '日': 6}
        broadcast_weekdays = [day_map[day] for day in broadcast_days if day in day_map]

        # フィルター期間と番組期間の重複部分を計算
        filter_start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        filter_end = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        prog_start = datetime.strptime(production_start, "%Y-%m-%d").date() if production_start else filter_start
        prog_end = datetime.strptime(production_end, "%Y-%m-%d").date() if production_end else filter_end

        actual_start = max(filter_start, prog_start)
        actual_end = min(filter_end, prog_end)

        if actual_start > actual_end:
            return []

        # 月ごとに放送回数を計算
        monthly_expansions = []
        current = actual_start.replace(day=1)  # 月初に設定

        while current <= actual_end:
            # その月の最終日を取得
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_end = current.replace(day=last_day)

            # その月の実際の放送期間
            month_start = max(actual_start, current)
            month_end_actual = min(actual_end, month_end)

            # 放送回数を計算
            broadcast_count = 0
            check_date = month_start
            while check_date <= month_end_actual:
                if check_date.weekday() in broadcast_weekdays:
                    broadcast_count += 1
                check_date += timedelta(days=1)

            if broadcast_count > 0:
                year_month = f"{current.year:04d}-{current.month:02d}"
                monthly_expansions.append((year_month, production, broadcast_count))

            # 次の月へ
            current = (current + relativedelta(months=1)).replace(day=1)

        return monthly_expansions

    def _calculate_total_broadcasts(self, production):
        """レギュラー番組の全期間の放送回数を計算

        Args:
            production: 制作物データ

        Returns:
            int: 全期間の放送回数
        """
        production_start = production[4]  # start_date
        production_end = production[5]    # end_date
        broadcast_days_str = production[9]  # broadcast_days

        if not production_start or not broadcast_days_str:
            return 0

        # 放送曜日をパース
        broadcast_days = [day.strip() for day in broadcast_days_str.split(',')]
        day_map = {'月': 0, '火': 1, '水': 2, '木': 3, '金': 4, '土': 5, '日': 6}
        broadcast_weekdays = [day_map[day] for day in broadcast_days if day in day_map]

        prog_start = datetime.strptime(production_start, "%Y-%m-%d").date()
        prog_end = datetime.strptime(production_end, "%Y-%m-%d").date() if production_end else (prog_start + timedelta(days=365))

        # 全期間の放送回数を計算
        total_count = 0
        check_date = prog_start
        while check_date <= prog_end:
            if check_date.weekday() in broadcast_weekdays:
                total_count += 1
            check_date += timedelta(days=1)

        return total_count

    def load_timeline(self):
        """タイムラインを読み込み"""
        self.tree.clear()
        self.tree.setSortingEnabled(False)  # ソートを一時無効化

        # フィルター条件取得
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        production_type = self.type_filter.currentData()
        program_id = self.program_filter.currentData()

        # 番組・イベント取得（全体から取得し、後でフィルタリング）
        productions = self.db.get_productions_with_hierarchy(
            search_term="",
            production_type=production_type or "",
            include_children=True
        )

        # レギュラー番組を月ごとに展開
        expanded_items = []
        for production in productions:
            # production: (id, name, description, production_type, start_date, end_date,
            #             start_time, end_time, broadcast_time, broadcast_days, status,
            #             parent_production_id, parent_name)
            production_type_val = production[3]

            # レギュラー番組の場合は月ごとに展開
            if production_type_val == "レギュラー番組":
                monthly_items = self._expand_regular_production_by_month(production, start_date, end_date)
                expanded_items.extend(monthly_items)
            else:
                # 単発番組・イベントは通常通り
                start_date_val = production[4]  # start_date

                # 日付フィルター
                if start_date_val and (start_date_val < start_date or start_date_val > end_date):
                    continue

                year_month = start_date_val[:7] if start_date_val else start_date[:7]
                expanded_items.append((year_month, production, 1))

        # 統計用変数
        total_amount = 0
        item_count = 0

        # ツリー構築
        for year_month, production, broadcast_count in expanded_items:
            production_id = production[0]
            production_name = production[1]
            production_type_str = production[3] or "イベント"
            start_date_display = production[4] or ""

            # 実績合計取得
            summary = self.db.get_production_summary(production_id)
            production_total = summary['actual']

            # レギュラー番組の場合、月単位で金額を按分
            if production_type_str == "レギュラー番組" and broadcast_count > 0:
                # 全期間の放送回数を計算（簡易版：年間として計算）
                total_broadcasts = self._calculate_total_broadcasts(production)
                if total_broadcasts > 0:
                    monthly_amount = (production_total / total_broadcasts) * broadcast_count
                else:
                    monthly_amount = production_total

                display_name = f"{production_name}（全{broadcast_count}回）"
                display_date = year_month
            else:
                monthly_amount = production_total
                display_name = production_name
                display_date = start_date_display

            total_amount += monthly_amount
            item_count += 1

            # 番組・イベントノード作成
            production_item = QTreeWidgetItem([
                display_date,
                display_name,
                production_type_str,
                f"{monthly_amount:,.0f}",
                ""
            ])

            # 番組・イベントノードのスタイル
            font = QFont()
            font.setBold(True)
            for col in range(5):
                production_item.setFont(col, font)
                production_item.setBackground(col, QBrush(QColor(240, 240, 240)))
                production_item.setForeground(col, QBrush(QColor(0, 0, 0)))  # 黒色

            # データを保存（編集用）
            production_item.setData(0, Qt.UserRole, ("production", production_id))

            # 費用項目取得
            expenses = self.db.get_expenses_by_production(production_id)

            for expense in expenses:
                # expense: (id, production_id, item_name, amount, supplier_id,
                #          contact_person, status, order_number,
                #          implementation_date, invoice_received_date)
                expense_id = expense[0]
                item_name = expense[2]
                amount = expense[3]
                status = expense[6] or ""

                # 支払予定日を取得（詳細情報が必要）
                expense_detail = self.db.get_expense_order_by_id(expense_id)
                payment_scheduled_date = ""
                if expense_detail and expense_detail[11]:
                    payment_scheduled_date = expense_detail[11]

                # レギュラー番組の場合、支払予定日がその月に含まれるもののみ表示
                if production_type_str == "レギュラー番組":
                    if not payment_scheduled_date or not payment_scheduled_date.startswith(year_month):
                        continue

                # 費用項目ノード作成
                expense_item = QTreeWidgetItem([
                    payment_scheduled_date,
                    item_name,
                    "",
                    f"{amount:,.0f}",
                    status
                ])

                # デフォルト文字色を黒に設定
                for col in range(5):
                    expense_item.setForeground(col, QBrush(QColor(0, 0, 0)))

                # ステータスに応じた色分け
                if status == "支払済":
                    expense_item.setForeground(4, QBrush(QColor(0, 128, 0)))  # 緑
                elif status == "未払" or status == "発注済":
                    expense_item.setForeground(4, QBrush(QColor(255, 0, 0)))  # 赤
                elif status == "請求書待ち":
                    expense_item.setForeground(4, QBrush(QColor(255, 165, 0)))  # オレンジ

                # データを保存（編集用）
                expense_item.setData(0, Qt.UserRole, ("expense", expense_id))

                production_item.addChild(expense_item)

            self.tree.addTopLevelItem(production_item)

        # ソートを再有効化
        self.tree.setSortingEnabled(True)

        # 全て展開
        self.tree.expandAll()

        # ステータス更新
        self.status_label.setText(
            f"番組・イベント: {item_count}件 | 総実績: {total_amount:,.0f}円"
        )

    def on_item_double_clicked(self, item, column):
        """アイテムダブルクリック時の処理"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        data_type, data_id = data

        if data_type == "production":
            # 番組・イベント編集
            production = self.db.get_production_by_id(data_id)
            if production:
                dialog = ProductionEditDialog(self, production=production)
                if dialog.exec_():
                    self.load_timeline()

        elif data_type == "expense":
            # 費用項目編集
            dialog = ExpenseEditDialog(self, expense_id=data_id)
            if dialog.exec_():
                self.load_timeline()

    def show_context_menu(self, position):
        """右クリックメニュー表示"""
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        if not data:
            return

        data_type, data_id = data

        menu = QMenu(self)

        # 編集アクション
        edit_action = QAction("編集", self)
        edit_action.triggered.connect(lambda: self.on_item_double_clicked(item, 0))
        menu.addAction(edit_action)

        menu.addSeparator()

        # 削除アクション
        delete_action = QAction("削除", self)
        delete_action.triggered.connect(lambda: self.delete_item(data_type, data_id))
        menu.addAction(delete_action)

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def delete_item(self, data_type, data_id):
        """アイテム削除"""
        reply = QMessageBox.question(
            self, "確認",
            f"この{'番組・イベント' if data_type == 'production' else '費用項目'}を削除してもよろしいですか？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if data_type == "production":
                    self.db.delete_production(data_id)
                    QMessageBox.information(self, "成功", "番組・イベントを削除しました")
                elif data_type == "expense":
                    self.db.delete_expense_order(data_id)
                    QMessageBox.information(self, "成功", "費用項目を削除しました")

                self.load_timeline()
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")

    def expand_all(self):
        """全て展開"""
        self.tree.expandAll()

    def collapse_all(self):
        """全て折りたたみ"""
        self.tree.collapseAll()

    def export_to_csv(self):
        """CSV出力"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "CSV出力", f"production_timeline_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow([
                    "実施日/支払予定日", "番組・イベント名/項目名",
                    "種別", "金額（円）", "ステータス"
                ])

                # データ
                root = self.tree.invisibleRootItem()
                for i in range(root.childCount()):
                    production_item = root.child(i)

                    # 番組・イベント行
                    writer.writerow([
                        production_item.text(0),
                        production_item.text(1),
                        production_item.text(2),
                        production_item.text(3),
                        production_item.text(4)
                    ])

                    # 費用項目行（インデント付き）
                    for j in range(production_item.childCount()):
                        expense_item = production_item.child(j)
                        writer.writerow([
                            expense_item.text(0),
                            "  " + expense_item.text(1),  # インデント
                            expense_item.text(2),
                            expense_item.text(3),
                            expense_item.text(4)
                        ])

            QMessageBox.information(self, "成功", f"CSV出力が完了しました:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"CSV出力に失敗しました:\n{str(e)}")

    def print_timeline(self):
        """印刷"""
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)

        if dialog.exec_() == QPrintDialog.Accepted:
            # 簡易的なHTML形式で印刷
            html = self._generate_print_html()

            from PyQt5.QtGui import QTextDocument
            document = QTextDocument()
            document.setHtml(html)
            document.print_(printer)

            QMessageBox.information(self, "成功", "印刷を開始しました")

    def _generate_print_html(self):
        """印刷用HTML生成"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: sans-serif; }
                h2 { text-align: center; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .production { font-weight: bold; background-color: #f9f9f9; }
                .expense { padding-left: 20px; }
            </style>
        </head>
        <body>
            <h2>番組・イベントタイムライン</h2>
            <table>
                <tr>
                    <th>実施日/支払予定日</th>
                    <th>番組・イベント名/項目名</th>
                    <th>種別</th>
                    <th>金額（円）</th>
                    <th>ステータス</th>
                </tr>
        """

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            production_item = root.child(i)

            # 番組・イベント行
            html += f"""
                <tr class="production">
                    <td>{production_item.text(0)}</td>
                    <td>{production_item.text(1)}</td>
                    <td>{production_item.text(2)}</td>
                    <td>{production_item.text(3)}</td>
                    <td>{production_item.text(4)}</td>
                </tr>
            """

            # 費用項目行
            for j in range(production_item.childCount()):
                expense_item = production_item.child(j)
                html += f"""
                    <tr class="expense">
                        <td>{expense_item.text(0)}</td>
                        <td>&nbsp;&nbsp;{expense_item.text(1)}</td>
                        <td>{expense_item.text(2)}</td>
                        <td>{expense_item.text(3)}</td>
                        <td>{expense_item.text(4)}</td>
                    </tr>
                """

        html += """
            </table>
        </body>
        </html>
        """

        return html
