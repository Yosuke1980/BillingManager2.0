"""番組編集ダイアログ

番組マスターの新規追加・編集を行うダイアログです。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QMessageBox, QLabel,
    QRadioButton, QButtonGroup, QCheckBox, QListWidget, QListWidgetItem,
    QInputDialog, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from order_management.database_manager import OrderManagementDB


class ProgramEditDialog(QDialog):
    """番組編集ダイアログ"""

    def __init__(self, parent=None, program=None):
        super().__init__(parent)
        self.db = OrderManagementDB()
        self.program = program
        self.is_edit = program is not None

        self.setWindowTitle("番組編集" if self.is_edit else "新規番組登録")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        self._setup_ui()

        if self.is_edit:
            self._load_program_data()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # フォームレイアウト
        form_layout = QFormLayout()

        # 番組名（必須）
        self.name_edit = QLineEdit()
        form_layout.addRow("番組名 *:", self.name_edit)

        # 備考
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("備考:", self.description_edit)

        # 開始日
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("開始日:", self.start_date_edit)

        # 終了日
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("終了日:", self.end_date_edit)

        # 放送時間
        self.broadcast_time_edit = QLineEdit()
        self.broadcast_time_edit.setPlaceholderText("例: 23:00-24:00")
        form_layout.addRow("放送時間:", self.broadcast_time_edit)

        # 放送曜日（チェックボックス）
        broadcast_days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        days = ["月", "火", "水", "木", "金", "土", "日"]
        for day in days:
            checkbox = QCheckBox(day)
            self.day_checkboxes[day] = checkbox
            broadcast_days_layout.addWidget(checkbox)

        broadcast_days_widget = QLabel()
        broadcast_days_widget.setLayout(broadcast_days_layout)
        form_layout.addRow("放送曜日:", broadcast_days_widget)

        # ステータス（ラジオボタン）
        status_layout = QHBoxLayout()
        self.status_group = QButtonGroup()
        self.status_broadcasting = QRadioButton("放送中")
        self.status_ended = QRadioButton("終了")
        self.status_group.addButton(self.status_broadcasting)
        self.status_group.addButton(self.status_ended)
        self.status_broadcasting.setChecked(True)
        status_layout.addWidget(self.status_broadcasting)
        status_layout.addWidget(self.status_ended)
        status_layout.addStretch()

        status_widget = QLabel()
        status_widget.setLayout(status_layout)
        form_layout.addRow("ステータス:", status_widget)

        layout.addLayout(form_layout)

        # 出演者セクション
        cast_label = QLabel("出演者:")
        cast_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(cast_label)

        self.cast_list = QListWidget()
        self.cast_list.setMaximumHeight(120)
        layout.addWidget(self.cast_list)

        cast_button_layout = QHBoxLayout()
        self.add_cast_button = QPushButton("出演者追加")
        self.edit_cast_button = QPushButton("出演者編集")
        self.delete_cast_button = QPushButton("出演者削除")
        self.add_cast_button.clicked.connect(self.add_cast)
        self.edit_cast_button.clicked.connect(self.edit_cast)
        self.delete_cast_button.clicked.connect(self.delete_cast)
        cast_button_layout.addWidget(self.add_cast_button)
        cast_button_layout.addWidget(self.edit_cast_button)
        cast_button_layout.addWidget(self.delete_cast_button)
        cast_button_layout.addStretch()
        layout.addLayout(cast_button_layout)

        # 制作会社セクション
        producer_label = QLabel("制作会社:")
        producer_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(producer_label)

        self.producer_list = QListWidget()
        self.producer_list.setMaximumHeight(120)
        self.producer_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.producer_list)

        producer_button_layout = QHBoxLayout()
        self.add_producer_button = QPushButton("制作会社追加")
        self.delete_producer_button = QPushButton("制作会社削除")
        self.add_producer_button.clicked.connect(self.add_producer)
        self.delete_producer_button.clicked.connect(self.delete_producer)
        producer_button_layout.addWidget(self.add_producer_button)
        producer_button_layout.addWidget(self.delete_producer_button)
        producer_button_layout.addStretch()
        layout.addLayout(producer_button_layout)

        # ボタン
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("キャンセル")
        self.save_button.clicked.connect(self.save)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # 出演者・制作会社データを保持する内部リスト
        self.cast_data = []  # [{'cast_name': '名前', 'role': '役割'}, ...]
        self.producer_data = []  # [{'id': partner_id, 'name': '会社名'}, ...]

    def _load_program_data(self):
        """番組データを読み込み"""
        if not self.program:
            return

        # 基本情報
        self.name_edit.setText(self.program[1] or "")
        self.description_edit.setPlainText(self.program[2] or "")

        # 日付
        if self.program[3]:  # start_date
            self.start_date_edit.setDate(QDate.fromString(self.program[3], "yyyy-MM-dd"))
        if self.program[4]:  # end_date
            self.end_date_edit.setDate(QDate.fromString(self.program[4], "yyyy-MM-dd"))

        # 放送時間
        self.broadcast_time_edit.setText(self.program[5] or "")

        # 放送曜日
        broadcast_days = self.program[6] or ""
        if broadcast_days:
            selected_days = broadcast_days.split(",")
            for day in selected_days:
                if day in self.day_checkboxes:
                    self.day_checkboxes[day].setChecked(True)

        # ステータス
        status = self.program[7] or "放送中"
        if status == "終了":
            self.status_ended.setChecked(True)
        else:
            self.status_broadcasting.setChecked(True)

        # 出演者を読み込み
        program_id = self.program[0]
        cast_list = self.db.get_program_cast(program_id)
        for cast in cast_list:
            cast_data = {
                'cast_name': cast[2],
                'role': cast[3] or ""
            }
            self.cast_data.append(cast_data)
            self._add_cast_to_list(cast_data)

        # 制作会社を読み込み
        producer_list = self.db.get_program_producers(program_id)
        for producer in producer_list:
            producer_data = {
                'id': producer[1],  # partner_id
                'name': producer[2]  # partner_name
            }
            self.producer_data.append(producer_data)
            self._add_producer_to_list(producer_data)

    def _add_cast_to_list(self, cast_data):
        """出演者をリストに追加"""
        display_text = cast_data['cast_name']
        if cast_data.get('role'):
            display_text += f" ({cast_data['role']})"
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, cast_data)
        self.cast_list.addItem(item)

    def _add_producer_to_list(self, producer_data):
        """制作会社をリストに追加"""
        item = QListWidgetItem(producer_data['name'])
        item.setData(Qt.UserRole, producer_data)
        self.producer_list.addItem(item)

    def add_cast(self):
        """出演者追加"""
        name, ok = QInputDialog.getText(self, "出演者追加", "出演者名:")
        if ok and name:
            role, ok2 = QInputDialog.getText(self, "出演者追加", "役割（任意）:")
            cast_data = {
                'cast_name': name,
                'role': role if ok2 else ""
            }
            self.cast_data.append(cast_data)
            self._add_cast_to_list(cast_data)

    def edit_cast(self):
        """出演者編集"""
        current_item = self.cast_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "編集する出演者を選択してください")
            return

        cast_data = current_item.data(Qt.UserRole)
        name, ok = QInputDialog.getText(self, "出演者編集", "出演者名:", text=cast_data['cast_name'])
        if ok and name:
            role, ok2 = QInputDialog.getText(self, "出演者編集", "役割（任意）:", text=cast_data.get('role', ''))
            cast_data['cast_name'] = name
            cast_data['role'] = role if ok2 else ""

            # リスト表示を更新
            display_text = name
            if cast_data['role']:
                display_text += f" ({cast_data['role']})"
            current_item.setText(display_text)
            current_item.setData(Qt.UserRole, cast_data)

    def delete_cast(self):
        """出演者削除"""
        current_item = self.cast_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "削除する出演者を選択してください")
            return

        cast_data = current_item.data(Qt.UserRole)
        row = self.cast_list.row(current_item)
        self.cast_list.takeItem(row)
        self.cast_data.remove(cast_data)

    def add_producer(self):
        """制作会社追加（取引先マスタから選択）"""
        # 取引先マスタから選択ダイアログを表示
        dialog = ProducerSelectDialog(self)
        if dialog.exec_():
            selected_partners = dialog.get_selected_partners()
            for partner in selected_partners:
                # 既に追加済みかチェック
                already_added = any(p['id'] == partner['id'] for p in self.producer_data)
                if not already_added:
                    self.producer_data.append(partner)
                    self._add_producer_to_list(partner)

    def delete_producer(self):
        """制作会社削除"""
        selected_items = self.producer_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "削除する制作会社を選択してください")
            return

        for item in selected_items:
            producer_data = item.data(Qt.UserRole)
            row = self.producer_list.row(item)
            self.producer_list.takeItem(row)
            self.producer_data.remove(producer_data)

    def save(self):
        """保存"""
        # バリデーション
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "番組名は必須です")
            return

        # 放送曜日を取得
        selected_days = [day for day, checkbox in self.day_checkboxes.items() if checkbox.isChecked()]
        broadcast_days = ",".join(selected_days)

        # ステータスを取得
        status = "放送中" if self.status_broadcasting.isChecked() else "終了"

        # データを構築
        program_data = {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'start_date': self.start_date_edit.date().toString("yyyy-MM-dd") if self.start_date_edit.date().isValid() else None,
            'end_date': self.end_date_edit.date().toString("yyyy-MM-dd") if self.end_date_edit.date().isValid() else None,
            'broadcast_time': self.broadcast_time_edit.text().strip(),
            'broadcast_days': broadcast_days,
            'status': status
        }

        if self.is_edit:
            program_data['id'] = self.program[0]

        try:
            # 番組を保存
            program_id = self.db.save_program(program_data, is_new=not self.is_edit)

            # 出演者を保存
            self.db.save_program_cast(program_id, self.cast_data)

            # 制作会社を保存
            producer_ids = [p['id'] for p in self.producer_data]
            self.db.save_program_producers(program_id, producer_ids)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")

    def get_data(self):
        """データを取得（使用しないが互換性のため残す）"""
        return {}


class ProducerSelectDialog(QDialog):
    """制作会社選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()

        self.setWindowTitle("制作会社選択")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_partners()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._load_partners)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # リスト
        self.partner_list = QListWidget()
        self.partner_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.partner_list)

        # ボタン
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("選択")
        self.cancel_button = QPushButton("キャンセル")
        self.select_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def _load_partners(self):
        """取引先を読み込み"""
        search_term = self.search_edit.text()
        partners = self.db.get_partners(search_term)

        self.partner_list.clear()
        for partner in partners:
            partner_id = partner[0]
            partner_name = partner[1]
            partner_code = partner[2] or ""

            display_text = partner_name
            if partner_code:
                display_text += f" ({partner_code})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {'id': partner_id, 'name': partner_name})
            self.partner_list.addItem(item)

    def get_selected_partners(self):
        """選択された取引先を取得"""
        selected_items = self.partner_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items]
