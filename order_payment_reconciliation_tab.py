"""発注・支払照合タブ

発注マスタから月次支払予定リストを生成し、実際の支払データと照合する画面
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QComboBox,
                             QMessageBox, QHeaderView, QGroupBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from datetime import datetime
from order_management.database_manager import OrderManagementDB
from database import DatabaseManager
from utils import log_message, format_amount


class OrderPaymentReconciliationTab(QWidget):
    """発注・支払照合タブ"""

    def __init__(self):
        super().__init__()
        self.order_db = OrderManagementDB()
        self.db_manager = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()

        # タイトル
        title_label = QLabel("発注・支払照合")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # フィルタセクション
        filter_group = QGroupBox("検索条件")
        filter_layout = QHBoxLayout()

        # 年選択
        filter_layout.addWidget(QLabel("年:"))
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 2, current_year + 2)]
        self.year_combo.addItems(years)
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.currentTextChanged.connect(self.load_reconciliation_data)
        filter_layout.addWidget(self.year_combo)

        # 月選択
        filter_layout.addWidget(QLabel("月:"))
        self.month_combo = QComboBox()
        months = [f"{m:02d}" for m in range(1, 13)]
        self.month_combo.addItems(months)
        self.month_combo.setCurrentText(f"{datetime.now().month:02d}")
        self.month_combo.currentTextChanged.connect(self.load_reconciliation_data)
        filter_layout.addWidget(self.month_combo)

        # 照合実行ボタン
        self.match_button = QPushButton("照合実行")
        self.match_button.clicked.connect(self.execute_matching)
        self.match_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        filter_layout.addWidget(self.match_button)

        # レポート出力ボタン
        self.export_button = QPushButton("レポート出力")
        self.export_button.clicked.connect(self.export_report)
        filter_layout.addWidget(self.export_button)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # サマリーセクション
        summary_group = QGroupBox("月次サマリー")
        summary_layout = QGridLayout()

        self.summary_labels = {}
        summary_items = [
            ('total_orders', '発注件数:', 0, 0),
            ('total_amount', '発注総額:', 0, 1),
            ('paid_count', '支払済件数:', 1, 0),
            ('paid_amount', '支払済金額:', 1, 1),
            ('unpaid_count', '未払い件数:', 2, 0),
            ('unpaid_amount', '未払い金額:', 2, 1),
            ('mismatch_count', '金額相違件数:', 3, 0),
            ('mismatch_amount', '金額相違合計:', 3, 1),
        ]

        for key, label_text, row, col in summary_items:
            label = QLabel(label_text)
            value_label = QLabel("0")
            value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.summary_labels[key] = value_label
            summary_layout.addWidget(label, row, col * 2)
            summary_layout.addWidget(value_label, row, col * 2 + 1)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "取引先コード", "取引先名", "発注番号", "案件名", "項目名",
            "支払タイプ", "計算内訳", "発注金額", "支払予定日",
            "支払タイミング", "ステータス"
        ])

        # カラム幅を調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 取引先コード
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 取引先名
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 発注番号
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 案件名
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 項目名
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 支払タイプ
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # 計算内訳
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # 発注金額
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # 支払予定日
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # 支払タイミング
        header.setSectionResizeMode(10, QHeaderView.ResizeToContents)  # ステータス

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addWidget(self.table)

        # ステータスバー
        self.status_label = QLabel("照合データを読み込んでいます...")
        self.status_label.setStyleSheet("margin: 5px; padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # 初期データ読み込み
        self.load_reconciliation_data()

    def load_reconciliation_data(self):
        """照合データを読み込み"""
        try:
            year = int(self.year_combo.currentText())
            month = int(self.month_combo.currentText())

            log_message(f"{year}年{month}月の照合データを読み込み中...")

            # 月次支払リストを取得
            payment_list = self.order_db.generate_monthly_payment_list(year, month)

            # サマリーを取得
            summary = self.order_db.get_payment_summary(year, month)

            # サマリーを更新
            self.update_summary(summary)

            # テーブルをクリア
            self.table.setRowCount(0)

            # テーブルに表示
            row = 0
            for partner in payment_list:
                partner_code = partner['partner_code']
                partner_name = partner['partner_name']

                for order in partner['orders']:
                    self.table.insertRow(row)

                    # 取引先コード (col 0)
                    self.table.setItem(row, 0, QTableWidgetItem(partner_code))

                    # 取引先名 (col 1)
                    self.table.setItem(row, 1, QTableWidgetItem(partner_name))

                    # 発注番号 (col 2)
                    self.table.setItem(row, 2, QTableWidgetItem(order['order_number']))

                    # 案件名 (col 3)
                    self.table.setItem(row, 3, QTableWidgetItem(order['project_name']))

                    # 項目名 (col 4)
                    self.table.setItem(row, 4, QTableWidgetItem(order['item_name']))

                    # 支払タイプ (col 5)
                    payment_type = order.get('payment_type', '-')
                    payment_type_item = QTableWidgetItem(payment_type)
                    payment_type_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 5, payment_type_item)

                    # 計算内訳 (col 6)
                    calculation_detail = order.get('calculation_detail', '-')
                    self.table.setItem(row, 6, QTableWidgetItem(calculation_detail))

                    # 発注金額 (col 7)
                    amount_item = QTableWidgetItem(format_amount(order['amount']))
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, 7, amount_item)

                    # 支払予定日 (col 8)
                    self.table.setItem(row, 8, QTableWidgetItem(order['expected_payment_date']))

                    # 支払タイミング (col 9)
                    payment_timing = order.get('payment_timing', '-')
                    payment_timing_item = QTableWidgetItem(payment_timing)
                    payment_timing_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 9, payment_timing_item)

                    # ステータス (col 10)
                    status = order['payment_status']
                    status_item = QTableWidgetItem(status)
                    status_item.setTextAlignment(Qt.AlignCenter)

                    # ステータスに応じて色分け
                    text_color = QColor(0, 0, 0)  # 黒
                    if status == '支払済':
                        status_item.setBackground(QColor(144, 238, 144))  # 薄緑
                    elif status == '金額相違':
                        status_item.setBackground(QColor(255, 255, 153))  # 薄黄
                    elif status == '未払い':
                        status_item.setBackground(QColor(255, 182, 193))  # 薄赤
                    else:
                        status_item.setBackground(QColor(211, 211, 211))  # グレー

                    status_item.setForeground(QBrush(text_color))
                    self.table.setItem(row, 10, status_item)

                    row += 1

            # ステータスバー更新
            total_orders = sum(len(p['orders']) for p in payment_list)
            self.status_label.setText(
                f"{year}年{month}月: {len(payment_list)}取引先、{total_orders}件の発注データを表示"
            )

            log_message(f"照合データ読み込み完了: {len(payment_list)}取引先、{total_orders}件")

        except Exception as e:
            log_message(f"照合データ読み込みエラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")
            QMessageBox.critical(self, "エラー", f"データの読み込みに失敗しました:\n{str(e)}")

    def update_summary(self, summary):
        """サマリーを更新"""
        self.summary_labels['total_orders'].setText(f"{summary['total_orders']}件")
        self.summary_labels['total_amount'].setText(format_amount(summary['total_amount']))
        self.summary_labels['paid_count'].setText(f"{summary['paid_count']}件")
        self.summary_labels['paid_amount'].setText(format_amount(summary['paid_amount']))
        self.summary_labels['unpaid_count'].setText(f"{summary['unpaid_count']}件")
        self.summary_labels['unpaid_amount'].setText(format_amount(summary['unpaid_amount']))
        self.summary_labels['mismatch_count'].setText(f"{summary['mismatch_count']}件")
        self.summary_labels['mismatch_amount'].setText(format_amount(summary['mismatch_amount']))

        # 未払いがある場合は赤色で強調
        if summary['unpaid_count'] > 0:
            self.summary_labels['unpaid_count'].setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
            self.summary_labels['unpaid_amount'].setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        else:
            self.summary_labels['unpaid_count'].setStyleSheet("font-weight: bold; font-size: 14px;")
            self.summary_labels['unpaid_amount'].setStyleSheet("font-weight: bold; font-size: 14px;")

        # 金額相違がある場合は黄色で強調
        if summary['mismatch_count'] > 0:
            self.summary_labels['mismatch_count'].setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
            self.summary_labels['mismatch_amount'].setStyleSheet("font-weight: bold; font-size: 14px; color: orange;")
        else:
            self.summary_labels['mismatch_count'].setStyleSheet("font-weight: bold; font-size: 14px;")
            self.summary_labels['mismatch_amount'].setStyleSheet("font-weight: bold; font-size: 14px;")

    def execute_matching(self):
        """照合を実行"""
        try:
            year = int(self.year_combo.currentText())
            month = int(self.month_combo.currentText())

            # 確認ダイアログ
            reply = QMessageBox.question(
                self,
                "照合実行確認",
                f"{year}年{month}月の発注データと支払データを照合しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

            # 照合実行
            log_message(f"{year}年{month}月の照合を開始...")
            self.status_label.setText("照合処理中...")

            matched_count, not_matched_count, errors = self.db_manager.match_orders_with_payments(year, month)

            # 結果表示
            if errors:
                error_msg = "\n".join(errors)
                QMessageBox.warning(
                    self,
                    "照合エラー",
                    f"照合処理中にエラーが発生しました:\n{error_msg}"
                )
            else:
                QMessageBox.information(
                    self,
                    "照合完了",
                    f"照合が完了しました。\n\n"
                    f"照合成功: {matched_count}件\n"
                    f"未照合: {not_matched_count}件"
                )

            # データを再読み込み
            self.load_reconciliation_data()

        except Exception as e:
            log_message(f"照合実行エラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")
            QMessageBox.critical(self, "エラー", f"照合処理に失敗しました:\n{str(e)}")

    def export_report(self):
        """レポートをCSV出力"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv

            year = int(self.year_combo.currentText())
            month = int(self.month_combo.currentText())

            # 保存先を選択
            default_filename = f"発注支払照合_{year}{month:02d}.csv"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "レポート保存",
                default_filename,
                "CSV Files (*.csv)"
            )

            if not filename:
                return

            # データ取得
            payment_list = self.order_db.generate_monthly_payment_list(year, month)
            summary = self.order_db.get_payment_summary(year, month)

            # CSV出力
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # ヘッダー
                writer.writerow([f"{year}年{month}月 発注・支払照合レポート"])
                writer.writerow([])

                # サマリー
                writer.writerow(["サマリー"])
                writer.writerow(["発注件数", summary['total_orders']])
                writer.writerow(["発注総額", summary['total_amount']])
                writer.writerow(["支払済件数", summary['paid_count']])
                writer.writerow(["支払済金額", summary['paid_amount']])
                writer.writerow(["未払い件数", summary['unpaid_count']])
                writer.writerow(["未払い金額", summary['unpaid_amount']])
                writer.writerow(["金額相違件数", summary['mismatch_count']])
                writer.writerow(["金額相違合計", summary['mismatch_amount']])
                writer.writerow([])

                # 明細
                writer.writerow(["明細"])
                writer.writerow([
                    "取引先コード", "取引先名", "発注番号", "案件名", "項目名",
                    "支払タイプ", "計算内訳", "発注金額", "支払予定日",
                    "支払タイミング", "ステータス", "金額差異"
                ])

                for partner in payment_list:
                    for order in partner['orders']:
                        writer.writerow([
                            partner['partner_code'],
                            partner['partner_name'],
                            order['order_number'],
                            order['project_name'],
                            order['item_name'],
                            order.get('payment_type', '-'),
                            order.get('calculation_detail', '-'),
                            order['amount'],
                            order['expected_payment_date'],
                            order.get('payment_timing', '-'),
                            order['payment_status'],
                            order['payment_difference']
                        ])

            QMessageBox.information(self, "成功", f"レポートを出力しました:\n{filename}")
            log_message(f"レポート出力完了: {filename}")

        except Exception as e:
            log_message(f"レポート出力エラー: {e}")
            import traceback
            log_message(f"エラー詳細: {traceback.format_exc()}")
            QMessageBox.critical(self, "エラー", f"レポート出力に失敗しました:\n{str(e)}")
