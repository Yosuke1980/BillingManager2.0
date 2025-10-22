import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QPushButton, QGroupBox, QGridLayout, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils import format_amount, log_message


class ManualMatchDialog(QDialog):
    def __init__(self, parent, payment_data, db_manager):
        super().__init__(parent)
        self.payment_data = payment_data
        self.db_manager = db_manager
        self.selected_expense_id = None
        
        self.setWindowTitle("手動照合")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
        self.load_expense_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 支払いデータ情報表示
        payment_group = QGroupBox("選択された支払いデータ")
        payment_layout = QGridLayout(payment_group)
        
        fields = [
            ("件名", self.payment_data.get('subject', '')),
            ("案件名", self.payment_data.get('project_name', '')),
            ("支払い先", self.payment_data.get('payee', '')),
            ("コード", self.payment_data.get('payee_code', '')),
            ("金額", self.payment_data.get('amount', '')),
            ("支払日", self.payment_data.get('payment_date', '')),
            ("状態", self.payment_data.get('status', ''))
        ]
        
        for i, (label, value) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            payment_layout.addWidget(QLabel(f"{label}:"), row, col)
            value_label = QLabel(str(value))
            value_label.setStyleSheet(
                "background-color: #f0f0f0; padding: 4px; border: 1px solid #ccc;"
            )
            payment_layout.addWidget(value_label, row, col + 1)
        
        layout.addWidget(payment_group)
        
        # 候補費用データ一覧
        candidates_group = QGroupBox("照合候補の費用データ")
        candidates_layout = QVBoxLayout(candidates_group)
        
        # フィルター説明
        filter_label = QLabel("※ 同じ支払い先コードまたは近似金額の費用データを表示しています")
        filter_label.setFont(QFont("", 9))
        filter_label.setStyleSheet("color: #666;")
        candidates_layout.addWidget(filter_label)
        
        # 費用データツリー
        self.expense_tree = QTreeWidget()
        self.expense_tree.setHeaderLabels([
            "案件名", "支払い先", "コード", "金額", "支払日", "状態"
        ])
        
        # 列サイズ設定
        self.expense_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.expense_tree.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        self.expense_tree.setAlternatingRowColors(True)
        self.expense_tree.itemSelectionChanged.connect(self.on_expense_selected)
        candidates_layout.addWidget(self.expense_tree)
        
        layout.addWidget(candidates_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        match_button = QPushButton("選択したデータと照合")
        match_button.clicked.connect(self.perform_manual_match)
        button_layout.addWidget(match_button)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_expense_data(self):
        """照合候補の費用データを読み込み"""
        try:
            # 候補検索条件
            payee_code = self.payment_data.get('payee_code', '').strip()
            amount_str = self.payment_data.get('amount', '').replace(',', '').replace('円', '')
            
            try:
                amount = float(amount_str) if amount_str else 0
            except ValueError:
                amount = 0
            
            # 候補費用データを取得
            expense_rows, _ = self.db_manager.get_expense_data()
            
            candidates = []
            for row in expense_rows:
                expense_id, project_name, payee, expense_payee_code, expense_amount, payment_date, status = row[:7]
                
                # 照合候補の条件
                code_match = payee_code and expense_payee_code and payee_code == expense_payee_code
                amount_match = amount > 0 and abs(float(expense_amount or 0) - amount) < 1.0
                
                if code_match or amount_match:
                    candidates.append(row)
            
            # ツリーにデータを追加
            for row in candidates:
                expense_id, project_name, payee, expense_payee_code, expense_amount, payment_date, status = row[:7]
                
                item = QTreeWidgetItem()
                item.setText(0, str(project_name or ''))
                item.setText(1, str(payee or ''))
                item.setText(2, str(expense_payee_code or ''))
                item.setText(3, format_amount(expense_amount))
                item.setText(4, str(payment_date or ''))
                item.setText(5, str(status or ''))
                item.setData(0, Qt.UserRole, expense_id)
                
                self.expense_tree.addTopLevelItem(item)
            
            if not candidates:
                item = QTreeWidgetItem()
                item.setText(0, "照合候補が見つかりません")
                for i in range(1, 6):
                    item.setText(i, "")
                self.expense_tree.addTopLevelItem(item)
        
        except Exception as e:
            log_message(f"費用データ読み込みエラー: {e}")
            QMessageBox.warning(self, "エラー", f"費用データの読み込みに失敗しました: {e}")
    
    def on_expense_selected(self):
        """費用データ選択時の処理"""
        selected_items = self.expense_tree.selectedItems()
        if selected_items:
            item = selected_items[0]
            self.selected_expense_id = item.data(0, Qt.UserRole)
    
    def perform_manual_match(self):
        """手動照合実行"""
        if not self.selected_expense_id:
            QMessageBox.information(self, "確認", "照合する費用データを選択してください")
            return
        
        try:
            # 確認ダイアログ
            reply = QMessageBox.question(
                self, "確認", 
                "選択された費用データと支払いデータを照合しますか？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # データベース更新
            conn_expenses = sqlite3.connect(self.db_manager.expenses_db)
            conn_payments = sqlite3.connect(self.db_manager.billing_db)
            
            try:
                # 費用データを照合済みに更新
                cursor_expenses = conn_expenses.cursor()
                cursor_expenses.execute(
                    "UPDATE expenses SET status = '照合済' WHERE id = ?",
                    (self.selected_expense_id,)
                )
                
                # 支払いデータを照合済みに更新（件名で特定）
                cursor_payments = conn_payments.cursor()
                cursor_payments.execute(
                    """UPDATE payments SET status = '照合済' 
                       WHERE subject = ? AND payee = ? AND amount = ?""",
                    (
                        self.payment_data.get('subject', ''),
                        self.payment_data.get('payee', ''),
                        float(self.payment_data.get('amount', '').replace(',', '').replace('円', '') or 0)
                    )
                )
                
                conn_expenses.commit()
                conn_payments.commit()
                
                log_message(f"手動照合成功: 費用ID:{self.selected_expense_id} <-> 支払い:{self.payment_data.get('subject', '')}")
                
                QMessageBox.information(self, "成功", "手動照合が完了しました")
                self.accept()
                
            except Exception as e:
                conn_expenses.rollback()
                conn_payments.rollback()
                raise e
            
            finally:
                conn_expenses.close()
                conn_payments.close()
        
        except Exception as e:
            log_message(f"手動照合エラー: {e}")
            QMessageBox.critical(self, "エラー", f"手動照合に失敗しました: {e}")