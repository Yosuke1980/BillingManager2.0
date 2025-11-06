"""
マスター編集ダイアログ
モーダルダイアログでマスターデータを編集
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QGroupBox, QGridLayout, QMessageBox,
    QTabWidget, QWidget, QScrollArea, QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QKeySequence
from utils import log_message, format_payee_code
from order_management.ui.custom_date_edit import ImprovedDateEdit


class MasterEditDialog(QDialog):
    """マスター編集ダイアログ"""

    def __init__(self, parent, db_manager, master_id=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.master_id = master_id
        self.edit_entries = {}
        self.weekday_vars = {}

        # ダイアログの設定
        self.setWindowTitle("マスターデータ編集" if master_id else "新規マスターデータ作成")
        self.setModal(True)
        self.resize(900, 700)

        self.setup_ui()

        # データの読み込み（既存レコードの場合）
        if master_id:
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
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        scroll.setWidget(content)

        # 基本情報グループ
        basic_group = QGroupBox("基本情報")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(8)
        basic_layout.setColumnStretch(1, 1)
        content_layout.addWidget(basic_group)

        # フィールド定義
        fields = [
            ("ID:", "id", "readonly"),
            ("案件名 *:", "project_name", "text"),
            ("支払い先 *:", "payee", "text"),
            ("支払い先コード:", "payee_code", "text"),
            ("金額 *:", "amount", "text"),
            ("種別:", "payment_type", "combo", ["月額固定", "回数ベース"]),
            ("支払い時期:", "payment_timing", "combo", ["翌月末払い", "当月末払い"]),
            ("開始日:", "start_date", "date"),
            ("終了日:", "end_date", "date"),
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
            basic_layout.addWidget(label, row, 0, Qt.AlignRight | Qt.AlignVCenter)

            # 入力ウィジェット
            if field_type == "readonly":
                widget = QLineEdit()
                widget.setReadOnly(True)
                widget.setStyleSheet("background-color: #f8f9fa;")
                widget.setMaximumWidth(150)
            elif field_type == "date":
                widget = ImprovedDateEdit()
                widget.setDate(QDate.currentDate())
                widget.setMaximumWidth(200)
            elif field_type == "combo":
                widget = QComboBox()
                widget.addItems(field_def[3])
                widget.setMaximumWidth(200)
                if field_key == "payment_type":
                    widget.currentIndexChanged.connect(self.on_payment_type_change)
            else:  # text
                widget = QLineEdit()
                if field_key == "amount":
                    widget.setPlaceholderText("整数で入力")
                    widget.setMaximumWidth(200)
                elif field_key == "payee_code":
                    widget.setMaximumWidth(150)

            basic_layout.addWidget(widget, row, 1)
            self.edit_entries[field_key] = widget

            row += 1

        # 放送曜日グループ
        broadcast_group = QGroupBox("放送曜日（回数ベースの場合）")
        broadcast_layout = QHBoxLayout(broadcast_group)
        broadcast_layout.setSpacing(6)
        content_layout.addWidget(broadcast_group)

        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        for day in weekdays:
            checkbox = QCheckBox(day)
            broadcast_layout.addWidget(checkbox)
            self.weekday_vars[day] = checkbox

        broadcast_layout.addStretch()

        # 非表示の放送曜日フィールド（データ保存用）
        self.edit_entries["broadcast_days"] = QLineEdit()
        self.edit_entries["broadcast_days"].hide()

        # 余白を追加
        content_layout.addStretch()

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
            ("担当部門:", "department", 0, 2, "text"),
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
                widget.setDate(QDate.currentDate())
                widget.setSpecialValueText("未設定")
            elif field_type == "combo":
                widget = QComboBox()
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

    def on_payment_type_change(self, index):
        """種別変更時の処理"""
        # 必要に応じて処理を追加
        pass

    def load_data(self):
        """既存データの読み込み"""
        try:
            row = self.db_manager.get_master_by_id(self.master_id)
            if not row:
                QMessageBox.warning(self, "エラー", "データが見つかりません")
                return

            # 基本情報の設定
            self.edit_entries["id"].setText(str(row[0]))
            self.edit_entries["project_name"].setText(str(row[1]) if row[1] else "")
            self.edit_entries["payee"].setText(str(row[2]) if row[2] else "")
            self.edit_entries["payee_code"].setText(str(row[3]) if row[3] else "")

            # 金額を整数表示
            try:
                amount_int = int(float(row[4])) if row[4] else 0
                self.edit_entries["amount"].setText(str(amount_int))
            except (ValueError, TypeError):
                self.edit_entries["amount"].setText("0")

            # 種別
            payment_type = row[5] if row[5] else "月額固定"
            index = self.edit_entries["payment_type"].findText(payment_type)
            if index >= 0:
                self.edit_entries["payment_type"].setCurrentIndex(index)

            # 支払い時期
            payment_timing = row[17] if len(row) > 17 and row[17] else "翌月末払い"
            index = self.edit_entries["payment_timing"].findText(payment_timing)
            if index >= 0:
                self.edit_entries["payment_timing"].setCurrentIndex(index)

            # 日付フィールド
            for date_field, date_index in [("start_date", 7), ("end_date", 8)]:
                date_value = row[date_index] if len(row) > date_index and row[date_index] else ""
                if date_value:
                    try:
                        parts = date_value.split("-")
                        if len(parts) >= 3:
                            qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                            self.edit_entries[date_field].setDate(qdate)
                    except (ValueError, IndexError):
                        pass

            # 詳細情報
            self.edit_entries["client_name"].setText(str(row[9]) if len(row) > 9 and row[9] else "")
            self.edit_entries["department"].setText(str(row[10]) if len(row) > 10 and row[10] else "")

            # 案件状況
            project_status = row[11] if len(row) > 11 and row[11] else "進行中"
            index = self.edit_entries["project_status"].findText(project_status)
            if index >= 0:
                self.edit_entries["project_status"].setCurrentIndex(index)

            # 案件日付
            for date_field, date_index in [("project_start_date", 12), ("project_end_date", 13)]:
                date_value = row[date_index] if len(row) > date_index and row[date_index] else ""
                if date_value:
                    try:
                        parts = date_value.split("-")
                        if len(parts) >= 3:
                            qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
                            self.edit_entries[date_field].setDate(qdate)
                    except (ValueError, IndexError):
                        pass

            # 予算を整数表示
            try:
                budget_int = int(float(row[14])) if len(row) > 14 and row[14] else 0
                self.edit_entries["budget"].setText(str(budget_int))
            except (ValueError, TypeError):
                self.edit_entries["budget"].setText("0")

            self.edit_entries["approver"].setText(str(row[15]) if len(row) > 15 and row[15] else "")

            # 緊急度
            urgency_level = row[16] if len(row) > 16 and row[16] else "通常"
            index = self.edit_entries["urgency_level"].findText(urgency_level)
            if index >= 0:
                self.edit_entries["urgency_level"].setCurrentIndex(index)

            # 放送曜日
            broadcast_days_str = row[6] if len(row) > 6 and row[6] else ""
            selected_days = [day.strip() for day in broadcast_days_str.split(",") if day.strip()]

            for day, checkbox in self.weekday_vars.items():
                checkbox.setChecked(day in selected_days)

        except Exception as e:
            log_message(f"マスターデータ読み込みエラー: {e}")
            QMessageBox.critical(self, "エラー", f"データの読み込みに失敗しました: {e}")

    def set_default_values(self):
        """デフォルト値の設定（新規作成時）"""
        self.edit_entries["id"].setText("新規")
        self.edit_entries["payment_type"].setCurrentText("月額固定")
        self.edit_entries["payment_timing"].setCurrentText("翌月末払い")
        self.edit_entries["project_status"].setCurrentText("進行中")
        self.edit_entries["urgency_level"].setCurrentText("通常")
        self.edit_entries["amount"].setText("0")
        self.edit_entries["budget"].setText("0")

    def save(self):
        """データの保存"""
        try:
            # 基本情報の取得
            master_id = self.edit_entries["id"].text()
            project_name = self.edit_entries["project_name"].text()
            payee = self.edit_entries["payee"].text()
            payee_code = self.edit_entries["payee_code"].text()
            amount_str = self.edit_entries["amount"].text()
            payment_type = self.edit_entries["payment_type"].currentText()
            payment_timing = self.edit_entries["payment_timing"].currentText()

            # 支払い先コードの0埋め処理
            if payee_code:
                payee_code = format_payee_code(payee_code)
                self.edit_entries["payee_code"].setText(payee_code)

            # 日付の取得
            start_date = self.edit_entries["start_date"].date()
            start_date_str = f"{start_date.year()}-{start_date.month():02d}-{start_date.day():02d}"

            end_date = self.edit_entries["end_date"].date()
            end_date_str = f"{end_date.year()}-{end_date.month():02d}-{end_date.day():02d}"

            # 放送曜日を取得
            selected_days = [day for day, checkbox in self.weekday_vars.items() if checkbox.isChecked()]
            broadcast_days = ",".join(selected_days)

            # 詳細情報の取得
            client_name = self.edit_entries["client_name"].text()
            department = self.edit_entries["department"].text()
            project_status = self.edit_entries["project_status"].currentText()
            urgency_level = self.edit_entries["urgency_level"].currentText()

            project_start_date = self.edit_entries["project_start_date"].date()
            project_start_date_str = f"{project_start_date.year()}-{project_start_date.month():02d}-{project_start_date.day():02d}"

            project_end_date = self.edit_entries["project_end_date"].date()
            project_end_date_str = f"{project_end_date.year()}-{project_end_date.month():02d}-{project_end_date.day():02d}"

            budget_str = self.edit_entries["budget"].text()
            approver = self.edit_entries["approver"].text()

            # 入力チェック
            if not project_name or not payee or not amount_str:
                QMessageBox.critical(self, "エラー", "必須項目（案件名、支払先、金額）を入力してください")
                return

            # 種別が回数ベースの場合は放送曜日を必須に
            if payment_type == "回数ベース" and not broadcast_days:
                QMessageBox.critical(self, "エラー", "回数ベースの場合は放送曜日を選択してください")
                return

            # 金額の変換
            try:
                amount_str = amount_str.replace(",", "").replace("円", "").strip()
                amount = float(amount_str)
            except ValueError:
                QMessageBox.critical(self, "エラー", "金額は数値で入力してください")
                return

            # 予算の変換
            try:
                budget_str = budget_str.replace(",", "").replace("円", "").strip()
                budget = float(budget_str) if budget_str else 0
            except ValueError:
                budget = 0

            # データの設定
            is_new = master_id == "新規"
            data = {
                "project_name": project_name,
                "payee": payee,
                "payee_code": payee_code,
                "amount": amount,
                "payment_type": payment_type,
                "payment_timing": payment_timing,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "broadcast_days": broadcast_days,
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
                data["id"] = master_id

            # データベースに保存
            saved_id = self.db_manager.save_master(data, is_new)

            # 成功メッセージ
            if is_new:
                message = f"新しいマスターデータを作成しました（ID: {saved_id}）"
            else:
                message = f"マスターデータ ID: {saved_id} を更新しました"

            log_message(message)
            QMessageBox.information(self, "保存完了", message)

            # ダイアログを閉じる
            self.accept()

        except Exception as e:
            log_message(f"マスターデータ保存エラー: {e}")
            QMessageBox.critical(self, "エラー", f"データの保存に失敗しました: {e}")
