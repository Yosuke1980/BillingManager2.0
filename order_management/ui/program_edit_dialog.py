"""番組編集ダイアログ（出演者マスタ連携版）"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QTextEdit, QDateEdit, QPushButton, QMessageBox, QLabel,
    QRadioButton, QButtonGroup, QCheckBox, QListWidget, QComboBox
)
from PyQt5.QtCore import Qt, QDate
from order_management.database_manager import OrderManagementDB
from order_management.ui.ui_helpers import create_list_item
from order_management.ui.cast_edit_dialog import CastEditDialog
from order_management.ui.producer_select_dialog import ProducerSelectDialog


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

        # フォーム
        form_layout = QFormLayout()

        # 番組名
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

        # 放送曜日
        broadcast_days_layout = QHBoxLayout()
        self.day_checkboxes = {}
        for day in ["月", "火", "水", "木", "金", "土", "日"]:
            checkbox = QCheckBox(day)
            self.day_checkboxes[day] = checkbox
            broadcast_days_layout.addWidget(checkbox)

        broadcast_days_widget = QLabel()
        broadcast_days_widget.setLayout(broadcast_days_layout)
        form_layout.addRow("放送曜日:", broadcast_days_widget)

        # ステータス
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
        self.delete_cast_button = QPushButton("出演者削除")
        self.new_cast_button = QPushButton("新規出演者登録")
        self.add_cast_button.clicked.connect(self.add_cast)
        self.delete_cast_button.clicked.connect(self.delete_cast)
        self.new_cast_button.clicked.connect(self.create_new_cast)
        cast_button_layout.addWidget(self.add_cast_button)
        cast_button_layout.addWidget(self.delete_cast_button)
        cast_button_layout.addWidget(self.new_cast_button)
        cast_button_layout.addStretch()
        layout.addLayout(cast_button_layout)

        # 制作会社セクション
        producer_label = QLabel("制作会社:")
        producer_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(producer_label)

        self.producer_list = QListWidget()
        self.producer_list.setMaximumHeight(120)
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

        # データ保持
        self.cast_data = []  # [{'cast_id': 1, 'role': 'MC'}, ...]
        self.producer_data = []  # [{'id': partner_id, 'name': '会社名'}, ...]

    def _load_program_data(self):
        """番組データを読み込み"""
        if not self.program:
            return

        self.name_edit.setText(self.program[1] or "")
        self.description_edit.setPlainText(self.program[2] or "")

        if self.program[3]:
            self.start_date_edit.setDate(QDate.fromString(self.program[3], "yyyy-MM-dd"))
        if self.program[4]:
            self.end_date_edit.setDate(QDate.fromString(self.program[4], "yyyy-MM-dd"))

        self.broadcast_time_edit.setText(self.program[5] or "")

        broadcast_days = self.program[6] or ""
        if broadcast_days:
            for day in broadcast_days.split(","):
                if day in self.day_checkboxes:
                    self.day_checkboxes[day].setChecked(True)

        if self.program[7] == "終了":
            self.status_ended.setChecked(True)

        # 出演者を読み込み（castテーブル経由）
        program_id = self.program[0]
        cast_list = self.db.get_program_cast_v2(program_id)
        for cast in cast_list:
            # cast: (program_cast.id, cast_id, cast_name, partner_name, role)
            cast_data = {'cast_id': cast[1], 'role': cast[4] or ""}
            self.cast_data.append(cast_data)
            display_text = f"{cast[2]} ({cast[3]})"
            if cast[4]:
                display_text += f" - {cast[4]}"
            item = create_list_item(display_text, cast_data)
            self.cast_list.addItem(item)

        # 制作会社を読み込み
        producer_list = self.db.get_program_producers(program_id)
        for producer in producer_list:
            producer_data = {'id': producer[1], 'name': producer[2]}
            self.producer_data.append(producer_data)
            item = create_list_item(producer_data['name'], producer_data)
            self.producer_list.addItem(item)

    def add_cast(self):
        """出演者追加（出演者マスタから選択）"""
        dialog = CastSelectDialog(self)
        if dialog.exec_():
            selected_casts = dialog.get_selected_casts()
            for cast in selected_casts:
                # 既に追加済みかチェック
                already_added = any(c['cast_id'] == cast['id'] for c in self.cast_data)
                if already_added:
                    continue

                # 役割を入力
                from PyQt5.QtWidgets import QInputDialog
                role, ok = QInputDialog.getText(self, "役割入力", f"{cast['name']}の役割（任意）:")

                cast_data = {'cast_id': cast['id'], 'role': role if ok else ""}
                self.cast_data.append(cast_data)

                display_text = f"{cast['name']} ({cast['partner_name']})"
                if role and ok:
                    display_text += f" - {role}"
                item = create_list_item(display_text, cast_data)
                self.cast_list.addItem(item)

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

    def create_new_cast(self):
        """新規出演者登録"""
        dialog = CastEditDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "完了", "出演者を登録しました。「出演者追加」から選択してください。")

    def add_producer(self):
        """制作会社追加"""
        dialog = ProducerSelectDialog(self)
        if dialog.exec_():
            selected_partners = dialog.get_selected_partners()
            for partner in selected_partners:
                already_added = any(p['id'] == partner['id'] for p in self.producer_data)
                if not already_added:
                    self.producer_data.append(partner)
                    item = create_list_item(partner['name'], partner)
                    self.producer_list.addItem(item)

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
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "入力エラー", "番組名は必須です")
            return

        selected_days = [day for day, cb in self.day_checkboxes.items() if cb.isChecked()]
        status = "放送中" if self.status_broadcasting.isChecked() else "終了"

        program_data = {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'start_date': self.start_date_edit.date().toString("yyyy-MM-dd") if self.start_date_edit.date().isValid() else None,
            'end_date': self.end_date_edit.date().toString("yyyy-MM-dd") if self.end_date_edit.date().isValid() else None,
            'broadcast_time': self.broadcast_time_edit.text().strip(),
            'broadcast_days': ",".join(selected_days),
            'status': status
        }

        if self.is_edit:
            program_data['id'] = self.program[0]

        try:
            program_id = self.db.save_program(program_data, is_new=not self.is_edit)

            # 出演者を保存（castテーブル経由）
            self.db.save_program_cast_v2(program_id, self.cast_data)

            # 制作会社を保存
            producer_ids = [p['id'] for p in self.producer_data]
            self.db.save_program_producers(program_id, producer_ids)

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存に失敗しました: {e}")

    def get_data(self):
        """データ取得（互換性のため）"""
        return {}


class CastSelectDialog(QDialog):
    """出演者選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = OrderManagementDB()

        self.setWindowTitle("出演者選択")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_casts()

    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout(self)

        # 検索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self._load_casts)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # リスト
        self.cast_list = QListWidget()
        self.cast_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.cast_list)

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

    def _load_casts(self):
        """出演者を読み込み"""
        search_term = self.search_edit.text()
        casts = self.db.get_casts(search_term)

        self.cast_list.clear()
        for cast in casts:
            # cast: (id, name, partner_name, partner_code, notes)
            display_text = f"{cast[1]} ({cast[2]})"
            cast_data = {'id': cast[0], 'name': cast[1], 'partner_name': cast[2]}
            item = create_list_item(display_text, cast_data)
            self.cast_list.addItem(item)

    def get_selected_casts(self):
        """選択された出演者を取得"""
        selected_items = self.cast_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items]
