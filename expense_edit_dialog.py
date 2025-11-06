"""
費用編集ダイアログ
モーダルダイアログで費用データを編集
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QMessageBox,
    QTabWidget, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QKeySequence
from utils import log_message, format_payee_code
from payee_line_edit import PayeeLineEdit
from order_management.ui.custom_date_edit import ImprovedDateEdit


class ExpenseEditDialog(QDialog):
    """費用編集ダイアログ"""

    def __init__(self, parent, db_manager, expense_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.expense_id = expense_id
        self.edit_entries = {}

        # ダイアログの設定
        self.setWindowTitle("費用データ編集" if expense_id else "新規費用データ作成")
        self.setModal(True)
        self.resize(900, 700)

        self.setup_ui()

        # データの読み込み（既存レコードの場合）
        if expense_id:
            self.load_data()
        else:
            self.set_default_values()

        # 最初のフィールドにフォーカス
        self.edit_entries.get("project_name", QLineEdit()).setFocus()

    def setup_ui(self):
        """UIのセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # タブウィジェット
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # 基本タブ
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "基本情報")

        # 詳細タブ
        detail_tab = self.create_detail_tab()
        tab_widget.addTab(detail_tab, "詳細情報")

        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("キャンセル (Esc)")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setMinimumWidth(120)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("保存 (Ctrl+S)")
        save_button.clicked.connect(self.save)
        save_button.setDefault(True)
        save_button.setMinimumWidth(120)
        button_layout.addWidget(save_button)

        layout.addLayout(button_layout)

        # キーボードショートカット
        self.setup_shortcuts()

    def create_basic_tab(self):
        """基本タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroll)

        # コンテンツウィジェット
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setSpacing(8)
        content_layout.setColumnStretch(1, 1)  # 入力欄を伸縮
        scroll.setWidget(content)

        # フィールド定義
        fields = [
            ("ID:", "id", "readonly"),
            ("案件名 *:", "project_name", "text"),
            ("支払い先 *:", "payee", "payee"),
            ("支払い先コード:", "payee_code", "text"),
            ("金額 *:", "amount", "text"),
            ("支払日 *:", "payment_date", "date"),
            ("状態:", "status", "combo", ["未処理", "処理中", "照合済", "完了"]),
            ("支払い時期:", "payment_timing", "combo", ["翌月末払い", "当月末払い"]),
        ]

        row = 0
        for field_def in fields:
            label_text = field_def[0]
            field_key = field_def[1]
            field_type = field_def[2]

            # ラベル
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            label.setMinimumWidth(150)
            content_layout.addWidget(label, row, 0, Qt.AlignRight | Qt.AlignVCenter)

            # 入力ウィジェット
            if field_type == "readonly":
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setStyleSheet("background-color: #f8f9fa;")
                widget.setMaximumWidth(150)
            elif field_type == "payee":
                widget = PayeeLineEdit(self.db_manager)
                # 支払い先コードとの連動を後で設定
            elif field_type == "date":
                widget = ImprovedDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                widget.setDisplayFormat("yyyy-MM-dd")
                widget.setMaximumWidth(200)
            elif field_type == "combo":
                widget = QComboBox()
                widget.addItems(field_def[3])
                widget.setMaximumWidth(200)
            else:  # text
                widget = QLineEdit()
                if field_key == "amount":
                    widget.setPlaceholderText("整数で入力")
                    widget.setMaximumWidth(200)
                elif field_key == "payee_code":
                    widget.setMaximumWidth(150)

            content_layout.addWidget(widget, row, 1)
            self.edit_entries[field_key] = widget

            row += 1

        # 支払い先と支払い先コードの連動
        payee_widget = self.edit_entries.get("payee")
        payee_code_widget = self.edit_entries.get("payee_code")
        if isinstance(payee_widget, PayeeLineEdit) and payee_code_widget:
            payee_widget.code_field = payee_code_widget

        # 余白を追加
        content_layout.setRowStretch(row, 1)

        return tab

    def create_detail_tab(self):
        """詳細タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroll)

        # コンテンツウィジェット
        content = QWidget()
        content_layout = QGridLayout(content)
        content_layout.setSpacing(8)
        content_layout.setColumnStretch(1, 1)  # 左列の入力欄
        content_layout.setColumnStretch(3, 1)  # 右列の入力欄
        scroll.setWidget(content)

        # フィールド定義（2カラム）
        fields = [
            ("クライアント:", "client_name", 0, 0, "text"),
            ("担当部門:", "department", 0, 2, "combo_editable", ["", "営業部", "マーケティング部", "総務部", "企画部", "制作部"]),
            ("案件状況:", "project_status", 1, 0, "combo", ["進行中", "完了", "中止", "保留"]),
            ("緊急度:", "urgency_level", 1, 2, "combo", ["通常", "重要", "緊急"]),
            ("開始日:", "project_start_date", 2, 0, "date"),
            ("完了予定日:", "project_end_date", 2, 2, "date"),
            ("予算:", "budget", 3, 0, "text"),
            ("承認者:", "approver", 3, 2, "text"),
        ]

        for field_def in fields:
            label_text = field_def[0]
            field_key = field_def[1]
            row = field_def[2]
            col = field_def[3]
            field_type = field_def[4]

            # ラベル
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold; color: #2c3e50;")
            label.setMinimumWidth(120)
            content_layout.addWidget(label, row, col, Qt.AlignRight | Qt.AlignVCenter)

            # 入力ウィジェット
            if field_type == "date":
                widget = ImprovedDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                widget.setDisplayFormat("yyyy-MM-dd")
                widget.setSpecialValueText("未設定")
            elif field_type == "combo":
                widget = QComboBox()
                widget.addItems(field_def[5])
            elif field_type == "combo_editable":
                widget = QComboBox()
                widget.setEditable(True)
                widget.addItems(field_def[5])
            else:  # text
                widget = QLineEdit()
                if field_key == "budget":
                    widget.setPlaceholderText("整数で入力")

            content_layout.addWidget(widget, row, col + 1)
            self.edit_entries[field_key] = widget

        # 余白を追加
        content_layout.setRowStretch(4, 1)

        return tab

    def setup_shortcuts(self):
        """キーボードショートカットのセットアップ"""
        # Ctrl+S: 保存
        from PyQt5.QtWidgets import QShortcut
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save)

        # Ctrl+Enter: 保存（代替）
        save_shortcut2 = QShortcut(QKeySequence("Ctrl+Return"), self)
        save_shortcut2.activated.connect(self.save)

        # Esc: キャンセル
        cancel_shortcut = QShortcut(QKeySequence("Esc"), self)
        cancel_shortcut.activated.connect(self.reject)

        # Enter: 次のフィールドへ（LineEditのみ）
        for field_key, widget in self.edit_entries.items():
            if isinstance(widget, QLineEdit) and not widget.isReadOnly():
                widget.returnPressed.connect(self.focus_next_field)

    def focus_next_field(self):
        """次のフィールドにフォーカス"""
        self.focusNextChild()

    def load_data(self):
        """既存データの読み込み"""
        try:
            row = self.db_manager.get_expense_by_id(self.expense_id)
            if not row:
                QMessageBox.warning(self, "エラー", "データが見つかりません")
                return

            # フィールドマッピング
            field_mapping = {
                0: "id",
                1: "project_name",
                2: "payee",
                3: "payee_code",
                4: "amount",
                5: "payment_date",
                6: "status",
                7: "client_name",
                8: "department",
                9: "project_status",
                10: "project_start_date",
                11: "project_end_date",
                12: "budget",
                13: "approver",
                14: "urgency_level",
                15: "payment_timing"
            }

            for i, field in field_mapping.items():
                if i >= len(row) or field not in self.edit_entries:
                    continue

                widget = self.edit_entries[field]
                value = row[i] if row[i] is not None else ""

                if isinstance(widget, QComboBox) and not widget.isEditable():
                    # 通常のコンボボックス
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, QComboBox) and widget.isEditable():
                    # 編集可能コンボボックス
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QDateEdit):
                    # 日付フィールド
                    if str(value) and str(value) != "":
                        try:
                            parts = str(value).split("-")
                            if len(parts) >= 3:
                                qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                                widget.setDate(qdate)
                        except (ValueError, IndexError):
                            pass
                elif field in ["amount", "budget"]:
                    # 金額フィールド（整数表示）
                    try:
                        int_value = int(float(value)) if value else 0
                        widget.setText(str(int_value))
                    except (ValueError, TypeError):
                        widget.setText("0")
                else:
                    # テキストフィールド
                    widget.setText(str(value))

        except Exception as e:
            log_message(f"データ読み込みエラー: {e}")
            QMessageBox.critical(self, "エラー", f"データの読み込みに失敗しました: {e}")

    def set_default_values(self):
        """デフォルト値の設定（新規作成時）"""
        self.edit_entries["id"].setText("新規")
        self.edit_entries["status"].setCurrentText("未処理")
        self.edit_entries["payment_timing"].setCurrentText("翌月末払い")
        self.edit_entries["project_status"].setCurrentText("進行中")
        self.edit_entries["urgency_level"].setCurrentText("通常")
        self.edit_entries["amount"].setText("0")
        self.edit_entries["budget"].setText("0")

    def save(self):
        """データの保存"""
        try:
            # 基本情報の取得
            expense_id = self.edit_entries["id"].text()
            project_name = self.edit_entries["project_name"].text()
            payee = self.edit_entries["payee"].text()
            payee_code = self.edit_entries["payee_code"].text()
            amount_str = self.edit_entries["amount"].text()
            status = self.edit_entries["status"].currentText()
            payment_timing = self.edit_entries["payment_timing"].currentText()

            # 支払い先コードの0埋め処理
            if payee_code:
                payee_code = format_payee_code(payee_code)
                self.edit_entries["payee_code"].setText(payee_code)

            # 日付の取得
            date = self.edit_entries["payment_date"].date()
            payment_date = f"{date.year()}-{date.month():02d}-{date.day():02d}"

            # 詳細情報の取得
            client_name = self.edit_entries["client_name"].text()
            department = self.edit_entries["department"].currentText() if hasattr(self.edit_entries["department"], 'currentText') else ""
            project_status = self.edit_entries["project_status"].currentText()
            urgency_level = self.edit_entries["urgency_level"].currentText()

            project_start_date = self.edit_entries["project_start_date"].date()
            project_start_date_str = f"{project_start_date.year()}-{project_start_date.month():02d}-{project_start_date.day():02d}"

            project_end_date = self.edit_entries["project_end_date"].date()
            project_end_date_str = f"{project_end_date.year()}-{project_end_date.month():02d}-{project_end_date.day():02d}"

            budget_str = self.edit_entries["budget"].text()
            approver = self.edit_entries["approver"].text()

            # 入力チェック
            if not project_name or not payee or not amount_str or not payment_date:
                QMessageBox.critical(self, "エラー", "必須項目（案件名、支払先、金額、支払日）を入力してください")
                return

            # 金額と予算の変換
            try:
                amount_str = amount_str.replace(",", "").replace("円", "").strip()
                amount = float(amount_str)
            except ValueError:
                QMessageBox.critical(self, "エラー", "金額は数値で入力してください")
                return

            try:
                budget = float(budget_str.replace(",", "").replace("円", "").strip()) if budget_str else 0
            except ValueError:
                budget = 0

            # データの設定
            is_new = expense_id == "新規"
            data = {
                "project_name": project_name,
                "payee": payee,
                "payee_code": payee_code,
                "amount": amount,
                "payment_date": payment_date,
                "status": status,
                "payment_timing": payment_timing,
                "client_name": client_name,
                "department": department,
                "project_status": project_status,
                "project_start_date": project_start_date_str,
                "project_end_date": project_end_date_str,
                "budget": budget,
                "approver": approver,
                "urgency_level": urgency_level,
            }

            if not is_new:
                data["id"] = expense_id

            # データベースに保存
            saved_id = self.db_manager.save_expense(data, is_new)

            # 成功メッセージ
            if is_new:
                message = f"新しい費用データを作成しました（ID: {saved_id}）"
            else:
                message = f"費用データ ID: {saved_id} を更新しました"

            log_message(message)
            QMessageBox.information(self, "保存完了", message)

            # ダイアログを閉じる
            self.accept()

        except Exception as e:
            log_message(f"費用データ保存エラー: {e}")
            QMessageBox.critical(self, "エラー", f"データの保存に失敗しました: {e}")
