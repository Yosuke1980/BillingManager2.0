"""案件ツリービューウィジェット

案件と費用項目をツリー形式で表示するウィジェットです。
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
    QHBoxLayout, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from order_management.database_manager import OrderManagementDB
from order_management.ui.expense_edit_dialog import ExpenseEditDialog
from order_management.config import OrderConfig
from order_management.gmail_manager import GmailManager
from order_management.email_template import EmailTemplate
from order_management.order_number_generator import OrderNumberGenerator


class ProjectTreeWidget(QWidget):
    """案件ツリービューウィジェット"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.current_project_id = None
        self._setup_ui()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # ヘッダー
        self.header_label = QLabel("案件を選択してください")
        self.header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(self.header_label)

        # ツリーウィジェット
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["項目", "金額", "ステータス", "実施日"])
        self.tree.itemDoubleClicked.connect(self.edit_expense)

        layout.addWidget(self.tree)

        # ボタン
        button_layout = QHBoxLayout()
        self.edit_expense_button = QPushButton("費用項目編集")
        self.delete_expense_button = QPushButton("費用項目削除")
        self.create_draft_button = QPushButton("発注メール作成")

        self.edit_expense_button.clicked.connect(self.edit_expense)
        self.delete_expense_button.clicked.connect(self.delete_expense)
        self.create_draft_button.clicked.connect(self.create_order_draft)

        button_layout.addWidget(self.edit_expense_button)
        button_layout.addWidget(self.delete_expense_button)
        button_layout.addWidget(self.create_draft_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def load_project(self, project_id: int):
        """案件データを読み込み（単一ID、後方互換性のため残す）"""
        self.load_projects([project_id])

    def load_projects(self, project_ids: list):
        """案件データを読み込み（複数ID対応）"""
        self.tree.clear()

        if not project_ids or not project_ids[0]:
            self.header_label.setText("案件を選択してください")
            return

        # 最初のIDを保存（既存機能との互換性）
        self.current_project_id = project_ids[0]

        # 複数案件の場合の合計を計算
        total_actual = 0
        project_names = []
        project_dates = []

        for project_id in project_ids:
            project = self.db.get_project_by_id(project_id)
            if project:
                project_names.append(project[1])
                project_dates.append(project[2] or "")

                summary = self.db.get_project_summary(project_id)
                total_actual += summary['actual']

        # ヘッダー更新（複数案件対応）
        if len(project_ids) == 1:
            # 単一案件の場合
            header_text = f"{project_dates[0]} {project_names[0]} | "
        else:
            # 複数案件の場合
            header_text = f"{project_names[0]} ({len(project_ids)}件) | "

        header_text += f"実績: {total_actual:,.0f}円"

        self.header_label.setText(header_text)

        # 全案件の費用項目を取得して表示
        for project_id in project_ids:
            expenses = self.db.get_expenses_by_project(project_id)

            for expense in expenses:
                expense_id = expense[0]
                item_name = expense[2]
                amount = expense[3]
                status = expense[6]
                impl_date = expense[8] or ""

                # ツリーアイテム作成
                tree_item = QTreeWidgetItem([
                    item_name,
                    f"{amount:,.0f}円",
                    status,
                    impl_date
                ])
                tree_item.setData(0, Qt.UserRole, expense_id)

                # 全カラムに基本文字色を設定（Mac対応）
                text_color = QColor("#2c3e50")  # 濃いグレー
                for col in range(4):  # 4列分
                    tree_item.setForeground(col, text_color)

                # ステータスに応じて色を変更
                if status == "発注予定":
                    tree_item.setForeground(2, Qt.gray)
                elif status == "下書き作成済":
                    tree_item.setForeground(2, Qt.blue)
                elif status == "発注済":
                    tree_item.setForeground(2, Qt.darkCyan)
                elif status == "請求書待ち":
                    tree_item.setForeground(2, Qt.darkYellow)
                elif status == "支払済":
                    tree_item.setForeground(2, Qt.darkGreen)

                self.tree.addTopLevelItem(tree_item)

        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

    def edit_expense(self):
        """費用項目編集"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "編集する費用項目を選択してください")
            return

        expense_id = current_item.data(0, Qt.UserRole)
        expense = self.db.get_expense_order_by_id(expense_id)

        dialog = ExpenseEditDialog(self, self.current_project_id, expense)
        if dialog.exec_():
            expense_data = dialog.get_data()
            expense_data['id'] = expense_id
            try:
                self.db.save_expense_order(expense_data, is_new=False)
                self.load_project(self.current_project_id)
                # 成功メッセージは表示しない（煩わしいため）
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"更新に失敗しました: {e}")

    def delete_expense(self):
        """費用項目削除"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "削除する費用項目を選択してください")
            return

        expense_id = current_item.data(0, Qt.UserRole)
        item_name = current_item.text(0)

        reply = QMessageBox.question(
            self, "確認",
            f"{item_name} を削除してもよろしいですか?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.db.delete_expense_order(expense_id)
                self.load_project(self.current_project_id)
                QMessageBox.information(self, "成功", "費用項目を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"削除に失敗しました: {e}")

    def create_order_draft(self):
        """発注メール下書き作成"""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "費用項目を選択してください")
            return

        # Gmail設定確認
        if not OrderConfig.is_gmail_configured():
            QMessageBox.warning(
                self, "警告",
                "Gmail設定が未設定です。\n先に「設定」タブでGmail設定を行ってください。"
            )
            return

        expense_id = current_item.data(0, Qt.UserRole)
        expense = self.db.get_expense_order_by_id(expense_id)

        # 発注先情報取得
        supplier_id = expense[4]
        if not supplier_id:
            QMessageBox.warning(self, "警告", "発注先が設定されていません")
            return

        supplier = self.db.get_supplier_by_id(supplier_id)
        if not supplier or not supplier[3]:  # メールアドレス確認
            QMessageBox.warning(self, "警告", "発注先のメールアドレスが設定されていません")
            return

        # 案件情報取得
        project = self.db.get_project_by_id(self.current_project_id)

        # 発注番号生成
        generator = OrderNumberGenerator()
        order_number = generator.generate_order_number(expense[9])  # order_date

        # メール生成
        config = OrderConfig.get_gmail_config()
        template_data = {
            'contact_person': expense[5] or supplier[2] or "ご担当者",
            'order_number': order_number,
            'project_name': project[1],
            'implementation_date': expense[8],
            'item_name': expense[2],
            'amount': expense[3],
            'payment_scheduled_date': expense[11],
        }

        subject = EmailTemplate.generate_subject(
            order_number, expense[8], project[1], expense[2]
        )
        body = EmailTemplate.generate_body(template_data, config['signature'])

        # Gmail下書き作成
        try:
            gmail = GmailManager(
                config['address'],
                config['app_password'],
                config['imap_server'],
                config['imap_port']
            )

            draft_id = gmail.create_draft(supplier[3], subject, body)

            if draft_id:
                # データベース更新
                expense_data = {
                    'id': expense_id,
                    'project_id': expense[1],
                    'item_name': expense[2],
                    'amount': expense[3],
                    'supplier_id': supplier_id,
                    'contact_person': expense[5],
                    'status': '下書き作成済',
                    'order_number': order_number,
                    'order_date': expense[7],
                    'implementation_date': expense[8],
                    'invoice_received_date': expense[9],
                    'payment_scheduled_date': expense[10],
                    'payment_date': expense[11],
                    'gmail_draft_id': draft_id,
                    'notes': expense[16],
                }
                self.db.save_expense_order(expense_data, is_new=False)

                self.load_project(self.current_project_id)
                QMessageBox.information(
                    self, "成功",
                    f"Gmail下書きを作成しました\n発注番号: {order_number}\n\nGmailを開いて下書きを確認・送信してください。"
                )
            else:
                QMessageBox.warning(self, "失敗", "Gmail下書きの作成に失敗しました")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"下書き作成中にエラーが発生しました:\n{str(e)}")
